from fastapi import APIRouter, HTTPException
from app.services.scenario_loader import (
    list_scenarios,
    load_scenario,
    save_custom_scenario,
    delete_custom_scenario,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("/")
async def get_scenarios():
    return list_scenarios()


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    scenario = load_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scénario introuvable")
    return scenario.model_dump()


@router.post("/")
async def create_scenario(scenario_data: dict):
    try:
        scenario = save_custom_scenario(scenario_data)
        return {"id": scenario.id, "message": "Scénario créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{scenario_id}")
async def update_scenario(scenario_id: str, scenario_data: dict):
    existing = load_scenario(scenario_id)
    if not existing or not existing.custom:
        raise HTTPException(status_code=404, detail="Scénario personnalisé introuvable")
    scenario_data["id"] = scenario_id
    try:
        scenario = save_custom_scenario(scenario_data)
        return {"id": scenario.id, "message": "Scénario mis à jour"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str):
    if not delete_custom_scenario(scenario_id):
        raise HTTPException(status_code=404, detail="Scénario personnalisé introuvable")
    return {"message": "Scénario supprimé"}
