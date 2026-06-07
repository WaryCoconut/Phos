from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import game_engine
from app.data.regions import all_regions, get_country_regions, SUPPORTED_COUNTRIES

router = APIRouter(prefix="/regions", tags=["regions"])


class OccupyRequest(BaseModel):
    adm1_code: str
    occupying_country_id: str


class IndependenceRequest(BaseModel):
    adm1_code: str
    new_country_name: str
    new_country_flag: str = "🏳️"


@router.get("/meta")
async def get_regions_meta():
    """Return all region metadata (for frontend display)."""
    return all_regions()


@router.get("/meta/{country_id}")
async def get_country_regions_meta(country_id: str):
    return get_country_regions(country_id)


@router.get("/{session_id}")
async def get_region_state(session_id: str):
    rs = game_engine.get_region_state(session_id)
    if rs is None:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return rs


@router.post("/{session_id}/occupy")
async def occupy_region(session_id: str, req: OccupyRequest):
    try:
        return game_engine.occupy_region(session_id, req.adm1_code, req.occupying_country_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{session_id}/occupy/{adm1_code}")
async def liberate_region(session_id: str, adm1_code: str):
    try:
        return game_engine.liberate_region(session_id, adm1_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/independence")
async def declare_independence(session_id: str, req: IndependenceRequest):
    try:
        return game_engine.declare_region_independent(
            session_id, req.adm1_code, req.new_country_name, req.new_country_flag
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{session_id}/independence/{adm1_code}")
async def reunify_region(session_id: str, adm1_code: str):
    try:
        return game_engine.reunify_region(session_id, adm1_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
