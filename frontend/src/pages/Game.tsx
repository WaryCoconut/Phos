import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Globe, BookOpen, Newspaper, ArrowRight,
  ChevronRight, Send, Loader2, LayoutDashboard, Settings, History, RotateCcw, Save, Swords,
  FileText, AlertTriangle, MessageSquarePlus,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useGameStore } from '@/store/gameStore'
import { gameApi, streamSimulation, streamSummary } from '@/api/client'
import type { SimEvent, SimDuration, MapPOI, StatSnapshot } from '@/types'
import WorldMap from '@/components/Map/WorldMap'
import CountryDashboard from '@/components/Dashboard/CountryDashboard'
import DiplomacyPanel from '@/components/Diplomacy/DiplomacyPanel'
import AdvisorPanel from '@/components/Advisor/AdvisorPanel'
import EventsFeed from '@/components/UI/EventsFeed'
import SettingsModal from '@/components/UI/SettingsModal'
import type { Country, LeftPanel, RightPanel } from '@/types'

interface Snapshot {
  turn: number
  year: number
  month: number
  saved_at: string
}

const months = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

export default function Game() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { gameState, isLoading, loadGame, error } = useGameStore()
  const [leftPanel, setLeftPanel] = useState<LeftPanel>('actions')
  const [rightPanel, setRightPanel] = useState<RightPanel>('advisor')
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null)
  const [mapView, setMapView] = useState<'relations' | 'stability' | 'ideology'>('relations')
  const [showSettings, setShowSettings] = useState(false)
  const [action, setAction] = useState('')
  const [diplomacyTarget, setDiplomacyTarget] = useState<Country | null>(null)
  const [showSnapshots, setShowSnapshots] = useState(false)
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])
  const [isRestoringSnapshot, setIsRestoringSnapshot] = useState(false)
  const [autoSaved, setAutoSaved] = useState(false)
  const [simEvents, setSimEvents] = useState<SimEvent[]>([])
  const [isSimulating, setIsSimulating] = useState(false)
  const [simDone, setSimDone] = useState(false)
  const [streamingPois, setStreamingPois] = useState<MapPOI[]>([])
  const [preSimSnapshot, setPreSimSnapshot] = useState<StatSnapshot | null>(null)
  const [donePayload, setDonePayload] = useState<SimEvent | null>(null)
  const [statHistory, setStatHistory] = useState<StatSnapshot[]>([])
  const [summaryText, setSummaryText] = useState('')
  const [isSummarizing, setIsSummarizing] = useState(false)
  const stopSimRef = useRef<(() => void) | null>(null)
  const stopSummaryRef = useRef<(() => void) | null>(null)
  const simBottomRef = useRef<HTMLDivElement>(null)
  const actionRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (sessionId) {
      loadGame(sessionId)
    }
  }, [sessionId])

  useEffect(() => {
    if (gameState && sessionId) {
      setAutoSaved(true)
      const t = setTimeout(() => setAutoSaved(false), 2000)
      return () => clearTimeout(t)
    }
  }, [gameState?.turn])

  // Record stat snapshots for sparkline charts
  useEffect(() => {
    if (!gameState) return
    const ns = gameState.player_country.national_stats
    const snap: StatSnapshot = {
      turn: gameState.turn,
      stability: gameState.player_country.stability,
      economy_modifier: gameState.player_country.economy_modifier ?? 1.0,
      gdp: gameState.player_country.economy?.gdp,
      sovereignty: ns?.sovereignty,
      food_autonomy: ns?.food_autonomy,
      energy_autonomy: ns?.energy_autonomy,
      economic_independence: ns?.economic_independence,
      security: ns?.security,
    }
    setStatHistory(prev => {
      if (prev.length > 0 && prev[prev.length - 1].turn === snap.turn) return prev
      return [...prev.slice(-19), snap]
    })
  }, [gameState?.turn])

  function openSnapshots() {
    if (!sessionId) return
    gameApi.listSnapshots(sessionId).then(setSnapshots)
    setShowSnapshots(true)
  }

  async function restoreSnapshot(turn: number) {
    if (!sessionId) return
    setIsRestoringSnapshot(true)
    try {
      await gameApi.restoreSnapshot(sessionId, turn)
      await loadGame(sessionId)
      setShowSnapshots(false)
    } catch {
      // ignore
    } finally {
      setIsRestoringSnapshot(false)
    }
  }

  useEffect(() => {
    if (selectedCountry) {
      setRightPanel('dashboard')
    }
  }, [selectedCountry])

  const SIM_DURATIONS: SimDuration[] = [
    { label: '1 week', weeks: 1 },
    { label: '1 month', months: 1 },
    { label: '3 months', months: 3 },
    { label: '6 months', months: 6 },
    { label: '1 year', months: 12 },
  ]

  async function queueAction() {
    if (!action.trim() || !sessionId) return
    await gameApi.queueAction(sessionId, action.trim())
    setAction('')
    await useGameStore.getState().refreshState()
  }

  async function removeAction(index: number) {
    if (!sessionId) return
    await gameApi.removeQueuedAction(sessionId, index)
    await useGameStore.getState().refreshState()
  }

  function startSummary() {
    if (!sessionId || isSummarizing) return
    setSummaryText('')
    setIsSummarizing(true)
    stopSummaryRef.current = streamSummary(
      sessionId,
      (chunk) => setSummaryText(prev => prev + chunk),
      () => setIsSummarizing(false),
      () => setIsSummarizing(false),
    )
  }

  function startSimulation(duration: SimDuration) {
    if (!sessionId || isSimulating) return
    // Snapshot state before simulation for end-of-turn diff
    if (gameState) {
      const ns = gameState.player_country.national_stats
      const mil = gameState.player_country.military
      setPreSimSnapshot({
        turn: gameState.turn,
        stability: gameState.player_country.stability,
        economy_modifier: gameState.player_country.economy_modifier ?? 1.0,
        military_modifier: gameState.player_country.military_modifier ?? 1.0,
        sovereignty: ns?.sovereignty,
        food_autonomy: ns?.food_autonomy,
        energy_autonomy: ns?.energy_autonomy,
        economic_independence: ns?.economic_independence,
        security: ns?.security,
        equipment: mil?.equipment ? { ...mil.equipment } : undefined,
      })
    }
    setSimEvents([])
    setSimDone(false)
    setDonePayload(null)
    setStreamingPois([])
    setSummaryText('')
    setIsSimulating(true)

    stopSimRef.current = streamSimulation(
      sessionId,
      { months: duration.months, weeks: duration.weeks },
      (event) => {
        setSimEvents((prev) => [...prev, event])
        if (event.type === 'poi_added' && event.poi_id && event.poi_coordinates) {
          setStreamingPois((prev) => [...prev, {
            id: event.poi_id!,
            name: event.poi_name ?? 'Point of interest',
            type: event.poi_type ?? 'monument',
            country_id: event.poi_country_id ?? '',
            coordinates: event.poi_coordinates!,
            icon: event.poi_icon ?? '📍',
            year: event.year ?? 0,
            month: event.month ?? 0,
          }])
        }
        setTimeout(() => simBottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
      },
      async (doneEvent) => {
        setDonePayload(doneEvent ?? null)
        setSimDone(true)
        setIsSimulating(false)
        await useGameStore.getState().refreshState()
        setStreamingPois([])
      },
      (err) => {
        setSimEvents((prev) => [...prev, { type: 'error', message: err }])
        setIsSimulating(false)
      },
    )
  }

  function pauseSimulation() {
    stopSimRef.current?.()
    stopSimRef.current = null
    setIsSimulating(false)
    setSimDone(true)
    useGameStore.getState().refreshState()
  }

  function handleCountryClick(countryId: string) {
    const country = gameState?.countries[countryId]
    if (country) {
      setSelectedCountry(country)
      setRightPanel('dashboard')
    }
  }

  function handleDiplomacyTarget(country: Country) {
    setDiplomacyTarget(country)
    setLeftPanel('diplomacy')
  }

  if (isLoading || !gameState) {
    return (
      <div className="h-screen flex items-center justify-center bg-pax-dark">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-pax-accent animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading simulation...</p>
        </div>
      </div>
    )
  }

  const displayCountry = selectedCountry
    ? gameState.countries[selectedCountry.id] || selectedCountry
    : gameState.player_country

  const leftTabs: { id: LeftPanel; icon: React.ElementType; label: string }[] = [
    { id: 'actions', icon: Swords, label: 'Actions' },
    { id: 'diplomacy', icon: Globe, label: 'Diplomacy' },
  ]

  const rightTabs: { id: RightPanel; icon: React.ElementType; label: string }[] = [
    { id: 'advisor', icon: BookOpen, label: 'Advisor' },
    { id: 'dashboard', icon: LayoutDashboard, label: 'Stats' },
    { id: 'events', icon: Newspaper, label: 'News' },
  ]

  return (
    <div className="h-screen flex flex-col bg-pax-dark overflow-hidden">
      <SettingsModal open={showSettings} onClose={() => setShowSettings(false)} />

      {/* Snapshots panel */}
      {showSnapshots && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowSnapshots(false)}>
          <div className="bg-pax-panel border border-pax-border rounded-xl p-5 w-96 max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <History className="w-4 h-4 text-pax-accent" /> Saves
              </h3>
              <button onClick={() => setShowSnapshots(false)} className="text-slate-400 hover:text-white text-sm">✕</button>
            </div>
            {snapshots.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-4">No saves available.</p>
            ) : (
              <div className="overflow-y-auto space-y-2">
                {snapshots.map((snap) => (
                  <div key={snap.turn} className="flex items-center justify-between bg-slate-800 border border-pax-border rounded-lg px-3 py-2.5">
                    <div>
                      <div className="text-sm text-white font-medium">Turn {snap.turn} — {snap.year}/{String(snap.month).padStart(2, '0')}</div>
                      <div className="text-xs text-slate-500">{new Date(snap.saved_at).toLocaleString('en-US')}</div>
                    </div>
                    <button
                      onClick={() => restoreSnapshot(snap.turn)}
                      disabled={isRestoringSnapshot || snap.turn === gameState?.turn}
                      className="btn-secondary text-xs px-3 py-1 flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed"
                      title={snap.turn === gameState?.turn ? 'Current turn' : 'Restore'}
                    >
                      {isRestoringSnapshot ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <><RotateCcw className="w-3.5 h-3.5" /> Restore</>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-pax-panel border-b border-pax-border px-4 py-2.5 flex items-center gap-4 shrink-0">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-white hover:text-pax-accent transition-colors">
          <Globe className="w-5 h-5" />
          <span className="font-bold text-sm">Phos</span>
        </button>

        <div className="h-4 w-px bg-pax-border" />

        <div className="flex items-center gap-2">
          <span className="text-xl">{gameState.player_country.flag || '🏳️'}</span>
          <div>
            <div className="text-sm font-semibold text-white">{gameState.player_country.name}</div>
            <div className="text-xs text-slate-400">{gameState.player_country.leader}</div>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-4">
          <div className="text-center">
            <div className="text-pax-gold font-bold text-sm">{months[gameState.month - 1]} {gameState.year}</div>
            <div className="text-xs text-slate-500">Turn {gameState.turn}</div>
          </div>

          <div className="flex items-center gap-2">
            {(['relations', 'stability', 'ideology'] as const).map((v) => (
              <button
                key={v}
                onClick={() => setMapView(v)}
                className={`text-xs px-2 py-1 rounded transition-colors ${
                  mapView === v
                    ? 'bg-pax-accent text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {v === 'relations' ? 'Relations' : v === 'stability' ? 'Stability' : 'Ideology'}
              </button>
            ))}
          </div>

          {autoSaved && (
            <div className="flex items-center gap-1 text-xs text-green-400 animate-pulse">
              <Save className="w-3.5 h-3.5" /> Saved
            </div>
          )}

          <button
            onClick={openSnapshots}
            className="btn-secondary p-2"
            title="Save history"
          >
            <History className="w-4 h-4" />
          </button>

          <button
            onClick={() => setShowSettings(true)}
            className="btn-secondary p-2"
            title="API settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <button
            onClick={() => { setLeftPanel('actions'); startSimulation({ label: '1 month', months: 1 }) }}
            disabled={isSimulating}
            className="btn-primary flex items-center gap-2 px-4"
          >
            {isSimulating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Simulating...
              </>
            ) : (
              <>
                Next turn <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main */}
      <div className="flex-1 flex overflow-hidden min-h-0">

        {/* Left panel — Actions + Diplomacy */}
        <div className="w-80 xl:w-96 border-r border-pax-border flex flex-col overflow-hidden shrink-0 min-h-0">
          <div className="flex border-b border-pax-border shrink-0">
            {leftTabs.map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => setLeftPanel(id)}
                title={label}
                className={`flex-1 py-2.5 flex items-center justify-center gap-2 transition-colors text-sm ${
                  leftPanel === id
                    ? 'text-pax-accent border-b-2 border-pax-accent bg-pax-accent/10'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <Icon className="w-4 h-4" />{label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-hidden">
            {leftPanel === 'actions' && (
              <div className="h-full flex flex-col">
                <div className="p-3 border-b border-pax-border shrink-0">
                  <h2 className="font-semibold text-white flex items-center gap-2 text-sm">
                    <Swords className="w-4 h-4 text-pax-accent" /> Government decisions
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">{gameState.player_country.flag} {gameState.player_country.name} · {months[gameState.month - 1]} {gameState.year}</p>
                </div>

                <div className="flex-1 overflow-y-auto min-h-0">
                  {/* Queue */}
                  {(gameState.pending_actions?.length ?? 0) > 0 && (
                    <div className="p-3 space-y-2">
                      <div className="text-xs text-slate-500 font-medium uppercase tracking-wide">Pending decisions</div>
                      {gameState.pending_actions!.map((a, i) => (
                        <div key={i} className="flex items-start gap-2 bg-slate-800 border border-pax-accent/30 rounded-lg p-2.5">
                          <div className="flex-1 text-xs text-white">{a.content}</div>
                          <button onClick={() => removeAction(i)} className="text-slate-500 hover:text-red-400 shrink-0">✕</button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* End-of-turn summary */}
                  {simDone && preSimSnapshot && donePayload && gameState && (() => {
                    const finalStab = Math.round(donePayload.final_stability ?? gameState.player_country.stability)
                    const finalEco = donePayload.final_economy_modifier ?? (gameState.player_country.economy_modifier ?? 1.0)
                    const finalMil = donePayload.final_military_modifier ?? (gameState.player_country.military_modifier ?? 1.0)
                    
                    const stabDelta = finalStab - Math.round(preSimSnapshot.stability)
                    const ecoDelta = (finalEco - preSimSnapshot.economy_modifier) * 100
                    const milDelta = (finalMil - (preSimSnapshot.military_modifier ?? 1.0)) * 100
                    
                    const worldEvents = donePayload.world_event_count ?? simEvents.filter(e => e.type === 'world_event').length
                    const actions = donePayload.action_count ?? simEvents.filter(e => e.type === 'action_result').length
                    const treaties = (gameState.treaties ?? []).filter(t =>
                      t.year > preSimSnapshot.turn || t.year === gameState.year
                    ).length
                    
                    const ns = gameState.player_country.national_stats
                    const idxChanges: string[] = []
                    if (ns && preSimSnapshot) {
                      const keys: { key: keyof typeof ns; label: string }[] = [
                        { key: 'sovereignty', label: 'Sovereignty' },
                        { key: 'food_autonomy', label: 'Food autonomy' },
                        { key: 'energy_autonomy', label: 'Energy autonomy' },
                        { key: 'economic_independence', label: 'Economic independence' },
                        { key: 'security', label: 'Internal security' },
                      ]
                      for (const k of keys) {
                        const pre = preSimSnapshot[k.key] ?? 50
                        const post = ns[k.key] ?? 50
                        const diff = post - pre
                        if (Math.abs(diff) > 0.01) {
                          idxChanges.push(`${k.label}: ${pre.toFixed(0)}% → ${post.toFixed(0)}% (${diff >= 0 ? '+' : ''}${diff.toFixed(0)}%)`)
                        }
                      }
                    }
                    
                    return (
                      <div className="mx-3 mt-3 mb-1 rounded-lg border border-pax-accent/40 bg-pax-accent/5 p-3">
                        <div className="text-xs font-semibold text-pax-accent mb-2 flex items-center gap-1.5">
                          ✅ Turn complete
                        </div>
                        <div className="grid grid-cols-3 gap-2 mb-2">
                          <div>
                            <div className="text-xs text-slate-400">Stability</div>
                            <div className={`text-sm font-bold ${stabDelta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {Math.round(preSimSnapshot.stability)} → {finalStab}
                              <span className="text-xs font-normal ml-1">({stabDelta >= 0 ? '+' : ''}{stabDelta})</span>
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-slate-400">Economy</div>
                            <div className={`text-sm font-bold ${ecoDelta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {ecoDelta >= 0 ? '+' : ''}{ecoDelta.toFixed(1)}%
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-slate-400">Military</div>
                            <div className={`text-sm font-bold ${milDelta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {milDelta >= 0 ? '+' : ''}{milDelta.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                        {idxChanges.length > 0 && (
                          <div className="text-[11px] border-t border-pax-border/30 pt-1.5 mt-1.5 mb-2 space-y-0.5">
                            <div className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">Strategic Indices Updates</div>
                            {idxChanges.map((change, idx) => (
                              <div key={idx} className="text-slate-300">📈 {change}</div>
                            ))}
                          </div>
                        )}
                        {(() => {
                          const preEq = preSimSnapshot.equipment || {}
                          const postEq = gameState.player_country.military?.equipment || {}
                          const eqChanges: string[] = []
                          
                          const equipmentLabels: Record<string, { label: string; icon: string }> = {
                            chars_combat: { label: 'Battle tanks', icon: '🛡️' },
                            avions_chasse: { label: 'Fighter jets', icon: '✈️' },
                            navires_guerre: { label: 'Warships', icon: '⚓' },
                            sous_marins: { label: 'Submarines', icon: '🌊' },
                            helicopteres: { label: 'Military helicopters', icon: '🚁' },
                            artillerie: { label: 'Artillery pieces', icon: '💣' },
                            drones: { label: 'Military drones', icon: '🛸' },
                          }
                          
                          const allKeys = Array.from(new Set([...Object.keys(preEq), ...Object.keys(postEq)]))
                          for (const k of allKeys) {
                            const preVal = preEq[k] ?? 0
                            const postVal = postEq[k] ?? 0
                            const diff = postVal - preVal
                            if (diff !== 0) {
                              const meta = equipmentLabels[k]
                              const labelName = meta ? `${meta.icon} ${meta.label}` : k.replace(/_/g, ' ')
                              eqChanges.push(`${labelName}: ${preVal.toLocaleString()} → ${postVal.toLocaleString()} (${diff >= 0 ? '+' : ''}${diff.toLocaleString()})`)
                            }
                          }
                          
                          if (eqChanges.length === 0) return null
                          
                          return (
                            <div className="text-[11px] border-t border-pax-border/30 pt-1.5 mt-1.5 mb-2 space-y-0.5">
                              <div className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">Arsenal Updates</div>
                              {eqChanges.map((change, idx) => (
                                <div key={idx} className="text-slate-300">{change}</div>
                              ))}
                            </div>
                          )
                        })()}
                        <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-slate-400 mb-2">
                          <span>🌍 {worldEvents} events</span>
                          <span>⚡ {actions} actions</span>
                          {treaties > 0 && <span>🤝 {treaties} treaties</span>}
                        </div>
                        <button
                          onClick={startSummary}
                          disabled={isSummarizing}
                          className="w-full btn-secondary text-xs py-1.5 flex items-center justify-center gap-1.5"
                        >
                          {isSummarizing ? <Loader2 className="w-3 h-3 animate-spin" /> : <FileText className="w-3 h-3" />}
                          {isSummarizing ? 'Generating summary…' : 'AI narrative summary'}
                        </button>
                        {summaryText && (
                          <div className="mt-2 text-xs text-slate-300 bg-slate-800 rounded-lg p-2.5 prose prose-invert prose-xs max-w-none border border-pax-border">
                            <ReactMarkdown>{summaryText}</ReactMarkdown>
                          </div>
                        )}
                      </div>
                    )
                  })()}

                  {/* Simulation timeline */}
                  {simEvents.length > 0 && (
                    <div className="p-3 space-y-2 border-t border-pax-border">
                      <div className="text-xs text-slate-500 font-medium uppercase tracking-wide">Simulation log</div>
                      {simEvents.map((e, i) => (
                        <div key={i} className={`rounded-lg p-2.5 text-xs ${
                          (e.type === 'month_start' || e.type === 'week_start') ? 'bg-pax-accent/10 border border-pax-accent/30 text-pax-accent font-semibold' :
                          e.type === 'action_result' ? 'bg-slate-800 border border-pax-gold/30' :
                          e.type === 'world_event' ? 'bg-slate-800 border border-pax-border' :
                          e.type === 'domestic_event' ? `bg-slate-800 border ${
                            (e.severity ?? 1) >= 3 ? 'border-red-700/60' :
                            (e.severity ?? 1) === 2 ? 'border-orange-700/60' :
                            'border-yellow-700/40'
                          }` :
                          e.type === 'poi_added' ? 'bg-pax-accent/5 border border-pax-accent/20' :
                          'bg-red-900/20 border border-red-700 text-red-300'
                        }`}>
                          {(e.type === 'month_start' || e.type === 'week_start') && (
                            e.type === 'week_start'
                              ? `📅 Week — ${months[(e.month ?? 1) - 1]} ${e.year} (day ${e.day ?? 1}) — Turn ${e.turn}`
                              : `📅 ${months[(e.month ?? 1) - 1]} ${e.year} — Turn ${e.turn}`
                          )}
                          {e.type === 'world_event' && (
                            <div>
                              <div className="flex items-start justify-between gap-2">
                                <div className="text-slate-300 font-medium">
                                  {e.event_type === 'diplomatic' ? '🤝' :
                                   e.event_type === 'economic' ? '📈' :
                                   e.event_type === 'military' ? '⚔️' :
                                   e.event_type === 'humanitarian' ? '🏥' :
                                   e.event_type === 'political' ? '🏛️' :
                                   e.event_type === 'natural' ? '🌪️' :
                                   e.event_type === 'reaction' ? '💬' :
                                   e.event_type === 'consequence' ? '⏳' : '🌍'
                                  } {e.title}
                                </div>
                                <button
                                  onClick={() => setAction(`React to: ${e.title} — `)}
                                  className="shrink-0 text-pax-accent/70 hover:text-pax-accent transition-colors"
                                  title="Intervene in this event"
                                >
                                  <MessageSquarePlus className="w-3.5 h-3.5" />
                                </button>
                              </div>
                              <div className="text-slate-400 mt-0.5">{e.description}</div>
                            </div>
                          )}
                          {e.type === 'action_result' && (
                            <>
                              <div className="text-pax-gold font-medium">⚡ {e.action}</div>
                              <div className="text-slate-300 mt-0.5 prose prose-invert prose-xs max-w-none">
                                <ReactMarkdown>{e.narrative ?? ''}</ReactMarkdown>
                              </div>
                              <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs">
                                {(e.stability_delta ?? 0) !== 0 && (
                                  <span className={`font-semibold ${(e.stability_delta ?? 0) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    Stability: {(e.stability_delta ?? 0) > 0 ? '+' : ''}{e.stability_delta}
                                  </span>
                                )}
                                {(e.economy_delta ?? 0) !== 0 && (
                                  <span className={`font-semibold ${(e.economy_delta ?? 0) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    Economy: {(e.economy_delta ?? 0) > 0 ? '+' : ''}{(e.economy_delta! * 100).toFixed(1)}%
                                  </span>
                                )}
                                {(e.military_delta ?? 0) !== 0 && (
                                  <span className={`font-semibold ${(e.military_delta ?? 0) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    Military: {(e.military_delta ?? 0) > 0 ? '+' : ''}{(e.military_delta! * 100).toFixed(1)}%
                                  </span>
                                )}
                              </div>
                              {e.stat_deltas && Object.values(e.stat_deltas).some(v => v !== 0) && (() => {
                                const labels: Record<string, string> = {
                                  sovereignty: 'Sovereignty',
                                  food_autonomy: 'Food autonomy',
                                  energy_autonomy: 'Energy autonomy',
                                  economic_independence: 'Economic independence',
                                  security: 'Internal security',
                                }
                                return (
                                  <div className="mt-1.5 flex flex-wrap gap-x-2 gap-y-0.5 text-[11px] text-slate-400 bg-slate-900/40 rounded px-2 py-1 border border-pax-border/30">
                                    {Object.entries(e.stat_deltas).filter(([, v]) => v !== 0).map(([k, v]) => (
                                      <span key={k}>
                                        {labels[k] ?? k}: <strong className={v > 0 ? 'text-green-400' : 'text-red-400'}>{v > 0 ? '+' : ''}{v}%</strong>
                                      </span>
                                    ))}
                                  </div>
                                )
                              })()}
                              {e.equipment_changes && Object.values(e.equipment_changes).some(v => v !== 0) && (() => {
                                const labels: Record<string, { label: string; icon: string }> = {
                                  chars_combat: { label: 'Battle tanks', icon: '🛡️' },
                                  avions_chasse: { label: 'Fighter jets', icon: '✈️' },
                                  navires_guerre: { label: 'Warships', icon: '⚓' },
                                  sous_marins: { label: 'Submarines', icon: '🌊' },
                                  helicopteres: { label: 'Military helicopters', icon: '🚁' },
                                  artillerie: { label: 'Artillery pieces', icon: '💣' },
                                  drones: { label: 'Military drones', icon: '🛸' },
                                }
                                return (
                                  <div className="mt-1.5 flex flex-wrap gap-x-2 gap-y-0.5 text-[11px] text-slate-400 bg-slate-900/40 rounded px-2 py-1 border border-pax-border/30">
                                    {Object.entries(e.equipment_changes).filter(([, v]) => v !== 0).map(([k, v]) => {
                                      const meta = labels[k]
                                      const displayName = meta ? `${meta.icon} ${meta.label}` : k.replace(/_/g, ' ')
                                      return (
                                        <span key={k}>
                                          {displayName}: <strong className={v > 0 ? 'text-green-400' : 'text-red-400'}>{v > 0 ? '+' : ''}{v.toLocaleString()}</strong>
                                        </span>
                                      )
                                    })}
                                  </div>
                                )
                              })()}
                            </>
                          )}
                          {e.type === 'domestic_event' && (
                            <>
                              <div className={`font-medium ${
                                (e.severity ?? 1) >= 3 ? 'text-red-400' :
                                (e.severity ?? 1) === 2 ? 'text-orange-400' :
                                'text-yellow-400'
                              }`}>
                                {e.event_type === 'protest' ? '✊' :
                                 e.event_type === 'rally' ? '🎉' :
                                 e.event_type === 'scandal' ? '📰' :
                                 e.event_type === 'economic' ? '📈' :
                                 e.event_type === 'military' ? '🪖' :
                                 e.event_type === 'infrastructure' ? '🏗️' :
                                 e.event_type === 'cultural' ? '🎭' : '🔔'
                                } {e.title}
                              </div>
                              <div className="text-slate-400 mt-0.5">{e.description}</div>
                              {(e.stability_impact ?? 0) !== 0 && (
                                <div className={`mt-1 font-medium text-xs ${(e.stability_impact ?? 0) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                  Stability impact: {(e.stability_impact ?? 0) > 0 ? '+' : ''}{e.stability_impact}
                                </div>
                              )}
                            </>
                          )}
                          {e.type === 'poi_added' && (
                            <div className="text-pax-accent">
                              {e.poi_icon} <span className="font-medium">{e.poi_name}</span>
                              <span className="text-slate-400"> — added to the map</span>
                            </div>
                          )}
                          {e.type === 'error' && `⚠️ ${e.message}`}
                        </div>
                      ))}
                      <div ref={simBottomRef} />
                    </div>
                  )}

                  {simEvents.length === 0 && (gameState.pending_actions?.length ?? 0) === 0 && (
                    <div className="p-6 text-center text-slate-500 text-xs">
                      Plan your government decisions, then launch the simulation.
                    </div>
                  )}
                </div>

                {/* Stability warning */}
                {gameState.player_country.stability < 20 && !isSimulating && (
                  <div className="mx-3 mb-1 rounded-lg border border-red-700/60 bg-red-900/20 px-3 py-2 flex items-center gap-2 text-xs text-red-300">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    <span><strong>Critical stability ({gameState.player_country.stability}/100).</strong> Risk of coup. Prioritize order.</span>
                  </div>
                )}

                {/* Input */}
                <div className="p-3 border-t border-pax-border shrink-0 space-y-2">
                  <div className="flex gap-2">
                    <textarea
                      ref={actionRef}
                      value={action}
                      onChange={(e) => setAction(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); queueAction() } }}
                      placeholder={`e.g. "Sign a trade deal with Germany", "Increase military budget"...`}
                      rows={2}
                      disabled={isSimulating}
                      className={`flex-1 bg-slate-800 border rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none focus:outline-none ${
                        gameState.player_country.stability < 20
                          ? 'border-red-700/50 focus:border-red-500'
                          : 'border-pax-border focus:border-pax-accent'
                      } disabled:opacity-50`}
                    />
                    <button
                      onClick={queueAction}
                      disabled={!action.trim() || isSimulating}
                      className="btn-secondary self-end px-2 py-2 disabled:opacity-40"
                      title="Add to queue"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Simulate buttons */}
                  {!isSimulating && (
                    <div className="grid grid-cols-5 gap-1">
                      {SIM_DURATIONS.map((d) => (
                        <button
                          key={d.label}
                          onClick={() => startSimulation(d)}
                          className="btn-primary text-xs py-1.5 px-1 text-center leading-tight"
                          title={`Simulate ${d.label}`}
                        >
                          {d.label}
                        </button>
                      ))}
                    </div>
                  )}
                  {isSimulating && (
                    <button
                      onClick={pauseSimulation}
                      className="w-full btn-secondary text-xs py-1.5 flex items-center justify-center gap-2 border-red-700 text-red-400 hover:text-red-300"
                    >
                      <Loader2 className="w-3 h-3 animate-spin" /> Simulation running — Stop
                    </button>
                  )}
                </div>
              </div>
            )}

            {leftPanel === 'diplomacy' && (
              <DiplomacyPanel
                gameState={gameState}
                targetCountry={diplomacyTarget}
                onSelectTarget={(c) => setDiplomacyTarget(c)}
              />
            )}
          </div>
        </div>

        {/* Map */}
        <div className="flex-1 flex flex-col overflow-hidden min-h-0">
          <div className="flex-1 relative min-h-0">
            <WorldMap
              countries={gameState.countries}
              playerCountryId={gameState.player_country.id}
              selectedCountryId={selectedCountry?.id}
              onSelectCountry={handleCountryClick}
              viewMode={mapView}
              pois={[...(gameState.map_pois ?? []), ...streamingPois]}
              regionState={gameState.region_state}
              customMapUrl={gameState.custom_map_id ? `/api/maps/${gameState.custom_map_id}` : undefined}
              featureIdProp={gameState.custom_map_feature_id_property}
              initialTerritories={gameState.initial_territories}
            />
          </div>
        </div>

        {/* Right panel — Advisor + Stats + News */}
        <div className="w-80 xl:w-96 border-l border-pax-border flex flex-col overflow-hidden shrink-0 min-h-0">
          <div className="flex border-b border-pax-border shrink-0">
            {rightTabs.map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => setRightPanel(id)}
                title={label}
                className={`flex-1 py-2.5 flex items-center justify-center gap-2 transition-colors text-sm ${
                  rightPanel === id
                    ? 'text-pax-accent border-b-2 border-pax-accent bg-pax-accent/10'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <Icon className="w-4 h-4" />{label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-hidden">
            {rightPanel === 'advisor' && (
              <AdvisorPanel gameState={gameState} />
            )}

            {rightPanel === 'dashboard' && (
              <div className="h-full overflow-y-auto">
                {selectedCountry && selectedCountry.id !== gameState.player_country.id && (
                  <div className="px-4 pt-3 flex items-center gap-2">
                    <button onClick={() => setSelectedCountry(null)} className="text-xs text-slate-400 hover:text-white">
                      ← My country
                    </button>
                    <ChevronRight className="w-3 h-3 text-slate-600" />
                    <span className="text-xs text-white">{selectedCountry.flag} {selectedCountry.name}</span>
                    <button
                      onClick={() => handleDiplomacyTarget(selectedCountry)}
                      className="ml-auto text-xs btn-secondary py-1 px-2 flex items-center gap-1"
                    >
                      <Globe className="w-3 h-3" /> Diplomacy
                    </button>
                  </div>
                )}
                <CountryDashboard
                  country={displayCountry}
                  isPlayer={!selectedCountry || selectedCountry.id === gameState.player_country.id}
                  playerCountry={gameState.player_country}
                  statHistory={(!selectedCountry || selectedCountry.id === gameState.player_country.id) ? statHistory : undefined}
                  treaties={gameState.treaties}
                  diplomaticHistory={selectedCountry && selectedCountry.id !== gameState.player_country.id
                    ? gameState.diplomatic_history.filter(m =>
                        (m.from_country === gameState.player_country.id && m.to_country === selectedCountry.id) ||
                        (m.from_country === selectedCountry.id && m.to_country === gameState.player_country.id)
                      )
                    : undefined}
                />
              </div>
            )}

            {rightPanel === 'events' && (
              <EventsFeed events={gameState.recent_events} />
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
