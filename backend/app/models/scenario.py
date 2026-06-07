from pydantic import BaseModel
from typing import Dict, List, Optional
from .country import Country


class Alliance(BaseModel):
    id: str
    name: str
    type: str  # military | economic | political
    members: List[str]
    description: str = ""
    color: str = "#888888"


class ScenarioEvent(BaseModel):
    title: str
    description: str
    year: int
    month: int
    affected_countries: List[str] = []


class Scenario(BaseModel):
    id: str
    name: str
    description: str
    start_year: int
    start_month: int = 1
    map_style: str = "modern"
    custom_map_id: Optional[str] = None           # UUID of uploaded GeoJSON
    custom_map_feature_id_property: str = "id"    # which GeoJSON property is the territory key
    initial_territories: Dict[str, str] = {}      # feature_id → faction_id
    countries: Dict[str, Country]
    alliances: Dict[str, Alliance] = {}
    initial_events: List[ScenarioEvent] = []
    custom: bool = False  # True si créé par l'utilisateur


class ScenarioSummary(BaseModel):
    id: str
    name: str
    description: str
    start_year: int
    country_count: int
    custom: bool = False
