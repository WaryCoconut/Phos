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
    stability_impact: int = 0   # applied to player if player is in affected_countries
    economy_impact: float = 0.0
    year: int
    month: int
    day: int = 1
    type: str = "general"  # diplomatic, economic, military, humanitarian, political, natural, reaction, consequence
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


class Treaty(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # commercial, militaire, diplomatique, culturel, humanitaire
    country_a: str
    country_b: str
    summary: str
    year: int
    month: int
    economy_bonus: float = 0.0   # monthly economy multiplier bonus
    relation_bonus: int = 0       # monthly relation improvement (per treaty)


class PendingConsequence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger_year: int
    trigger_month: int
    source_action: str
    title: str
    description: str
    event_type: str = "consequence"
    stability_impact: int = 0
    economy_impact: float = 0.0


class GameSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    player_country_id: str
    year: int
    month: int
    day: int = 1                # day within month (1-30), for sub-month simulation
    turn: int = 1
    country_states: Dict[str, dict] = {}
    dynamic_countries: Dict[str, dict] = {}   # country_id -> country data (independent regions)
    region_state: Dict[str, dict] = Field(
        default_factory=lambda: {"occupied": {}, "independent": {}}
    )
    diplomatic_history: List[DiplomaticMessage] = []
    action_history: List[ActionResult] = []
    world_events: List[WorldEvent] = []
    domestic_events: List[DomesticEvent] = []
    map_pois: List[MapPOI] = []
    pending_actions: List[PendingAction] = []
    pending_consequences: List[PendingConsequence] = []
    treaties: List[Treaty] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateGameRequest(BaseModel):
    scenario_id: str
    player_country_id: str


class QueueActionRequest(BaseModel):
    content: str


class SimulateRequest(BaseModel):
    months: int = 0
    weeks: int = 0   # if weeks > 0, simulate in week units (overrides months)

    @property
    def is_week_mode(self) -> bool:
        return self.weeks > 0

    @property
    def total_units(self) -> int:
        return self.weeks if self.is_week_mode else max(1, self.months)

    @property
    def unit_days(self) -> int:
        return 7 if self.is_week_mode else 30


class DiplomacyRequest(BaseModel):
    target_country_id: str
    message: str


class AdvisorRequest(BaseModel):
    question: str
