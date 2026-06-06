from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.game import DiplomacyRequest, DiplomaticMessage
from app.services import game_engine, ai_service
from app.services.scenario_loader import load_scenario
from app.dependencies import AiConfig, get_ai_config
import json

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
    target_country = scenario.countries.get(req.target_country_id)

    if not player_country or not target_country:
        raise HTTPException(status_code=400, detail="Pays introuvable")

    world_context = f"{session.year}/{session.month:02d}"
    history = game_engine.get_diplomatic_history_with(session_id, req.target_country_id)

    async def event_stream():
        full_response = ""
        try:
            async for chunk in ai_service.get_country_response(
                country=target_country.model_dump(),
                player_country=player_country.model_dump(),
                player_message=req.message,
                world_context=world_context,
                diplomatic_history=history,
                config=config,
            ):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            msg = DiplomaticMessage(
                from_country=session.player_country_id,
                to_country=req.target_country_id,
                content=req.message,
                response=full_response,
            )
            game_engine.add_diplomatic_message(session_id, msg)
            yield f"data: {json.dumps({'done': True, 'message_id': msg.id})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{session_id}/history/{target_country_id}")
async def get_diplomacy_history(session_id: str, target_country_id: str):
    session = game_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
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
