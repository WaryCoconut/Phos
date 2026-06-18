from pydantic import BaseModel
from typing import Optional, List, Dict


class CountryNationalStats(BaseModel):
    sovereignty: float = 50.0           # indépendance politique/institutionnelle 0-100
    food_autonomy: float = 50.0         # autosuffisance alimentaire 0-100+
    energy_autonomy: float = 50.0       # autosuffisance énergétique 0-100+
    economic_independence: float = 50.0 # indépendance économique 0-100
    security: float = 50.0              # sécurité intérieure / ordre public 0-100


class CountryEconomy(BaseModel):
    gdp: float  # milliards USD
    gdp_per_capita: float
    gdp_growth: float = 0.0  # % annuel
    inflation: float = 2.0
    unemployment: float = 5.0
    debt_pct_gdp: float = 50.0
    budget_balance_pct_gdp: float = -2.0  # % du PIB, positif = excédent, négatif = déficit
    currency: str = "USD"
    main_sectors: List[str] = []
    sectors: Dict[str, float] = {}  # {agriculture/industrie/services: % du PIB}


class CountryMilitary(BaseModel):
    strength: int  # 1-10
    active_personnel: int = 0
    nuclear_weapons: bool = False
    defense_budget_pct: float = 2.0  # % du PIB
    equipment: Dict[str, int] = {}   # {chars_combat/avions_chasse/…: count}


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
    national_stats: Optional[CountryNationalStats] = None
    relations: Dict[str, int] = {}  # country_id -> score -100..+100
    personality_traits: List[str] = []
    personality: str = ""  # description libre de la personnalité diplomatique
    description: str = ""
    nation_brief: str = ""
    color: Optional[str] = None  # couleur sur la carte (hex)
    initial_stability: int = 50  # stabilité au démarrage de la partie (0-100)


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
