import json
import os
import uuid
from typing import Dict, Optional
from app.models.scenario import Scenario, ScenarioSummary

SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scenarios")
CUSTOM_SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "custom_scenarios")

_cache: Dict[str, Scenario] = {}


def _ensure_custom_dir():
    os.makedirs(CUSTOM_SCENARIOS_DIR, exist_ok=True)


def load_scenario(scenario_id: str) -> Optional[Scenario]:
    if scenario_id in _cache:
        return _cache[scenario_id]

    for directory in [SCENARIOS_DIR, CUSTOM_SCENARIOS_DIR]:
        path = os.path.join(directory, f"{scenario_id}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            scenario = Scenario(**data)
            _cache[scenario_id] = scenario
            return scenario

    return None


def list_scenarios() -> list[ScenarioSummary]:
    summaries = []
    _ensure_custom_dir()

    for directory, is_custom in [(SCENARIOS_DIR, False), (CUSTOM_SCENARIOS_DIR, True)]:
        if not os.path.exists(directory):
            continue
        for filename in os.listdir(directory):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(directory, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            summaries.append(
                ScenarioSummary(
                    id=data["id"],
                    name=data["name"],
                    description=data["description"],
                    start_year=data["start_year"],
                    country_count=len(data.get("countries", {})),
                    custom=is_custom,
                )
            )

    return summaries


def save_custom_scenario(scenario_data: dict) -> Scenario:
    _ensure_custom_dir()
    if not scenario_data.get("id"):
        scenario_data["id"] = f"custom_{uuid.uuid4().hex[:8]}"
    scenario_data["custom"] = True
    scenario = Scenario(**scenario_data)
    path = os.path.join(CUSTOM_SCENARIOS_DIR, f"{scenario.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scenario.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    _cache[scenario.id] = scenario
    return scenario


def delete_custom_scenario(scenario_id: str) -> bool:
    path = os.path.join(CUSTOM_SCENARIOS_DIR, f"{scenario_id}.json")
    if os.path.exists(path):
        os.remove(path)
        _cache.pop(scenario_id, None)
        return True
    return False
