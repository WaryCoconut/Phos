import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft, Save, Search, ChevronDown, ChevronUp, Plus, X,
  Loader2, Check, Upload, Globe, Swords, Map, Trash2, Edit2,
} from 'lucide-react'
import { ComposableMap, Geographies, Geography, ZoomableGroup, type GeoRecord } from 'react-simple-maps'
import clsx from 'clsx'
import { scenariosApi, mapsApi } from '@/api/client'

// ─── Types ──────────────────────────────────────────────────────────────────

type EditorMode = 'real-world' | 'custom'
type Tab = 'factions' | 'map'

interface ScenarioMeta {
  name: string
  description: string
  start_year: number
  start_month: number
}

/** Faction in custom universe mode */
interface CustomFaction {
  id: string
  name: string
  flag: string
  color: string
  leader: string
  capital: string
  ideology: string
  population: number
  stability: number
  // Strategic indices
  sovereignty: number
  food_autonomy: number
  energy_autonomy: number
  economic_independence: number
  security: number
  // Economy
  gdp: number
  gdp_growth: number
  inflation: number
  unemployment: number
  debt_pct_gdp: number
  budget_balance_pct_gdp: number
  currency: string
  main_sectors: string[]
  sector_agriculture: number
  sector_industrie: number
  sector_services: number
  // Military
  active_personnel: number
  nuclear_weapons: boolean
  defense_budget_pct: number
  equipment: Record<string, number>
  // Diplomacy / AI
  personality_traits: string[]
  personality: string
  description: string
}

/** Country draft in real-world mode */
interface CountryDraft {
  id: string
  name: string
  flag: string
  continent: string
  leader: string
  ideology: string
  color: string
  // Stability & indices
  stability: number
  sovereignty: number
  food_autonomy: number
  energy_autonomy: number
  economic_independence: number
  security: number
  // Economy
  gdp: number
  gdp_growth: number
  inflation: number
  unemployment: number
  debt_pct_gdp: number
  budget_balance_pct_gdp: number
  currency: string
  main_sectors: string[]
  sector_agriculture: number
  sector_industrie: number
  sector_services: number
  // Military
  active_personnel: number
  nuclear_weapons: boolean
  defense_budget_pct: number
  equipment: Record<string, number>
  // Diplomacy
  personality_traits: string[]
  personality: string
}

/** Detected GeoJSON feature */
interface MapFeature {
  id: string
  displayName: string
}

// ─── Constants ───────────────────────────────────────────────────────────────

const CONTINENTS = ['All', 'North America', 'South America', 'Europe', 'Asia', 'Africa', 'Oceania', 'Middle East']

const PALETTE = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6',
  '#3b82f6', '#8b5cf6', '#ec4899', '#78716c', '#94a3b8',
  '#0ea5e9', '#10b981', '#f59e0b', '#6366f1', '#e11d48',
]

const ID_PRIORITY = ['id', 'ID', 'code', 'CODE', 'key', 'KEY', 'ref', 'REF', 'name', 'NAME', 'label', 'LABEL']

function slugify(name: string): string {
  return name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '').slice(0, 20) || 'faction'
}

function autoDetectIdProp(features: object[]): string {
  if (!features.length) return 'id'
  const props = (features[0] as Record<string, unknown>).properties as Record<string, unknown> | null
  if (!props) return '_feature_id'
  for (const key of ID_PRIORITY) {
    if (key in props) return key
  }
  return Object.keys(props)[0] ?? '_feature_id'
}

function extractFeatures(geojson: object, idProp: string): MapFeature[] {
  const fc = geojson as { type: string; features?: object[] }
  const features = fc.type === 'FeatureCollection' ? (fc.features ?? []) : [geojson]
  return features.map((f: object, i) => {
    const feat = f as { id?: unknown; properties?: Record<string, unknown> }
    const props = feat.properties ?? {}
    const rawId = idProp === '_feature_id'
      ? String(feat.id ?? i)
      : String(props[idProp] ?? feat.id ?? i)
    const displayName = String(props.name ?? props.NAME ?? props.label ?? rawId)
    return { id: rawId, displayName }
  })
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function ScenarioEditor() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const editId = searchParams.get('edit')

  // ── Meta
  const [meta, setMeta] = useState<ScenarioMeta>({ name: '', description: '', start_year: 2025, start_month: 1 })
  const [mode, setMode] = useState<EditorMode>('real-world')
  const [tab, setTab] = useState<Tab>('factions')

  // ── Real-world mode state
  const [rwCountries, setRwCountries] = useState<CountryDraft[]>([])
  const [rawBase, setRawBase] = useState<Record<string, object>>({})
  const [rwSearch, setRwSearch] = useState('')
  const [rwContinent, setRwContinent] = useState('All')
  const [rwExpanded, setRwExpanded] = useState<string | null>(null)
  const [rwTraitInput, setRwTraitInput] = useState('')

  // ── Custom mode state
  const [factions, setFactions] = useState<CustomFaction[]>([])
  const [expandedFaction, setExpandedFaction] = useState<string | null>(null)
  const [factionTraitInput, setFactionTraitInput] = useState('')

  // ── Faction sub-form state (equipment / sectors / traits)
  const [equipKeyInput, setEquipKeyInput] = useState('')
  const [equipValInput, setEquipValInput] = useState('')
  const [sectorInput, setSectorInput] = useState('')

  // ── Custom map state
  const [mapFile, setMapFile] = useState<File | null>(null)
  const [mapGeoJson, setMapGeoJson] = useState<object | null>(null)
  const [mapId, setMapId] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [availableProps, setAvailableProps] = useState<string[]>([])
  const [featureIdProp, setFeatureIdProp] = useState('id')
  const [territories, setTerritories] = useState<Record<string, string>>({})
  const [mapFeatures, setMapFeatures] = useState<MapFeature[]>([])
  const [featSearch, setFeatSearch] = useState('')
  const dropRef = useRef<HTMLDivElement>(null)

  // ── Shared
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savedOk, setSavedOk] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ─── Load base data on mount ─────────────────────────────────────────────
  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        if (editId) {
          const scenario = await scenariosApi.get(editId)
          setMeta({ name: scenario.name, description: scenario.description, start_year: scenario.start_year, start_month: scenario.start_month ?? 1 })
          if (scenario.custom_map_id) {
            setMode('custom')
            setMapId(scenario.custom_map_id)
            setFeatureIdProp(scenario.custom_map_feature_id_property ?? 'id')
            setTerritories(scenario.initial_territories ?? {})
            // Build faction list from countries
            setFactions(Object.values(scenario.countries as Record<string, object>).map(cToFaction))
          } else {
            setMode('real-world')
            setRawBase(scenario.countries)
            setRwCountries(Object.values(scenario.countries as Record<string, object>).map(cToCountryDraft).sort((a, b) => a.name.localeCompare(b.name)))
          }
        } else {
          // Load default scenario as base for real-world mode
          const scenarios = await scenariosApi.list()
          const base = scenarios.find((s: { custom: boolean }) => !s.custom) ?? scenarios[0]
          if (base) {
            const scenario = await scenariosApi.get(base.id)
            setRawBase(scenario.countries)
            setRwCountries(Object.values(scenario.countries as Record<string, object>).map(cToCountryDraft).sort((a, b) => a.name.localeCompare(b.name)))
          }
        }
      } catch {
        setError('Failed to load base data.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [editId])

  // ─── GeoJSON helpers ─────────────────────────────────────────────────────
  function handleFileChange(file: File) {
    setMapFile(file)
    setUploadError(null)
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const parsed = JSON.parse(e.target?.result as string)
        setMapGeoJson(parsed)
        const fc = parsed.type === 'FeatureCollection' ? (parsed.features ?? []) : [parsed]
        const detectedProp = autoDetectIdProp(fc)
        // Available props from first feature
        const firstProps = fc[0]?.properties ?? {}
        const props: string[] = Object.keys(firstProps)
        if (fc[0]?.id !== undefined) props.unshift('_feature_id')
        setAvailableProps(props)
        setFeatureIdProp(detectedProp)
        const feats = extractFeatures(parsed, detectedProp)
        setMapFeatures(feats)
        // Upload to backend
        setUploading(true)
        const result = await mapsApi.upload(file)
        setMapId(result.map_id)
      } catch (err) {
        setUploadError((err as Error).message || 'Error loading file')
      } finally {
        setUploading(false)
      }
    }
    reader.readAsText(file)
  }

  useEffect(() => {
    if (mapGeoJson && featureIdProp) {
      setMapFeatures(extractFeatures(mapGeoJson, featureIdProp))
    }
  }, [featureIdProp, mapGeoJson])

  // ─── Drag & drop for GeoJSON ─────────────────────────────────────────────
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFileChange(file)
  }, [])

  // ─── Type helpers ─────────────────────────────────────────────────────────
  function cToCountryDraft(c: object): CountryDraft {
    const country = c as Record<string, unknown>
    const econ = (country.economy as Record<string, unknown>) ?? {}
    const mil = (country.military as Record<string, unknown>) ?? {}
    const ns = (country.national_stats as Record<string, unknown>) ?? {}
    const sectors = (econ.sectors as Record<string, unknown>) ?? {}
    return {
      id: String(country.id ?? ''),
      name: String(country.name ?? ''),
      flag: String(country.flag ?? ''),
      continent: String(country.continent ?? ''),
      leader: String(country.leader ?? ''),
      ideology: String(country.ideology ?? ''),
      color: String(country.color ?? ''),
      stability: Number(country.initial_stability ?? 50),
      sovereignty: Number(ns.sovereignty ?? 50),
      food_autonomy: Number(ns.food_autonomy ?? 50),
      energy_autonomy: Number(ns.energy_autonomy ?? 50),
      economic_independence: Number(ns.economic_independence ?? 50),
      security: Number(ns.security ?? 50),
      gdp: Number(econ.gdp ?? 0),
      gdp_growth: Number(econ.gdp_growth ?? 0),
      inflation: Number(econ.inflation ?? 2),
      unemployment: Number(econ.unemployment ?? 5),
      debt_pct_gdp: Number(econ.debt_pct_gdp ?? 50),
      budget_balance_pct_gdp: Number(econ.budget_balance_pct_gdp ?? -2),
      currency: String(econ.currency ?? ''),
      main_sectors: Array.isArray(econ.main_sectors) ? (econ.main_sectors as string[]) : [],
      sector_agriculture: Number(sectors.agriculture ?? 20),
      sector_industrie: Number(sectors.industrie ?? 30),
      sector_services: Number(sectors.services ?? 50),
      active_personnel: Number(mil.active_personnel ?? 0),
      nuclear_weapons: Boolean(mil.nuclear_weapons ?? false),
      defense_budget_pct: Number(mil.defense_budget_pct ?? 2),
      equipment: (mil.equipment as Record<string, number>) ?? {},
      personality_traits: Array.isArray(country.personality_traits) ? (country.personality_traits as string[]) : [],
      personality: String(country.personality ?? ''),
    }
  }

  function cToFaction(c: object): CustomFaction {
    const country = c as Record<string, unknown>
    const econ = (country.economy as Record<string, unknown>) ?? {}
    const mil = (country.military as Record<string, unknown>) ?? {}
    const ns = (country.national_stats as Record<string, unknown>) ?? {}
    const sectors = (econ.sectors as Record<string, unknown>) ?? {}
    return {
      id: String(country.id ?? ''),
      name: String(country.name ?? ''),
      flag: String(country.flag ?? '🏳️'),
      color: String(country.color ?? '#3b82f6'),
      leader: String(country.leader ?? ''),
      capital: String(country.capital ?? ''),
      ideology: String(country.ideology ?? ''),
      population: Number(country.population ?? 0),
      stability: Number(country.initial_stability ?? country.stability ?? 50),
      sovereignty: Number(ns.sovereignty ?? 50),
      food_autonomy: Number(ns.food_autonomy ?? 50),
      energy_autonomy: Number(ns.energy_autonomy ?? 50),
      economic_independence: Number(ns.economic_independence ?? 50),
      security: Number(ns.security ?? 50),
      gdp: Number(econ.gdp ?? 0),
      gdp_growth: Number(econ.gdp_growth ?? 0),
      inflation: Number(econ.inflation ?? 2),
      unemployment: Number(econ.unemployment ?? 5),
      debt_pct_gdp: Number(econ.debt_pct_gdp ?? 50),
      budget_balance_pct_gdp: Number(econ.budget_balance_pct_gdp ?? -2),
      currency: String(econ.currency ?? ''),
      main_sectors: Array.isArray(econ.main_sectors) ? (econ.main_sectors as string[]) : [],
      sector_agriculture: Number(sectors.agriculture ?? 20),
      sector_industrie: Number(sectors.industrie ?? 30),
      sector_services: Number(sectors.services ?? 50),
      active_personnel: Number(mil.active_personnel ?? 0),
      nuclear_weapons: Boolean(mil.nuclear_weapons ?? false),
      defense_budget_pct: Number(mil.defense_budget_pct ?? 2),
      equipment: (mil.equipment as Record<string, number>) ?? {},
      personality_traits: Array.isArray(country.personality_traits) ? (country.personality_traits as string[]) : [],
      personality: String(country.personality ?? ''),
      description: String(country.description ?? ''),
    }
  }

  // ─── Real-world mode ─────────────────────────────────────────────────────
  const rwFiltered = useMemo(() => rwCountries.filter((c) => {
    const ms = !rwSearch || c.name.toLowerCase().includes(rwSearch.toLowerCase()) || c.id.toLowerCase().includes(rwSearch.toLowerCase())
    const mc = rwContinent === 'All' || c.continent === rwContinent
    return ms && mc
  }), [rwCountries, rwSearch, rwContinent])

  function updateRwCountry(id: string, patch: Partial<CountryDraft>) {
    setRwCountries((prev) => prev.map((c) => c.id === id ? { ...c, ...patch } : c))
  }

  function addRwTrait(id: string, trait: string) {
    const t = trait.trim()
    if (!t) return
    const c = rwCountries.find((x) => x.id === id)
    if (!c || c.personality_traits.includes(t)) return
    updateRwCountry(id, { personality_traits: [...c.personality_traits, t] })
    setRwTraitInput('')
  }

  // ─── Custom mode: factions ────────────────────────────────────────────────
  function addFaction() {
    const newF: CustomFaction = {
      id: `faction_${Date.now()}`,
      name: 'New faction',
      flag: '🏳️',
      color: PALETTE[factions.length % PALETTE.length],
      leader: '',
      capital: '',
      ideology: '',
      population: 1000000,
      stability: 50,
      sovereignty: 50,
      food_autonomy: 50,
      energy_autonomy: 50,
      economic_independence: 50,
      security: 50,
      gdp: 100,
      gdp_growth: 0,
      inflation: 2,
      unemployment: 5,
      debt_pct_gdp: 50,
      budget_balance_pct_gdp: -2,
      currency: '',
      main_sectors: [],
      sector_agriculture: 20,
      sector_industrie: 30,
      sector_services: 50,
      active_personnel: 0,
      nuclear_weapons: false,
      defense_budget_pct: 2,
      equipment: {},
      personality_traits: [],
      personality: '',
      description: '',
    }
    setFactions((prev) => [...prev, newF])
    setExpandedFaction(newF.id)
  }

  function updateFaction(id: string, patch: Partial<CustomFaction>) {
    setFactions((prev) => prev.map((f) => f.id === id ? { ...f, ...patch } : f))
  }

  function removeFaction(id: string) {
    setFactions((prev) => prev.filter((f) => f.id !== id))
    setTerritories((prev) => {
      const next = { ...prev }
      Object.keys(next).forEach((k) => { if (next[k] === id) delete next[k] })
      return next
    })
  }

  function addFactionTrait(fid: string, trait: string) {
    const t = trait.trim()
    if (!t) return
    const f = factions.find((x) => x.id === fid)
    if (!f || f.personality_traits.includes(t)) return
    updateFaction(fid, { personality_traits: [...f.personality_traits, t] })
    setFactionTraitInput('')
  }

  function updateFactionId(oldId: string, newId: string) {
    const slug = slugify(newId) || oldId
    updateFaction(oldId, { id: slug })
    setFactions((prev) => prev.map((f) => f.id === oldId ? { ...f, id: slug } : f))
    // Update territories that reference old id
    setTerritories((prev) => {
      const next: Record<string, string> = {}
      Object.entries(prev).forEach(([k, v]) => { next[k] = v === oldId ? slug : v })
      return next
    })
    if (expandedFaction === oldId) setExpandedFaction(slug)
  }

  // ─── Save ─────────────────────────────────────────────────────────────────
  async function save() {
    if (!meta.name.trim()) { setError('Scenario name is required.'); return }
    if (mode === 'custom' && !mapId) { setError('Please upload a GeoJSON map.'); return }
    if (mode === 'custom' && factions.length === 0) { setError('Create at least one faction.'); return }
    setSaving(true)
    setError(null)
    try {
      let countriesObj: Record<string, object> = {}

      if (mode === 'real-world') {
        rwCountries.forEach((c) => {
          const base = (rawBase[c.id] ?? {}) as Record<string, unknown>
          countriesObj[c.id] = {
            ...base,
            leader: c.leader,
            ideology: c.ideology,
            color: c.color || base.color,
            initial_stability: c.stability,
            national_stats: { sovereignty: c.sovereignty, food_autonomy: c.food_autonomy, energy_autonomy: c.energy_autonomy, economic_independence: c.economic_independence, security: c.security },
            economy: {
              ...((base.economy as object) ?? {}),
              gdp: c.gdp,
              gdp_per_capita: c.gdp > 0 && (base.population as number) > 0 ? Math.round(c.gdp * 1e9 / (base.population as number)) : 0,
              gdp_growth: c.gdp_growth,
              inflation: c.inflation,
              unemployment: c.unemployment,
              debt_pct_gdp: c.debt_pct_gdp,
              budget_balance_pct_gdp: c.budget_balance_pct_gdp,
              currency: c.currency,
              main_sectors: c.main_sectors,
              sectors: { agriculture: c.sector_agriculture, industrie: c.sector_industrie, services: c.sector_services },
            },
            military: {
              ...((base.military as object) ?? {}),
              active_personnel: c.active_personnel,
              nuclear_weapons: c.nuclear_weapons,
              defense_budget_pct: c.defense_budget_pct,
              equipment: c.equipment,
            },
            personality_traits: c.personality_traits,
            personality: c.personality,
          }
        })
      } else {
        factions.forEach((f) => {
          countriesObj[f.id] = {
            id: f.id,
            name: f.name,
            flag: f.flag,
            color: f.color,
            capital: f.capital,
            continent: '',
            population: f.population,
            initial_stability: f.stability,
            government_type: 'unknown',
            ideology: f.ideology,
            leader: f.leader,
            alliances: [],
            personality_traits: f.personality_traits,
            personality: f.personality,
            description: f.description,
            relations: {},
            national_stats: {
              sovereignty: f.sovereignty,
              food_autonomy: f.food_autonomy,
              energy_autonomy: f.energy_autonomy,
              economic_independence: f.economic_independence,
              security: f.security,
            },
            economy: {
              gdp: f.gdp,
              gdp_per_capita: f.population > 0 ? Math.round(f.gdp * 1e9 / f.population) : 0,
              gdp_growth: f.gdp_growth,
              inflation: f.inflation,
              unemployment: f.unemployment,
              debt_pct_gdp: f.debt_pct_gdp,
              budget_balance_pct_gdp: f.budget_balance_pct_gdp,
              currency: f.currency || 'Units',
              main_sectors: f.main_sectors,
              sectors: { agriculture: f.sector_agriculture, industrie: f.sector_industrie, services: f.sector_services },
            },
            military: {
              strength: Math.max(1, Math.round(f.active_personnel / 100000)) || 1,
              active_personnel: f.active_personnel,
              nuclear_weapons: f.nuclear_weapons,
              defense_budget_pct: f.defense_budget_pct,
              equipment: f.equipment,
            },
          }
        })
      }

      const payload: Record<string, unknown> = {
        ...meta,
        countries: countriesObj,
        alliances: {},
        initial_events: [],
        ...(mode === 'custom' && {
          custom_map_id: mapId,
          custom_map_feature_id_property: featureIdProp,
          initial_territories: territories,
        }),
      }

      if (editId) await scenariosApi.update(editId, payload)
      else await scenariosApi.create(payload)

      setSavedOk(true)
      setTimeout(() => navigate('/'), 1200)
    } catch (e) {
      setError(`Error: ${(e as Error).message}`)
    } finally {
      setSaving(false)
    }
  }

  // ─── Computed stats ───────────────────────────────────────────────────────
  const rwModified = rwCountries.filter((c) => c.personality.trim() || c.personality_traits.length).length
  const featFiltered = useMemo(() => mapFeatures.filter((f) =>
    !featSearch || f.displayName.toLowerCase().includes(featSearch.toLowerCase()) || f.id.toLowerCase().includes(featSearch.toLowerCase())
  ), [mapFeatures, featSearch])

  // ─── Render ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-pax-dark flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pax-accent" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-pax-dark text-white flex flex-col overflow-hidden" style={{ height: '100vh' }}>

      {/* Top bar */}
      <div className="border-b border-pax-border bg-pax-panel px-4 py-3 flex items-center gap-3 shrink-0">
        <button onClick={() => navigate('/')} className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors text-sm">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="flex-1">
          <h1 className="font-semibold text-white text-sm">{editId ? 'Edit scenario' : 'Create scenario'}</h1>
          <p className="text-xs text-slate-400">Real world or fully custom universe</p>
        </div>
        <button
          onClick={save}
          disabled={saving || savedOk}
          className="btn-primary flex items-center gap-2 px-4 py-1.5 text-sm disabled:opacity-60"
        >
          {savedOk ? <Check className="w-4 h-4" /> : saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {savedOk ? 'Saved!' : 'Save'}
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">

        {/* ── Left sidebar ── */}
        <div className="w-72 border-r border-pax-border bg-pax-panel flex flex-col shrink-0 overflow-y-auto">

          {/* Mode selector */}
          <div className="p-4 border-b border-pax-border">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Universe type</p>
            <div className="grid grid-cols-2 gap-1.5">
              <button
                onClick={() => setMode('real-world')}
                className={clsx('flex flex-col items-center gap-1 rounded-lg p-2.5 border text-xs transition-colors', mode === 'real-world' ? 'border-pax-accent bg-pax-accent/10 text-white' : 'border-pax-border text-slate-400 hover:text-slate-200')}
              >
                <Globe className="w-5 h-5" />
                Real world
              </button>
              <button
                onClick={() => setMode('custom')}
                className={clsx('flex flex-col items-center gap-1 rounded-lg p-2.5 border text-xs transition-colors', mode === 'custom' ? 'border-pax-accent bg-pax-accent/10 text-white' : 'border-pax-border text-slate-400 hover:text-slate-200')}
              >
                <Swords className="w-5 h-5" />
                Custom
              </button>
            </div>
            {mode === 'custom' && (
              <p className="text-xs text-slate-500 mt-2">LoTR, Star Wars, Warhammer, Napoleon…</p>
            )}
          </div>

          {/* Metadata */}
          <div className="p-4 space-y-3 border-b border-pax-border">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Scenario</p>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Name *</label>
              <input type="text" value={meta.name} onChange={(e) => setMeta((m) => ({ ...m, name: e.target.value }))} placeholder="E.g. War of the Rings" className="input-field w-full text-sm" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Description</label>
              <textarea value={meta.description} onChange={(e) => setMeta((m) => ({ ...m, description: e.target.value }))} rows={3} placeholder="Narrative context…" className="input-field w-full text-sm resize-none" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Year</label>
                <input type="number" value={meta.start_year} onChange={(e) => setMeta((m) => ({ ...m, start_year: parseInt(e.target.value) || 2025 }))} className="input-field w-full text-sm" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Month</label>
                <select value={meta.start_month} onChange={(e) => setMeta((m) => ({ ...m, start_month: parseInt(e.target.value) }))} className="input-field w-full text-sm">
                  {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map((m, i) => (
                    <option key={i} value={i + 1}>{m}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="p-4 text-xs text-slate-400 space-y-1">
            {mode === 'real-world' ? (
              <>
                <div><span className="text-white font-medium">{rwCountries.length}</span> countries</div>
                <div><span className="text-pax-accent font-medium">{rwModified}</span> with personality defined</div>
              </>
            ) : (
              <>
                <div><span className="text-white font-medium">{factions.length}</span> factions created</div>
                <div><span className="text-pax-accent font-medium">{Object.keys(territories).length}</span> / {mapFeatures.length} territories assigned</div>
                {mapId && <div className="text-green-400">✓ Map uploaded</div>}
              </>
            )}
          </div>

          {/* Tabs (custom mode) */}
          {mode === 'custom' && (
            <div className="px-4 pb-4 space-y-1">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Sections</p>
              <button onClick={() => setTab('factions')} className={clsx('w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors', tab === 'factions' ? 'bg-pax-accent/15 text-white border border-pax-accent/30' : 'text-slate-400 hover:text-slate-200')}>
                <Swords className="w-4 h-4" /> Factions
              </button>
              <button onClick={() => setTab('map')} className={clsx('w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors', tab === 'map' ? 'bg-pax-accent/15 text-white border border-pax-accent/30' : 'text-slate-400 hover:text-slate-200')}>
                <Map className="w-4 h-4" /> Map & Territories
                {!mapId && <span className="ml-auto w-2 h-2 rounded-full bg-amber-400" />}
              </button>
            </div>
          )}

          {error && (
            <div className="mx-4 mb-4 bg-red-900/30 border border-red-700/50 rounded-lg p-3 text-xs text-red-300">{error}</div>
          )}
        </div>

        {/* ── Main content ── */}
        <div className="flex-1 overflow-hidden flex flex-col">

          {/* ═══ REAL-WORLD: country editor ═══ */}
          {mode === 'real-world' && (
            <>
              {/* Filters */}
              <div className="px-4 py-3 border-b border-pax-border flex items-center gap-3 shrink-0">
                <div className="relative flex-1 max-w-xs">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                  <input type="text" value={rwSearch} onChange={(e) => setRwSearch(e.target.value)} placeholder="Search…" className="input-field w-full pl-8 text-sm py-1.5" />
                </div>
                <div className="flex gap-1 overflow-x-auto">
                  {CONTINENTS.map((c) => (
                    <button key={c} onClick={() => setRwContinent(c)} className={clsx('px-2.5 py-1 rounded text-xs whitespace-nowrap transition-colors shrink-0', rwContinent === c ? 'bg-pax-accent/20 text-pax-accent border border-pax-accent/40' : 'text-slate-400 hover:text-slate-200 border border-transparent')}>
                      {c}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-1.5">
                {rwFiltered.map((country) => {
                  const isOpen = rwExpanded === country.id
                  const hasP = country.personality.trim().length > 0
                  return (
                    <div key={country.id} className={clsx('rounded-lg border transition-colors', isOpen ? 'border-pax-accent/40 bg-slate-800/60' : 'border-pax-border bg-slate-800/30 hover:border-slate-600')}>
                      <button className="w-full flex items-center gap-3 px-3 py-2.5" onClick={() => setRwExpanded(isOpen ? null : country.id)}>
                        <span className="text-lg shrink-0">{country.flag}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-white">{country.name}</span>
                            <span className="text-xs text-slate-500">{country.id}</span>
                            {(hasP || country.personality_traits.length > 0) && (
                              <span className="text-xs bg-pax-accent/20 text-pax-accent px-1.5 py-0.5 rounded">✓</span>
                            )}
                          </div>
                          {hasP && !isOpen && <div className="text-xs text-slate-500 truncate mt-0.5">{country.personality.slice(0, 80)}…</div>}
                        </div>
                        <div className="flex items-center gap-2 shrink-0 text-xs text-slate-500">
                          <span>{country.continent}</span>
                          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </div>
                      </button>
                      {isOpen && (
                        <div className="px-3 pb-4 pt-2 space-y-5 border-t border-pax-border/50">

                          {/* ── Politics ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Politics</p>
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Leader</label>
                                <input type="text" value={country.leader} onChange={(e) => updateRwCountry(country.id, { leader: e.target.value })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Ideology</label>
                                <input type="text" value={country.ideology} onChange={(e) => updateRwCountry(country.id, { ideology: e.target.value })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                          </div>

                          {/* ── Stability & Indices ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Stability & Strategic indices</p>
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Initial stability (0-100)</label>
                                <input type="number" min={0} max={100} value={country.stability} onChange={(e) => updateRwCountry(country.id, { stability: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Sovereignty (%)</label>
                                <input type="number" min={0} max={100} value={country.sovereignty} onChange={(e) => updateRwCountry(country.id, { sovereignty: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Food self-sufficiency (%)</label>
                                <input type="number" min={0} max={100} value={country.food_autonomy} onChange={(e) => updateRwCountry(country.id, { food_autonomy: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Energy autonomy (%)</label>
                                <input type="number" min={0} max={100} value={country.energy_autonomy} onChange={(e) => updateRwCountry(country.id, { energy_autonomy: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Eco. independence (%)</label>
                                <input type="number" min={0} max={100} value={country.economic_independence} onChange={(e) => updateRwCountry(country.id, { economic_independence: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Internal security (%)</label>
                                <input type="number" min={0} max={100} value={country.security} onChange={(e) => updateRwCountry(country.id, { security: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                          </div>

                          {/* ── Economy ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Economy</p>
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">GDP (B$)</label>
                                <input type="number" value={country.gdp} onChange={(e) => updateRwCountry(country.id, { gdp: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Growth (%)</label>
                                <input type="number" step={0.1} value={country.gdp_growth} onChange={(e) => updateRwCountry(country.id, { gdp_growth: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Inflation (%)</label>
                                <input type="number" step={0.1} value={country.inflation} onChange={(e) => updateRwCountry(country.id, { inflation: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Unemployment (%)</label>
                                <input type="number" step={0.1} value={country.unemployment} onChange={(e) => updateRwCountry(country.id, { unemployment: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Debt / GDP (%)</label>
                                <input type="number" step={0.1} value={country.debt_pct_gdp} onChange={(e) => updateRwCountry(country.id, { debt_pct_gdp: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Budget balance (% GDP)</label>
                                <input type="number" step={0.1} value={country.budget_balance_pct_gdp} onChange={(e) => updateRwCountry(country.id, { budget_balance_pct_gdp: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Currency</label>
                                <input type="text" value={country.currency} onChange={(e) => updateRwCountry(country.id, { currency: e.target.value })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1.5">Main sectors</label>
                              <div className="flex flex-wrap gap-1.5 mb-2">
                                {country.main_sectors.map((s) => (
                                  <span key={s} className="flex items-center gap-1 bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full">
                                    {s}
                                    <button onClick={() => updateRwCountry(country.id, { main_sectors: country.main_sectors.filter((x) => x !== s) })} className="text-slate-500 hover:text-red-400"><X className="w-3 h-3" /></button>
                                  </span>
                                ))}
                              </div>
                              <div className="flex gap-2">
                                <input type="text" value={sectorInput} onChange={(e) => setSectorInput(e.target.value)}
                                  onKeyDown={(e) => { if (e.key === 'Enter' && sectorInput.trim() && !country.main_sectors.includes(sectorInput.trim())) { updateRwCountry(country.id, { main_sectors: [...country.main_sectors, sectorInput.trim()] }); setSectorInput('') } }}
                                  placeholder="E.g. Oil (Enter)" className="input-field flex-1 text-xs" />
                                <button onClick={() => { const v = sectorInput.trim(); if (v && !country.main_sectors.includes(v)) { updateRwCountry(country.id, { main_sectors: [...country.main_sectors, v] }); setSectorInput('') } }} className="btn-secondary px-2 py-1 text-xs"><Plus className="w-3.5 h-3.5" /></button>
                              </div>
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                              <div>
                                <label className="block text-xs text-slate-500 mb-1">Agriculture (%)</label>
                                <input type="number" min={0} max={100} value={country.sector_agriculture} onChange={(e) => updateRwCountry(country.id, { sector_agriculture: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-500 mb-1">Industry (%)</label>
                                <input type="number" min={0} max={100} value={country.sector_industrie} onChange={(e) => updateRwCountry(country.id, { sector_industrie: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-500 mb-1">Services (%)</label>
                                <input type="number" min={0} max={100} value={country.sector_services} onChange={(e) => updateRwCountry(country.id, { sector_services: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                          </div>

                          {/* ── Military ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Military</p>
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Active personnel</label>
                                <input type="number" value={country.active_personnel} onChange={(e) => updateRwCountry(country.id, { active_personnel: parseInt(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Defense budget (% GDP)</label>
                                <input type="number" step={0.1} min={0} value={country.defense_budget_pct} onChange={(e) => updateRwCountry(country.id, { defense_budget_pct: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                            <label className="flex items-center gap-2 cursor-pointer select-none">
                              <input type="checkbox" checked={country.nuclear_weapons} onChange={(e) => updateRwCountry(country.id, { nuclear_weapons: e.target.checked })} className="w-4 h-4 rounded accent-pax-accent" />
                              <span className="text-xs text-slate-300">Nuclear weapons</span>
                            </label>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1.5">Arsenal</label>
                              <div className="space-y-1.5 mb-2">
                                {Object.entries(country.equipment).map(([key, val]) => (
                                  <div key={key} className="flex items-center gap-2 bg-slate-800/60 rounded px-2 py-1">
                                    <span className="text-xs text-white flex-1">{key}</span>
                                    <input type="number" value={val} onChange={(e) => updateRwCountry(country.id, { equipment: { ...country.equipment, [key]: parseInt(e.target.value) || 0 } })} className="w-20 text-xs bg-slate-700 border border-pax-border rounded px-2 py-0.5 text-white focus:outline-none focus:border-pax-accent" />
                                    <button onClick={() => { const eq = { ...country.equipment }; delete eq[key]; updateRwCountry(country.id, { equipment: eq }) }} className="text-slate-500 hover:text-red-400"><X className="w-3.5 h-3.5" /></button>
                                  </div>
                                ))}
                              </div>
                              <div className="flex gap-2">
                                <input type="text" value={equipKeyInput} onChange={(e) => setEquipKeyInput(e.target.value)} placeholder="E.g. battle_tanks" className="input-field flex-1 text-xs" />
                                <input type="number" value={equipValInput} onChange={(e) => setEquipValInput(e.target.value)} placeholder="100" className="input-field w-20 text-xs" />
                                <button onClick={() => { const k = equipKeyInput.trim(); const v = parseInt(equipValInput) || 0; if (!k) return; updateRwCountry(country.id, { equipment: { ...country.equipment, [k]: v } }); setEquipKeyInput(''); setEquipValInput('') }} className="btn-secondary px-2 py-1 text-xs"><Plus className="w-3.5 h-3.5" /></button>
                              </div>
                            </div>
                          </div>

                          {/* ── Diplomacy & AI ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Diplomacy & AI</p>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1.5">Diplomatic traits</label>
                              <div className="flex flex-wrap gap-1.5 mb-2">
                                {country.personality_traits.map((t) => (
                                  <span key={t} className="flex items-center gap-1 bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full">
                                    {t}
                                    <button onClick={() => updateRwCountry(country.id, { personality_traits: country.personality_traits.filter((x) => x !== t) })} className="text-slate-500 hover:text-red-400"><X className="w-3 h-3" /></button>
                                  </span>
                                ))}
                              </div>
                              <div className="flex gap-2">
                                <input type="text" value={rwTraitInput} onChange={(e) => setRwTraitInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') addRwTrait(country.id, rwTraitInput) }} placeholder="Add a trait" className="input-field flex-1 text-xs" />
                                <button onClick={() => addRwTrait(country.id, rwTraitInput)} className="btn-secondary px-2 py-1 text-xs"><Plus className="w-3.5 h-3.5" /></button>
                              </div>
                            </div>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1">Diplomatic personality <span className="text-slate-500">(injected into the AI prompt)</span></label>
                              <textarea value={country.personality} onChange={(e) => updateRwCountry(country.id, { personality: e.target.value })} rows={3} placeholder={`Diplomatic style of ${country.name}…`} className="input-field w-full text-sm resize-none" />
                            </div>
                          </div>

                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </>
          )}

          {/* ═══ CUSTOM: factions ═══ */}
          {mode === 'custom' && tab === 'factions' && (
            <div className="flex-1 overflow-y-auto p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-white">Factions / Powers</h2>
                <button onClick={addFaction} className="btn-primary flex items-center gap-1.5 px-3 py-1.5 text-sm">
                  <Plus className="w-4 h-4" /> Add
                </button>
              </div>
              {factions.length === 0 && (
                <div className="text-center py-16 text-slate-500 text-sm">
                  <Swords className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p>No factions created.</p>
                  <p className="text-xs mt-1">Click "Add" to create your first faction.</p>
                </div>
              )}
              <div className="space-y-2">
                {factions.map((f) => {
                  const isOpen = expandedFaction === f.id
                  return (
                    <div key={f.id} className={clsx('rounded-lg border transition-colors', isOpen ? 'border-pax-accent/50 bg-slate-800/70' : 'border-pax-border bg-slate-800/30 hover:border-slate-600')}>
                      {/* Header */}
                      <div className="flex items-center gap-3 px-3 py-2.5">
                        <div className="w-4 h-4 rounded-sm shrink-0 border border-white/20" style={{ background: f.color }} />
                        <span className="text-lg shrink-0 leading-none">{f.flag}</span>
                        <button className="flex-1 text-left" onClick={() => setExpandedFaction(isOpen ? null : f.id)}>
                          <div className="text-sm font-medium text-white">{f.name}</div>
                          <div className="text-xs text-slate-500">{f.id}{f.leader ? ` · ${f.leader}` : ''}</div>
                        </button>
                        <div className="flex items-center gap-1 shrink-0">
                          <button onClick={() => setExpandedFaction(isOpen ? null : f.id)} className="text-slate-400 hover:text-white p-1">
                            {isOpen ? <ChevronUp className="w-4 h-4" /> : <Edit2 className="w-4 h-4" />}
                          </button>
                          <button onClick={() => removeFaction(f.id)} className="text-slate-500 hover:text-red-400 p-1">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {/* Expanded form */}
                      {isOpen && (
                        <div className="px-3 pb-4 pt-2 border-t border-pax-border/50 space-y-5">

                          {/* ── IDENTITY ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Identity</p>
                            <div className="grid grid-cols-3 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Emoji / Emblem</label>
                                <input type="text" value={f.flag} onChange={(e) => updateFaction(f.id, { flag: e.target.value })} className="input-field w-full text-center text-lg" maxLength={4} />
                              </div>
                              <div className="col-span-2">
                                <label className="block text-xs text-slate-400 mb-1">Faction name</label>
                                <input type="text" value={f.name} onChange={(e) => updateFaction(f.id, { name: e.target.value })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                            <div className="grid grid-cols-3 gap-2 items-end">
                              <div className="col-span-2">
                                <label className="block text-xs text-slate-400 mb-1">ID <span className="text-slate-500">(territory key)</span></label>
                                <input type="text" value={f.id} onChange={(e) => updateFactionId(f.id, e.target.value)} className="input-field w-full text-sm font-mono" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Color</label>
                                <div className="flex gap-1 flex-wrap">
                                  {PALETTE.map((c) => (
                                    <button key={c} onClick={() => updateFaction(f.id, { color: c })} className={clsx('w-5 h-5 rounded-sm border-2 transition-all', f.color === c ? 'border-white scale-110' : 'border-transparent')} style={{ background: c }} />
                                  ))}
                                </div>
                              </div>
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Leader</label>
                                <input type="text" value={f.leader} onChange={(e) => updateFaction(f.id, { leader: e.target.value })} placeholder="Name" className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Capital</label>
                                <input type="text" value={f.capital} onChange={(e) => updateFaction(f.id, { capital: e.target.value })} placeholder="City" className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Ideology</label>
                                <input type="text" value={f.ideology} onChange={(e) => updateFaction(f.id, { ideology: e.target.value })} placeholder="E.g. monarchy" className="input-field w-full text-sm" />
                              </div>
                            </div>
                          </div>

                          {/* ── STABILITY & INDICES ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Stability & Strategic indices</p>
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Population</label>
                                <input type="number" value={f.population} onChange={(e) => updateFaction(f.id, { population: parseInt(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Stability (0-100)</label>
                                <input type="number" min={0} max={100} value={f.stability} onChange={(e) => updateFaction(f.id, { stability: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Sovereignty (%)</label>
                                <input type="number" min={0} max={100} value={f.sovereignty} onChange={(e) => updateFaction(f.id, { sovereignty: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Food self-sufficiency (%)</label>
                                <input type="number" min={0} max={100} value={f.food_autonomy} onChange={(e) => updateFaction(f.id, { food_autonomy: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Energy autonomy (%)</label>
                                <input type="number" min={0} max={100} value={f.energy_autonomy} onChange={(e) => updateFaction(f.id, { energy_autonomy: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Eco. independence (%)</label>
                                <input type="number" min={0} max={100} value={f.economic_independence} onChange={(e) => updateFaction(f.id, { economic_independence: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Internal security (%)</label>
                                <input type="number" min={0} max={100} value={f.security} onChange={(e) => updateFaction(f.id, { security: Math.max(0, Math.min(100, parseInt(e.target.value) || 50)) })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                          </div>

                          {/* ── ECONOMY ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Economy</p>
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">GDP (B$)</label>
                                <input type="number" value={f.gdp} onChange={(e) => updateFaction(f.id, { gdp: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Growth (%)</label>
                                <input type="number" step={0.1} value={f.gdp_growth} onChange={(e) => updateFaction(f.id, { gdp_growth: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Inflation (%)</label>
                                <input type="number" step={0.1} value={f.inflation} onChange={(e) => updateFaction(f.id, { inflation: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Unemployment (%)</label>
                                <input type="number" step={0.1} value={f.unemployment} onChange={(e) => updateFaction(f.id, { unemployment: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Debt / GDP (%)</label>
                                <input type="number" step={0.1} value={f.debt_pct_gdp} onChange={(e) => updateFaction(f.id, { debt_pct_gdp: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Budget balance (% GDP)</label>
                                <input type="number" step={0.1} value={f.budget_balance_pct_gdp} onChange={(e) => updateFaction(f.id, { budget_balance_pct_gdp: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Currency</label>
                                <input type="text" value={f.currency} onChange={(e) => updateFaction(f.id, { currency: e.target.value })} placeholder="E.g. Ducats" className="input-field w-full text-sm" />
                              </div>
                            </div>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1.5">Main sectors <span className="text-slate-500">(tags)</span></label>
                              <div className="flex flex-wrap gap-1.5 mb-2">
                                {f.main_sectors.map((s) => (
                                  <span key={s} className="flex items-center gap-1 bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full">
                                    {s}
                                    <button onClick={() => updateFaction(f.id, { main_sectors: f.main_sectors.filter((x) => x !== s) })} className="text-slate-500 hover:text-red-400"><X className="w-3 h-3" /></button>
                                  </span>
                                ))}
                              </div>
                              <div className="flex gap-2">
                                <input type="text" value={sectorInput} onChange={(e) => setSectorInput(e.target.value)}
                                  onKeyDown={(e) => { if (e.key === 'Enter' && sectorInput.trim() && !f.main_sectors.includes(sectorInput.trim())) { updateFaction(f.id, { main_sectors: [...f.main_sectors, sectorInput.trim()] }); setSectorInput('') } }}
                                  placeholder="E.g. Agriculture (Enter)" className="input-field flex-1 text-xs" />
                                <button onClick={() => { const v = sectorInput.trim(); if (v && !f.main_sectors.includes(v)) { updateFaction(f.id, { main_sectors: [...f.main_sectors, v] }); setSectorInput('') } }} className="btn-secondary px-2 py-1 text-xs"><Plus className="w-3.5 h-3.5" /></button>
                              </div>
                            </div>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1.5">Sector breakdown <span className="text-slate-500">(ideally totals 100%)</span></label>
                              <div className="grid grid-cols-3 gap-2">
                                <div>
                                  <label className="block text-xs text-slate-500 mb-1">Agriculture (%)</label>
                                  <input type="number" min={0} max={100} value={f.sector_agriculture} onChange={(e) => updateFaction(f.id, { sector_agriculture: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                                </div>
                                <div>
                                  <label className="block text-xs text-slate-500 mb-1">Industry (%)</label>
                                  <input type="number" min={0} max={100} value={f.sector_industrie} onChange={(e) => updateFaction(f.id, { sector_industrie: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                                </div>
                                <div>
                                  <label className="block text-xs text-slate-500 mb-1">Services (%)</label>
                                  <input type="number" min={0} max={100} value={f.sector_services} onChange={(e) => updateFaction(f.id, { sector_services: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* ── MILITARY ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Military</p>
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Active personnel</label>
                                <input type="number" value={f.active_personnel} onChange={(e) => updateFaction(f.id, { active_personnel: parseInt(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                              <div>
                                <label className="block text-xs text-slate-400 mb-1">Defense budget (% GDP)</label>
                                <input type="number" step={0.1} min={0} value={f.defense_budget_pct} onChange={(e) => updateFaction(f.id, { defense_budget_pct: parseFloat(e.target.value) || 0 })} className="input-field w-full text-sm" />
                              </div>
                            </div>
                            <label className="flex items-center gap-2 cursor-pointer select-none">
                              <input type="checkbox" checked={f.nuclear_weapons} onChange={(e) => updateFaction(f.id, { nuclear_weapons: e.target.checked })} className="w-4 h-4 rounded accent-pax-accent" />
                              <span className="text-xs text-slate-300">Nuclear weapons</span>
                            </label>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1.5">Arsenal <span className="text-slate-500">(equipment key → quantity)</span></label>
                              <div className="space-y-1.5 mb-2">
                                {Object.entries(f.equipment).map(([key, val]) => (
                                  <div key={key} className="flex items-center gap-2 bg-slate-800/60 rounded px-2 py-1">
                                    <span className="text-xs text-white flex-1">{key}</span>
                                    <input
                                      type="number"
                                      value={val}
                                      onChange={(e) => updateFaction(f.id, { equipment: { ...f.equipment, [key]: parseInt(e.target.value) || 0 } })}
                                      className="w-20 text-xs bg-slate-700 border border-pax-border rounded px-2 py-0.5 text-white focus:outline-none focus:border-pax-accent"
                                    />
                                    <button onClick={() => { const eq = { ...f.equipment }; delete eq[key]; updateFaction(f.id, { equipment: eq }) }} className="text-slate-500 hover:text-red-400"><X className="w-3.5 h-3.5" /></button>
                                  </div>
                                ))}
                              </div>
                              <div className="flex gap-2">
                                <input type="text" value={equipKeyInput} onChange={(e) => setEquipKeyInput(e.target.value)} placeholder="E.g. battle_tanks" className="input-field flex-1 text-xs" />
                                <input type="number" value={equipValInput} onChange={(e) => setEquipValInput(e.target.value)} placeholder="100" className="input-field w-20 text-xs" />
                                <button
                                  onClick={() => {
                                    const k = equipKeyInput.trim()
                                    const v = parseInt(equipValInput) || 0
                                    if (!k) return
                                    updateFaction(f.id, { equipment: { ...f.equipment, [k]: v } })
                                    setEquipKeyInput('')
                                    setEquipValInput('')
                                  }}
                                  className="btn-secondary px-2 py-1 text-xs"
                                ><Plus className="w-3.5 h-3.5" /></button>
                              </div>
                            </div>
                          </div>

                          {/* ── DIPLOMACY / AI ── */}
                          <div className="space-y-3">
                            <p className="text-xs font-semibold text-pax-accent/80 uppercase tracking-wider">Diplomacy & AI</p>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1.5">Diplomatic traits</label>
                              <div className="flex flex-wrap gap-1.5 mb-2">
                                {f.personality_traits.map((t) => (
                                  <span key={t} className="flex items-center gap-1 bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full">
                                    {t}
                                    <button onClick={() => updateFaction(f.id, { personality_traits: f.personality_traits.filter((x) => x !== t) })} className="text-slate-500 hover:text-red-400"><X className="w-3 h-3" /></button>
                                  </span>
                                ))}
                              </div>
                              <div className="flex gap-2">
                                <input type="text" value={factionTraitInput} onChange={(e) => setFactionTraitInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') addFactionTrait(f.id, factionTraitInput) }} placeholder="Add a trait (Enter)" className="input-field flex-1 text-xs" />
                                <button onClick={() => addFactionTrait(f.id, factionTraitInput)} className="btn-secondary px-2 py-1 text-xs"><Plus className="w-3.5 h-3.5" /></button>
                              </div>
                            </div>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1">
                                Diplomatic personality & behavior
                                <span className="ml-2 text-slate-500">(injected into the AI prompt)</span>
                              </label>
                              <textarea
                                value={f.personality}
                                onChange={(e) => updateFaction(f.id, { personality: e.target.value })}
                                rows={4}
                                placeholder={`Describe how ${f.name} behaves in negotiations. Tone, motivations, red lines, communication style…`}
                                className="input-field w-full text-sm resize-none"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-slate-400 mb-1">General description</label>
                              <textarea value={f.description} onChange={(e) => updateFaction(f.id, { description: e.target.value })} rows={2} placeholder="Historical context, lore…" className="input-field w-full text-sm resize-none" />
                            </div>
                          </div>

                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* ═══ CUSTOM: map & territories ═══ */}
          {mode === 'custom' && tab === 'map' && (
            <div className="flex-1 overflow-hidden flex gap-0">

              {/* Left: upload + config */}
              <div className="w-80 border-r border-pax-border flex flex-col overflow-y-auto shrink-0">
                <div className="p-4 space-y-4">
                  <h2 className="text-sm font-semibold text-white">GeoJSON Map</h2>

                  {/* Drop zone */}
                  <div
                    ref={dropRef}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={onDrop}
                    className={clsx('border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer', mapGeoJson ? 'border-green-600/50 bg-green-950/10' : 'border-pax-border hover:border-pax-accent/50')}
                    onClick={() => document.getElementById('map-file-input')?.click()}
                  >
                    <input id="map-file-input" type="file" accept=".geojson,.json" className="hidden" onChange={(e) => { if (e.target.files?.[0]) handleFileChange(e.target.files[0]) }} />
                    {uploading ? (
                      <><Loader2 className="w-8 h-8 animate-spin text-pax-accent mx-auto mb-2" /><p className="text-xs text-slate-400">Uploading…</p></>
                    ) : mapGeoJson ? (
                      <>
                        <div className="text-green-400 text-2xl mb-1">✓</div>
                        <p className="text-xs text-green-400 font-medium">{mapFile?.name}</p>
                        <p className="text-xs text-slate-500 mt-1">{mapFeatures.length} features detected</p>
                        <p className="text-xs text-slate-500 mt-1 underline">Click to change</p>
                      </>
                    ) : (
                      <>
                        <Upload className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                        <p className="text-sm text-slate-300 font-medium">Drop a GeoJSON file</p>
                        <p className="text-xs text-slate-500 mt-1">or click to browse</p>
                        <p className="text-xs text-slate-600 mt-2">Format: .geojson or .json · Max 50 MB</p>
                      </>
                    )}
                  </div>
                  {uploadError && <p className="text-xs text-red-400">{uploadError}</p>}

                  {/* Property selector */}
                  {mapGeoJson && availableProps.length > 0 && (
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Property identifying territories</label>
                      <select value={featureIdProp} onChange={(e) => setFeatureIdProp(e.target.value)} className="input-field w-full text-sm">
                        {availableProps.map((p) => <option key={p} value={p}>{p === '_feature_id' ? 'Feature ID (feature.id)' : p}</option>)}
                      </select>
                      <p className="text-xs text-slate-500 mt-1">This value will be used as key for faction assignment</p>
                    </div>
                  )}

                  {/* Territory assignment */}
                  {mapFeatures.length > 0 && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-xs text-slate-400 font-medium">Territory assignment</label>
                        <span className="text-xs text-slate-500">{Object.keys(territories).length}/{mapFeatures.length}</span>
                      </div>
                      <div className="relative mb-2">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                        <input type="text" value={featSearch} onChange={(e) => setFeatSearch(e.target.value)} placeholder="Filter features…" className="input-field w-full pl-7 text-xs py-1.5" />
                      </div>
                      <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
                        {featFiltered.map((feat) => {
                          const assigned = territories[feat.id]
                          const faction = factions.find((f) => f.id === assigned)
                          return (
                            <div key={feat.id} className="flex items-center gap-2 bg-slate-800/50 rounded px-2 py-1.5">
                              {faction && <div className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: faction.color }} />}
                              <span className="text-xs text-white flex-1 truncate" title={feat.id}>{feat.displayName}</span>
                              <select
                                value={assigned ?? ''}
                                onChange={(e) => {
                                  const v = e.target.value
                                  setTerritories((prev) => {
                                    const next = { ...prev }
                                    if (v) next[feat.id] = v
                                    else delete next[feat.id]
                                    return next
                                  })
                                }}
                                className="text-xs bg-slate-700 border border-pax-border rounded px-1.5 py-0.5 text-white focus:outline-none focus:border-pax-accent"
                              >
                                <option value="">— neutral —</option>
                                {factions.map((f) => (
                                  <option key={f.id} value={f.id}>{f.flag} {f.name}</option>
                                ))}
                              </select>
                            </div>
                          )
                        })}
                      </div>
                      {factions.length === 0 && (
                        <p className="text-xs text-amber-400 mt-2">⚠ Create factions first to assign them.</p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Right: map preview */}
              <div className="flex-1 relative bg-slate-900/50">
                {mapGeoJson ? (
                  <>
                    <ComposableMap projection="geoMercator" projectionConfig={{ scale: 130, center: [10, 20] }} style={{ width: '100%', height: '100%' }}>
                      <ZoomableGroup zoom={1} minZoom={0.5} maxZoom={10}>
                        <Geographies geography={mapGeoJson as object}>
                          {({ geographies }: { geographies: GeoRecord[] }) =>
                            geographies.map((geo: GeoRecord) => {
                              const props = geo.properties as Record<string, unknown>
                              const fid = String(featureIdProp === '_feature_id' ? (geo.id ?? '') : (props[featureIdProp] ?? geo.id ?? ''))
                              const assignedFaction = factions.find((f) => f.id === (territories[fid] ?? fid))
                              const fill = assignedFaction?.color ?? '#1e293b'
                              const displayName = String(props.name ?? props.NAME ?? props.label ?? fid)
                              return (
                                <Geography
                                  key={geo.rsmKey}
                                  geography={geo}
                                  fill={fill}
                                  stroke="#0f172a"
                                  strokeWidth={0.5}
                                  style={{ default: { outline: 'none' }, hover: { fill: fill, outline: 'none' }, pressed: { outline: 'none' } }}
                                  aria-label={`${displayName} → ${assignedFaction?.name ?? 'Unassigned'}`}
                                />
                              )
                            })
                          }
                        </Geographies>
                      </ZoomableGroup>
                    </ComposableMap>
                    <div className="absolute bottom-3 right-3 panel p-2 text-xs text-slate-400">
                      Scroll to zoom · Drag to pan
                    </div>
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-600 text-sm">
                    <div className="text-center">
                      <Map className="w-16 h-16 mx-auto mb-3 opacity-20" />
                      <p>Upload a GeoJSON file</p>
                      <p className="text-xs mt-1 text-slate-700">to preview your map here</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
