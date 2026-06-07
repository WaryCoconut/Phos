from fastapi import APIRouter, Depends
from app.dependencies import AiConfig, get_ai_config
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/sync-agent")
async def sync_agent(config: AiConfig = Depends(get_ai_config)):
    if not ai_service._is_socle(config):
        return {"status": "skipped"}
    result = await ai_service.sync_agent(config)
    return {"status": "ok", **result}
