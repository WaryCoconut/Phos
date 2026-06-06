from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.game import AdvisorRequest
from app.services import game_engine, ai_service
from app.services.scenario_loader import load_scenario
from app.dependencies import AiConfig, get_ai_config
import json

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/{session_id}/ask")
async def ask_advisor(
    session_id: str,
    req: AdvisorRequest,
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

    country_state = session.country_states.get(session.player_country_id, {})
    world_context = f"{session.year}/{session.month:02d}"
    recent_events = [e.model_dump(mode="json") for e in session.domestic_events[-5:]]

    async def event_stream():
        try:
            async for chunk in ai_service.get_advisor_response(
                player_country=player_country.model_dump(),
                world_context=world_context,
                country_state=country_state,
                question=req.question,
                recent_events=recent_events,
                config=config,
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{session_id}/briefing")
async def get_briefing(
    session_id: str,
    config: AiConfig = Depends(get_ai_config),
):
    req = AdvisorRequest(
        question=(
            "Donne-moi un briefing complet de la situation actuelle : "
            "état économique, relations diplomatiques clés, menaces et opportunités, "
            "et tes 3 principales recommandations pour ce mois."
        )
    )
    return await ask_advisor(session_id, req, config)
