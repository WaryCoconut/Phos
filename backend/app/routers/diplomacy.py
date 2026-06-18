import json
import random

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.game import DiplomacyRequest, DiplomaticMessage
from app.services import game_engine, ai_service
from app.services.scenario_loader import load_scenario
from app.dependencies import AiConfig, get_ai_config

router = APIRouter(prefix="/diplomacy", tags=["diplomacy"])


@router.post("/{session_id}/message")
async def send_diplomatic_message(
    session_id: str,
    req: DiplomacyRequest,
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

    world_context = f"{session.year}/{session.month:02d}"

    # Check if target is a group
    is_group = req.target_country_id.startswith("group:")

    if is_group:
        group_id = req.target_country_id
        # Determine group name and members
        group_name = "Group Chat"
        members = []
        
        # 1. Check if it's an alliance group
        alliance_id = group_id.split(":")[1]
        alliance = scenario.alliances.get(alliance_id)
        if alliance:
            group_name = alliance.name
            members = list(alliance.members)
        else:
            # 2. Check if it's a custom group in the session
            for cg in session.custom_groups:
                if cg.id == alliance_id or cg.name == alliance_id:
                    group_name = cg.name
                    members = list(cg.members)
                    break
        
        if not members:
            raise HTTPException(status_code=400, detail="Groupe vide ou inexistant")

        members_to_respond = [m for m in members if m != session.player_country_id]
        if not members_to_respond:
            raise HTTPException(status_code=400, detail="Aucun autre membre dans ce groupe")

        responders = random.sample(members_to_respond, min(2, len(members_to_respond)))

        # Load group diplomatic history
        group_history = [
            {
                "player": msg.content if msg.from_country == session.player_country_id else "",
                "response": f"[{msg.from_country}]: {msg.content or msg.response or ''}" if msg.from_country != session.player_country_id else "",
            }
            for msg in session.diplomatic_history
            if msg.to_country == group_id
        ]

        async def group_event_stream():
            try:
                # Save player message first
                player_msg = DiplomaticMessage(
                    from_country=session.player_country_id,
                    to_country=group_id,
                    content=req.message,
                )
                game_engine.add_diplomatic_message(session_id, player_msg)

                # Generate replies sequentially
                for rep_id in responders:
                    rep_country = scenario.countries.get(rep_id)
                    if not rep_country:
                        rep_data = session.dynamic_countries.get(rep_id)
                        if rep_data:
                            from app.models.scenario import Country as ScenarioCountry
                            rep_country = ScenarioCountry(**rep_data)
                    
                    if not rep_country:
                        continue

                    rep_country_data = game_engine.merge_country(rep_country, session.country_states.get(rep_id))
                    player_country_data = game_engine.merge_country(player_country, session.country_states.get(session.player_country_id))
                    
                    full_response = ""
                    async for chunk in ai_service.get_group_member_response(
                        country=rep_country_data,
                        player_country=player_country_data,
                        player_message=req.message,
                        group_name=group_name,
                        group_members=members,
                        world_context=world_context,
                        diplomatic_history=group_history,
                        config=config,
                        session_id=session_id,
                        country_state=session.country_states.get(rep_id),
                    ):
                        full_response += chunk
                        yield f"data: {json.dumps({'chunk': chunk, 'sender_id': rep_id})}\n\n"

                    # Save reply to history
                    rep_msg = DiplomaticMessage(
                        from_country=rep_id,
                        to_country=group_id,
                        content=full_response,
                    )
                    game_engine.add_diplomatic_message(session_id, rep_msg)

                    # Update history context
                    group_history.append({
                        "player": "",
                        "response": f"[{rep_id}]: {full_response}",
                    })

                    # Analyze exchange and apply effects
                    effect = await ai_service.analyze_diplomatic_exchange(
                        player_country=player_country_data,
                        target_country=rep_country_data,
                        player_message=req.message,
                        country_response=full_response,
                        config=config,
                    )
                    if effect.get("relation_delta") or effect.get("economy_delta") or effect.get("domestic_events"):
                        game_engine.apply_diplomatic_effects(
                            session_id=session_id,
                            player_country_id=session.player_country_id,
                            target_country_id=rep_id,
                            effect=effect,
                        )

                yield f"data: {json.dumps({'done': True})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(group_event_stream(), media_type="text/event-stream")

    else:
        target_country = scenario.countries.get(req.target_country_id)
        if not target_country:
            dyn = session.dynamic_countries.get(req.target_country_id)
            if dyn:
                from app.models.scenario import Country as ScenarioCountry
                target_country = ScenarioCountry(**dyn)

        if not target_country:
            raise HTTPException(status_code=400, detail="Pays cible introuvable")

        history = game_engine.get_diplomatic_history_with(session_id, req.target_country_id)

        async def event_stream():
            full_response = ""
            try:
                target_country_data = game_engine.merge_country(target_country, session.country_states.get(req.target_country_id))
                player_country_data = game_engine.merge_country(player_country, session.country_states.get(session.player_country_id))
                
                async for chunk in ai_service.get_country_response(
                    country=target_country_data,
                    player_country=player_country_data,
                    player_message=req.message,
                    world_context=world_context,
                    diplomatic_history=history,
                    config=config,
                    session_id=session_id,
                    country_state=session.country_states.get(req.target_country_id),
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'chunk': chunk, 'sender_id': req.target_country_id})}\n\n"

                msg = DiplomaticMessage(
                    from_country=session.player_country_id,
                    to_country=req.target_country_id,
                    content=req.message,
                    response=full_response,
                )
                game_engine.add_diplomatic_message(session_id, msg)

                effect = await ai_service.analyze_diplomatic_exchange(
                    player_country=player_country_data,
                    target_country=target_country_data,
                    player_message=req.message,
                    country_response=full_response,
                    config=config,
                )
                if effect.get("relation_delta") or effect.get("economy_delta") or effect.get("domestic_events"):
                    game_engine.apply_diplomatic_effects(
                        session_id=session_id,
                        player_country_id=session.player_country_id,
                        target_country_id=req.target_country_id,
                        effect=effect,
                    )
                yield f"data: {json.dumps({'done': True, 'message_id': msg.id, 'game_effect': effect, 'sender_id': req.target_country_id})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{session_id}/history/{target_country_id}")
async def get_diplomacy_history(session_id: str, target_country_id: str):
    session = game_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    if target_country_id.startswith("group:"):
        history = [
            m.model_dump(mode="json")
            for m in session.diplomatic_history
            if m.to_country == target_country_id
        ]
    else:
        history = [
            m.model_dump(mode="json")
            for m in session.diplomatic_history
            if (m.from_country == session.player_country_id and m.to_country == target_country_id)
            or (m.from_country == target_country_id and m.to_country == session.player_country_id)
        ]
    return history


@router.get("/{session_id}/history")
async def get_all_diplomacy_history(session_id: str):
    session = game_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return [m.model_dump(mode="json") for m in session.diplomatic_history]
