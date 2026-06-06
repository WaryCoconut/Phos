from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.game import CreateGameRequest, PlayerAction, ActionResult, QueueActionRequest, SimulateRequest
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

    consequences = await ai_service.process_player_action(
        player_country=player_country.model_dump(),
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

    async def event_stream():
        # Distribute actions across months
        actions_by_month: dict[int, str] = {}
        for i, action in enumerate(pending):
            actions_by_month[i % req.months] = action

        for month_i in range(req.months):
            try:
                # Generate world events for this month (using current state before advancing)
                events = await ai_service.generate_turn_events(
                    year=session.year,
                    month=session.month,
                    world_state=session.country_states,
                    player_country_id=session.player_country_id,
                    config=config,
                )
            except Exception as e:
                events = []
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

            # Process action for this month (if any)
            action_result = None
            action_content = actions_by_month.get(month_i)
            if action_content:
                try:
                    result_data = await ai_service.process_player_action(
                        player_country=player_country.model_dump(),
                        action=action_content,
                        year=session.year,
                        month=session.month,
                        world_state=session.country_states,
                        config=config,
                    )
                    action_result = {"action": action_content, **result_data}
                except Exception as e:
                    action_result = {"action": action_content, "narrative": str(e), "relation_changes": {}, "stability_delta": 0, "economy_delta": 0.0}

            # Track indices before applying to detect newly added items
            dom_idx = len(session.domestic_events)
            poi_idx = len(session.map_pois)

            # Apply changes and advance month
            game_engine.apply_simulation_month(session, action_result, events)

            new_domestic = session.domestic_events[dom_idx:]
            new_pois = session.map_pois[poi_idx:]

            # Stream month_start
            yield f"data: {json.dumps({'type': 'month_start', 'year': session.year, 'month': session.month, 'turn': session.turn})}\n\n"

            # Stream world events
            for e in events:
                yield f"data: {json.dumps({'type': 'world_event', 'title': e.get('title', ''), 'description': e.get('description', ''), 'affected_countries': e.get('affected_countries', [])})}\n\n"

            # Stream action result
            if action_result and action_result.get("applicable", True):
                yield f"data: {json.dumps({'type': 'action_result', 'action': action_content, 'narrative': action_result.get('narrative', ''), 'relation_changes': action_result.get('relation_changes', {}), 'stability_delta': action_result.get('stability_delta', 0)})}\n\n"

            # Stream domestic events (Game Master)
            for de in new_domestic:
                yield f"data: {json.dumps({'type': 'domestic_event', 'title': de.title, 'description': de.description, 'event_type': de.type, 'severity': de.severity, 'stability_impact': de.stability_impact})}\n\n"

            # Stream new POIs
            for poi in new_pois:
                yield f"data: {json.dumps({'type': 'poi_added', 'poi_id': poi.id, 'poi_name': poi.name, 'poi_type': poi.type, 'poi_icon': poi.icon, 'poi_coordinates': poi.coordinates, 'poi_country_id': poi.country_id, 'year': session.year, 'month': session.month})}\n\n"

        game_engine._save_snapshot(session)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

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
