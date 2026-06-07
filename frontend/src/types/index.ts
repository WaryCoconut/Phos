export interface CountryNationalStats {
  sovereignty: number
  food_autonomy: number
  energy_autonomy: number
  economic_independence: number
}

export interface CountryEconomy {
  gdp: number
  gdp_per_capita: number
  gdp_growth: number
  inflation: number
  unemployment: number
  debt_pct_gdp: number
  budget_balance_pct_gdp?: number
  currency: string
  main_sectors: string[]
  sectors?: Record<string, number>  // agriculture/industrie/services: %
}

export interface CountryMilitary {
  strength: number
  active_personnel: number
  nuclear_weapons: boolean
  defense_budget_pct: number
  equipment?: Record<string, number>  // chars_combat/avions_chasse/…: count
}

export interface Country {
  id: string
  name: string
  flag: string
  capital: string
  continent: string
  population: number
  government_type: string
  ideology: string
  leader: string
  alliances: string[]
  economy?: CountryEconomy
  military?: CountryMilitary
  national_stats?: CountryNationalStats
  relations: Record<string, number>
  personality_traits: string[]
  description: string
  color?: string
  // Dynamic state
  stability: number
  economy_modifier: number
  military_modifier: number
  at_war_with: string[]
  sanctions_by: string[]
  active_events: string[]
}

export interface Alliance {
  id: string
  name: string
  type: string
  members: string[]
  description: string
  color: string
}

export interface WorldEvent {
  id: string
  title: string
  description: string
  affected_countries: string[]
  year: number
  month: number
  day?: number
  type?: string
  triggered_by_player: boolean
}

export interface DiplomaticMessage {
  id: string
  from_country: string
  to_country: string
  content: string
  response?: string
  timestamp: string
}

export interface ActionResult {
  action: string
  consequences: string
  year: number
  month: number
}

export interface PendingAction {
  content: string
  created_at: string
}

export interface DomesticEvent {
  id: string
  title: string
  description: string
  type: string
  severity: number
  stability_impact: number
  year: number
  month: number
}

export interface MapPOI {
  id: string
  name: string
  type: string
  country_id: string
  coordinates: [number, number]
  icon: string
  year: number
  month: number
}

export type SimDuration = { label: string; months?: number; weeks?: number }

export interface SimEvent {
  type: 'month_start' | 'week_start' | 'world_event' | 'action_result' | 'domestic_event' | 'poi_added' | 'done' | 'error'
  year?: number
  month?: number
  day?: number
  turn?: number
  title?: string
  description?: string
  affected_countries?: string[]
  action?: string
  narrative?: string
  relation_changes?: Record<string, Record<string, number>>
  stability_delta?: number
  message?: string
  // domestic_event + world_event type field
  event_type?: string
  severity?: number
  stability_impact?: number
  // poi_added fields
  poi_id?: string
  poi_name?: string
  poi_type?: string
  poi_icon?: string
  poi_coordinates?: [number, number]
  poi_country_id?: string
  // done event summary fields
  final_stability?: number
  final_economy_modifier?: number
  world_event_count?: number
  action_count?: number
  treaty_count?: number
}

export interface OccupiedRegion {
  adm1_code: string
  occupied_by: string
  country_id: string
  region_name: string
}

export interface IndependentRegion {
  adm1_code: string
  country_id: string
  parent_id: string
  region_name: string
  since_year: number
}

export interface RegionState {
  occupied: Record<string, OccupiedRegion>
  independent: Record<string, IndependentRegion>
}

export interface RegionMeta {
  adm1_code: string
  country_id: string
  name: string
  name_fr: string
  lat: number
  lon: number
}

export interface GameState {
  session_id: string
  scenario_id: string
  year: number
  month: number
  turn: number
  player_country: Country
  countries: Record<string, Country>
  alliances: Record<string, Alliance>
  recent_events: WorldEvent[]
  domestic_events?: DomesticEvent[]
  map_pois?: MapPOI[]
  diplomatic_history: DiplomaticMessage[]
  action_history: ActionResult[]
  pending_actions?: PendingAction[]
  region_state?: RegionState
  treaties?: Treaty[]
  custom_map_id?: string
  custom_map_feature_id_property?: string
  initial_territories?: Record<string, string>
}

export interface ScenarioSummary {
  id: string
  name: string
  description: string
  start_year: number
  country_count: number
  custom: boolean
}

export interface DiplomaticEffect {
  agreement_reached: boolean
  agreement_type: string | null
  summary: string | null
  relation_delta: number
  economy_delta: number
  domestic_events: unknown[]
}

export interface Treaty {
  id: string
  type: string
  country_a: string
  country_b: string
  summary: string
  year: number
  month: number
  economy_bonus: number
  relation_bonus: number
}

export interface StatSnapshot {
  turn: number
  stability: number
  economy_modifier: number
  sovereignty?: number
  food_autonomy?: number
  energy_autonomy?: number
  economic_independence?: number
}

export type LeftPanel = 'actions' | 'diplomacy'
export type RightPanel = 'advisor' | 'dashboard' | 'events'
export type PanelView = LeftPanel | RightPanel
