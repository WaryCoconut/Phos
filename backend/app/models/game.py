from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid


class DiplomaticMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_country: str
    to_country: str
    content: str
    response: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WorldEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    affected_countries: List[str] = []
    relation_changes: Dict[str, Dict[str, int]] = {}  # {country_id: {other_id: delta}}
    year: int
    month: int
    triggered_by_player: bool = False


class PlayerAction(BaseModel):
    content: str
    year: int
    month: int


class ActionResult(BaseModel):
    action: str
    consequences: str
    world_events: List[WorldEvent] = []
    relation_changes: Dict[str, Dict[str, int]] = {}
    year: int
    month: int


class PendingAction(BaseModel):
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DomesticEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: str = "internal"  # protest, rally, scandal, economic, military, infrastructure, social, cultural
    severity: int = 1  # 1=minor, 2=significant, 3=major
    stability_impact: int = 0
    year: int
    month: int


class MapPOI(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # university, military_base, factory, hospital, parliament, port, dam, research_center, monument, embassy, airport, nuclear_plant, cultural_center, stadium
    country_id: str
    coordinates: List[float]  # [longitude, latitude]
    icon: str = "📍"
    year: int
    month: int


class GameSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    player_country_id: str
    year: int
    month: int
    turn: int = 1
    country_states: Dict[str, dict] = {}
    diplomatic_history: List[DiplomaticMessage] = []
    action_history: List[ActionResult] = []
    world_events: List[WorldEvent] = []
    domestic_events: List[DomesticEvent] = []
    map_pois: List[MapPOI] = []
    pending_actions: List[PendingAction] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateGameRequest(BaseModel):
    scenario_id: str
    player_country_id: str


class QueueActionRequest(BaseModel):
    content: str


class SimulateRequest(BaseModel):
    months: int = 1  # 1, 3, 6, 12


class DiplomacyRequest(BaseModel):
    target_country_id: str
    message: str


class AdvisorRequest(BaseModel):
    question: str
