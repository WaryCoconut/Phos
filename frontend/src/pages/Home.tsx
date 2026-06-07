import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Globe, ChevronRight, Clock, Map, Loader2, Settings, PlayCircle, Trash2, RotateCcw } from 'lucide-react'
import { scenariosApi, gameApi } from '@/api/client'
import { useSettingsStore } from '@/store/settingsStore'
import SettingsModal from '@/components/UI/SettingsModal'
import type { ScenarioSummary } from '@/types'

interface CountryBasic {
  id: string
  name: string
  flag: string
  continent: string
}

interface SavedSession {
  id: string
  scenario_id: string
  scenario_name: string
  player_country_id: string
  player_country_name: string
  player_country_flag: string
  year: number
  month: number
  turn: number
  created_at: string
  updated_at: string
}

const months = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

export default function Home() {
  const navigate = useNavigate()
  const { isConfigured } = useSettingsStore()
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([])
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null)
  const [countries, setCountries] = useState<CountryBasic[]>([])
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [savedSessions, setSavedSessions] = useState<SavedSession[]>([])
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    if (!isConfigured()) setShowSettings(true)
  }, [])

  useEffect(() => {
    scenariosApi.list().then((data) => {
      setScenarios(data)
      if (data.length > 0) setSelectedScenario(data[0].id)
      setIsLoading(false)
    }).catch(() => {
      setError('Cannot reach the backend. Make sure the FastAPI server is running on port 8000.')
      setIsLoading(false)
    })
    loadSessions()
  }, [])

  useEffect(() => {
    if (!selectedScenario) return
    scenariosApi.get(selectedScenario).then((data) => {
      const cs = Object.values(data.countries as Record<string, CountryBasic>)
        .map((c) => ({ id: c.id, name: c.name, flag: c.flag, continent: c.continent }))
        .sort((a, b) => a.name.localeCompare(b.name))
      setCountries(cs)
    })
  }, [selectedScenario])

  function loadSessions() {
    gameApi.listSessions().then(setSavedSessions).catch(() => {})
  }

  async function startGame() {
    if (!selectedScenario || !selectedCountry) return
    if (!isConfigured()) {
      setShowSettings(true)
      return
    }
    setIsStarting(true)
    try {
      const { session_id } = await gameApi.create(selectedScenario, selectedCountry)
      navigate(`/game/${session_id}`)
    } catch {
      setError('Could not create the game. Check the backend and your API key.')
      setIsStarting(false)
    }
  }

  async function deleteSession(id: string) {
    setDeletingId(id)
    try {
      await gameApi.deleteSession(id)
      setSavedSessions((prev) => prev.filter((s) => s.id !== id))
    } catch {
      // ignore
    } finally {
      setDeletingId(null)
    }
  }

  const filteredCountries = countries.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.continent.toLowerCase().includes(search.toLowerCase())
  )
  const continents = [...new Set(filteredCountries.map((c) => c.continent))].sort()

  return (
    <div className="min-h-screen bg-pax-dark flex flex-col">
      <SettingsModal
        open={showSettings}
        onClose={() => setShowSettings(false)}
        required={!isConfigured()}
      />

      {/* Header */}
      <div className="border-b border-pax-border bg-pax-panel">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center gap-4">
          <Globe className="w-8 h-8 text-pax-accent" />
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-white">Phos</h1>
            <p className="text-sm text-slate-400">AI-powered geopolitical narrative simulation</p>
          </div>
          <button
            onClick={() => setShowSettings(true)}
            className="btn-secondary flex items-center gap-2"
            title="API settings"
          >
            <Settings className="w-4 h-4" />
            {isConfigured() ? 'API configured' : 'Configure API'}
          </button>
        </div>
      </div>

      {error && (
        <div className="max-w-5xl mx-auto px-6 mt-4">
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-300 text-sm">
            {error}
          </div>
        </div>
      )}

      <div className="max-w-5xl mx-auto px-6 py-8 flex-1 w-full">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-pax-accent animate-spin" />
          </div>
        ) : (
          <>
            {/* Saved sessions */}
            {savedSessions.length > 0 && (
              <div className="mb-10">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <RotateCcw className="w-5 h-5 text-pax-accent" /> Continue a game
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {savedSessions.map((s) => (
                    <div
                      key={s.id}
                      className="panel p-4 flex flex-col gap-3 hover:border-slate-600 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-3xl">{s.player_country_flag || '🏳️'}</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-semibold text-white truncate">{s.player_country_name}</div>
                          <div className="text-xs text-slate-500 truncate">{s.scenario_name}</div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-pax-gold text-sm font-bold">
                            {months[s.month - 1]} {s.year}
                          </div>
                          <div className="text-xs text-slate-500">Turn {s.turn}</div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => navigate(`/game/${s.id}`)}
                          className="flex-1 btn-primary flex items-center justify-center gap-1.5 text-xs py-1.5"
                        >
                          <PlayCircle className="w-3.5 h-3.5" /> Resume
                        </button>
                        <button
                          onClick={() => deleteSession(s.id)}
                          disabled={deletingId === s.id}
                          className="btn-secondary px-2 py-1.5 text-xs text-red-400 hover:text-red-300 hover:border-red-800 disabled:opacity-50"
                          title="Delete this save"
                        >
                          {deletingId === s.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* New game */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Scenario selection */}
              <div>
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-pax-accent" /> Choose a scenario
                </h2>
                <div className="space-y-3">
                  {scenarios.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setSelectedScenario(s.id)}
                      className={`w-full text-left panel p-4 transition-all hover:border-pax-accent ${
                        selectedScenario === s.id ? 'border-pax-accent bg-pax-accent/10' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-semibold text-white">{s.name}</div>
                          <div className="text-sm text-slate-400 mt-0.5">{s.description}</div>
                        </div>
                        <div className="text-right shrink-0 ml-4">
                          <div className="text-pax-gold font-bold">{s.start_year}</div>
                          <div className="text-xs text-slate-500">{s.country_count} countries</div>
                        </div>
                      </div>
                      {s.custom && (
                        <span className="text-xs bg-pax-accent/20 text-pax-accent px-2 py-0.5 rounded-full mt-2 inline-block">
                          Custom
                        </span>
                      )}
                    </button>
                  ))}
                  <button
                    onClick={() => navigate('/scenario-editor')}
                    className="w-full text-left panel p-4 border-dashed hover:border-pax-accent transition-all"
                  >
                    <div className="flex items-center gap-2 text-slate-400 hover:text-white">
                      <Map className="w-4 h-4" />
                      <span className="text-sm">Create a custom scenario</span>
                    </div>
                  </button>
                </div>
              </div>

              {/* Country selection */}
              <div>
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-pax-accent" /> Choose your country
                </h2>
                <input
                  type="text"
                  placeholder="Search a country..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-pax-panel border border-pax-border rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent mb-3"
                />
                <div className="panel overflow-y-auto" style={{ maxHeight: '380px' }}>
                  {continents.map((continent) => (
                    <div key={continent}>
                      <div className="sticky top-0 bg-pax-panel px-3 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-pax-border">
                        {continent}
                      </div>
                      {filteredCountries
                        .filter((c) => c.continent === continent)
                        .map((c) => (
                          <button
                            key={c.id}
                            onClick={() => setSelectedCountry(c.id)}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 hover:bg-slate-700 transition-colors text-left ${
                              selectedCountry === c.id ? 'bg-pax-accent/20' : ''
                            }`}
                          >
                            <span className="text-xl">{c.flag || '🏳️'}</span>
                            <span className={`text-sm ${selectedCountry === c.id ? 'text-pax-accent font-medium' : 'text-white'}`}>
                              {c.name}
                            </span>
                            {selectedCountry === c.id && (
                              <ChevronRight className="w-4 h-4 text-pax-accent ml-auto" />
                            )}
                          </button>
                        ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-center">
              <button
                onClick={startGame}
                disabled={!selectedScenario || !selectedCountry || isStarting}
                className="btn-primary flex items-center gap-3 px-8 py-3 text-base font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isStarting ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Creating game...</>
                ) : (
                  <><Globe className="w-5 h-5" /> Start game</>
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
