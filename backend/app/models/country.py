from pydantic import BaseModel
from typing import Optional, List, Dict


class CountryEconomy(BaseModel):
    gdp: float  # milliards USD
    gdp_per_capita: float
    gdp_growth: float = 0.0  # % annuel
    inflation: float = 2.0
    unemployment: float = 5.0
    debt_pct_gdp: float = 50.0
    currency: str = "USD"
    main_sectors: List[str] = []


class CountryMilitary(BaseModel):
    strength: int  # 1-10
    active_personnel: int = 0
    nuclear_weapons: bool = False
    defense_budget_pct: float = 2.0  # % du PIB


class Country(BaseModel):
    id: str  # ISO 3166-1 alpha-3
    name: str
    flag: str = ""
    capital: str = ""
    continent: str = ""
    population: int = 0
    government_type: str = "republic"
    ideology: str = "neutral"
    leader: str = ""
    alliances: List[str] = []
    economy: Optional[CountryEconomy] = None
    military: Optional[CountryMilitary] = None
    relations: Dict[str, int] = {}  # country_id -> score -100..+100
    personality_traits: List[str] = []
    description: str = ""
    color: Optional[str] = None  # couleur sur la carte (hex)


class CountryState(BaseModel):
    """État dynamique d'un pays pendant la partie."""
    id: str
    stability: int = 50  # 0-100
    economy_modifier: float = 1.0
    military_modifier: float = 1.0
    relations: Dict[str, int] = {}
    at_war_with: List[str] = []
    sanctions_by: List[str] = []
    active_events: List[str] = []
