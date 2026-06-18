from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.game import CreateGameRequest, PlayerAction, ActionResult, QueueActionRequest, SimulateRequest, CreateCustomGroupRequest
from app.services import game_engine, ai_service
from app.services.scenario_loader import load_scenario
from app.dependencies import AiConfig, get_ai_config
import json

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/")
async def create_game(req: CreateGameRequest):
    try:
        session = game_engine.create_session(req.scenario_id, req.player_country_id)
        return {"session_id": session.id, "message": "Partie créée avec succès"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    return game_engine.list_sessions()


@router.get("/{session_id}")
async def get_game(session_id: str):
    state = game_engine.get_game_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return state


@router.post("/{session_id}/action")
async def submit_action(
    session_id: str,
    action: PlayerAction,
    config: AiConfig = Depends(get_ai_config),
):
    session = game_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    scenario = load_scenario(session.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scénario introuvable")

    player_country = scenario.countries.get(session.player_country_id)
    if not player_country:
        raise HTTPException(status_code=400, detail="Pays du joueur introuvable")

    player_country_data = game_engine.merge_country(player_country, session.country_states.get(session.player_country_id))
    consequences = await ai_service.process_player_action(
        player_country=player_country_data,
        action=action.content,
        year=session.year,
        month=session.month,
        world_state=session.country_states,
        config=config,
    )

    result = ActionResult(
        action=action.content,
        consequences=consequences,
        year=session.year,
        month=session.month,
    )
    game_engine.apply_action_result(session_id, result)
    return result.model_dump(mode="json")


@router.post("/{session_id}/queue")
async def queue_action(session_id: str, req: QueueActionRequest):
    try:
        queue = game_engine.queue_action(session_id, req.content)
        return {"queue": queue}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{session_id}/queue/{index}")
async def remove_queued_action(session_id: str, index: int):
    try:
        queue = game_engine.remove_queued_action(session_id, index)
        return {"queue": queue}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{session_id}/custom-group")
async def create_custom_group(session_id: str, req: CreateCustomGroupRequest):
    session = game_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    scenario = load_scenario(session.scenario_id)
    valid_ids = set(scenario.countries.keys()) if scenario else set()
    valid_ids |= set(session.dynamic_countries.keys())
    invalid = [m for m in req.members if m not in valid_ids]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Pays inconnus : {', '.join(invalid)}")
    if len(req.members) < 2:
        raise HTTPException(status_code=400, detail="Un groupe doit contenir au moins 2 membres")

    group = game_engine.create_custom_group(session_id, req.name, req.members)
    return group.model_dump(mode="json")


@router.post("/{session_id}/simulate")
async def simulate(
    session_id: str,
    req: SimulateRequest,
    config: AiConfig = Depends(get_ai_config),
):
    session = game_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    scenario = load_scenario(session.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scénario introuvable")

    player_country = scenario.countries.get(session.player_country_id)
    if not player_country:
        raise HTTPException(status_code=400, detail="Pays introuvable")

    # Snapshot the pending actions queue and clear it
    pending = [a.content for a in session.pending_actions]
    session.pending_actions = []

    total_units = req.total_units
    unit_days = req.unit_days
    scale = unit_days / 30.0  # scale deltas proportionally to unit size

    async def event_stream():
        # Distribute actions across simulation units — list per unit, all actions preserved
        actions_by_unit: dict[int, list[str]] = {i: [] for i in range(total_units)}
        for i, action in enumerate(pending):
            actions_by_unit[i % total_units].append(action)

        total_world_events = 0
        total_actions_processed = 0

        for unit_i in range(total_units):
            # Only generate world events on full-month boundaries (every 4 weeks or every month)
            generate_events = not req.is_week_mode or (unit_i % 4 == 0)
            recent_actions = [a.content for a in session.pending_actions] + [
                ar.get("action", "") for ar in [
                    session.action_history[-1].model_dump() if session.action_history else {}
                ] if ar.get("action")
            ]
            try:
                if generate_events:
                    events = await ai_service.generate_turn_events(
                        year=session.year,
                        month=session.month,
                        world_state=session.country_states,
                        player_country_id=session.player_country_id,
                        config=config,
                        recent_player_actions=recent_actions,
                    )
                else:
                    events = []
            except Exception as e:
                events = []
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

            # Process ALL actions queued for this unit
            unit_actions = actions_by_unit.get(unit_i, [])
            # Build recent diplomacy context from session history (last 4 exchanges)
            recent_diplomacy = [
                {"player": m.content, "response": m.response or ""}
                for m in session.diplomatic_history[-4:]
            ]

            action_results = []
            for action_content in unit_actions:
                try:
                    player_country_data = game_engine.merge_country(player_country, session.country_states.get(session.player_country_id))
                    result_data = await ai_service.process_player_action(
                        player_country=player_country_data,
                        action=action_content,
                        year=session.year,
                        month=session.month,
                        world_state=session.country_states,
                        config=config,
                        recent_diplomacy=recent_diplomacy,
                    )
                    action_results.append({"action": action_content, **result_data})
                except Exception as e:
                    action_results.append({
                        "action": action_content,
                        "narrative": str(e),
                        "applicable": True,
                        "relation_changes": {},
                        "stability_delta": 0,
                        "economy_delta": 0.0,
                        "domestic_events": [],
                        "map_poi": None,
                        "stat_deltas": {"sovereignty": 0, "food_autonomy": 0, "energy_autonomy": 0, "economic_independence": 0},
                        "equipment_changes": {},
                        "future_events": [],
                    })

            # Track indices before applying
            dom_idx = len(session.domestic_events)
            poi_idx = len(session.map_pois)

            # Advance time + apply first action (if any) + war + treaties + economy
            first_action = action_results[0] if action_results else None
            game_engine.apply_simulation_unit(session, first_action, events, days=unit_days, scale=scale)

            # Apply additional actions (same unit, no time advancement)
            for extra_ar in action_results[1:]:
                game_engine.apply_action_result_to_session(session, extra_ar, save=False, scale=scale)
            if len(action_results) > 1:
                game_engine._save_session(session)

            new_domestic = session.domestic_events[dom_idx:]
            new_pois = session.map_pois[poi_idx:]

            total_world_events += len(events)
            total_actions_processed += len(action_results)

            label = "week_start" if req.is_week_mode else "month_start"
            yield f"data: {json.dumps({'type': label, 'year': session.year, 'month': session.month, 'day': session.day, 'turn': session.turn})}\n\n"

            for e in events:
                yield f"data: {json.dumps({'type': 'world_event', 'title': e.get('title', ''), 'description': e.get('description', ''), 'affected_countries': e.get('affected_countries', []), 'event_type': e.get('type', 'general')})}\n\n"

            for ar in action_results:
                if ar.get("applicable", True):
                    yield f"data: {json.dumps({
                        'type': 'action_result',
                        'action': ar['action'],
                        'narrative': ar.get('narrative', ''),
                        'relation_changes': ar.get('relation_changes', {}),
                        'stability_delta': ar.get('stability_delta', 0),
                        'economy_delta': ar.get('economy_delta', 0.0),
                        'military_delta': ar.get('military_delta', 0.0),
                        'stat_deltas': ar.get('stat_deltas', {}),
                        'equipment_changes': ar.get('equipment_changes', {}),
                    })}\n\n"

            for de in new_domestic:
                yield f"data: {json.dumps({'type': 'domestic_event', 'title': de.title, 'description': de.description, 'event_type': de.type, 'severity': de.severity, 'stability_impact': de.stability_impact})}\n\n"

            for poi in new_pois:
                yield f"data: {json.dumps({'type': 'poi_added', 'poi_id': poi.id, 'poi_name': poi.name, 'poi_type': poi.type, 'poi_icon': poi.icon, 'poi_coordinates': poi.coordinates, 'poi_country_id': poi.country_id, 'year': session.year, 'month': session.month})}\n\n"

        game_engine._save_snapshot(session)
        final_ps = session.country_states.get(session.player_country_id, {})
        yield f"data: {json.dumps({'type': 'done', 'final_stability': final_ps.get('stability', 50), 'final_economy_modifier': final_ps.get('economy_modifier', 1.0), 'final_military_modifier': final_ps.get('military_modifier', 1.0), 'world_event_count': total_world_events, 'action_count': total_actions_processed, 'treaty_count': len(session.treaties)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{session_id}/end-turn")
async def end_turn(
    session_id: str,
    config: AiConfig = Depends(get_ai_config),
):
    """Kept for backward compat — runs a 1-month simulation."""
    return await simulate(session_id, SimulateRequest(months=1), config)


@router.get("/{session_id}/snapshots")
async def list_snapshots(session_id: str):
    session = game_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return game_engine.list_snapshots(session_id)


@router.post("/{session_id}/restore/{turn}")
async def restore_snapshot(session_id: str, turn: int):
    try:
        session = game_engine.restore_snapshot(session_id, turn)
        return {"session_id": session.id, "turn": session.turn, "year": session.year, "month": session.month}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{session_id}")
async def delete_game(session_id: str):
    deleted = game_engine.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"deleted": True}
