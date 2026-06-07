import { useState, useEffect } from 'react'
import { Map, Flag, Shield, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import type { GameState, RegionMeta } from '@/types'
import { regionsApi } from '@/api/client'
import { useGameStore } from '@/store/gameStore'

const SUPPORTED_IDS = ['USA', 'RUS', 'CHN', 'IND', 'BRA', 'AUS', 'CAN', 'IDN', 'ZAF']

interface Props {
  gameState: GameState
}

type RegionStatus = 'free' | 'occupied' | 'independent'

interface ActionState {
  type: 'occupy' | 'independence' | null
  adm1Code: string | null
  inputValue: string
}

export default function RegionPanel({ gameState }: Props) {
  const { sessionId, refreshState } = useGameStore()
  const [selectedCountryId, setSelectedCountryId] = useState<string>(SUPPORTED_IDS[0])
  const [regionsMeta, setRegionsMeta] = useState<RegionMeta[]>([])
  const [loading, setLoading] = useState(false)
  const [action, setAction] = useState<ActionState>({ type: null, adm1Code: null, inputValue: '' })

  const regionState = gameState.region_state ?? { occupied: {}, independent: {} }

  const supportedCountries = SUPPORTED_IDS.filter((id) => gameState.countries[id])

  useEffect(() => {
    if (!selectedCountryId) return
    regionsApi.getCountryMeta(selectedCountryId).then(setRegionsMeta).catch(() => setRegionsMeta([]))
  }, [selectedCountryId])

  function getStatus(adm1Code: string): RegionStatus {
    if (regionState.occupied[adm1Code]) return 'occupied'
    if (regionState.independent[adm1Code]) return 'independent'
    return 'free'
  }

  async function handleOccupy(adm1Code: string) {
    if (!sessionId || !action.inputValue.trim()) return
    setLoading(true)
    try {
      await regionsApi.occupy(sessionId, adm1Code, action.inputValue.trim())
      await refreshState()
      setAction({ type: null, adm1Code: null, inputValue: '' })
    } finally {
      setLoading(false)
    }
  }

  async function handleLiberate(adm1Code: string) {
    if (!sessionId) return
    setLoading(true)
    try {
      await regionsApi.liberate(sessionId, adm1Code)
      await refreshState()
    } finally {
      setLoading(false)
    }
  }

  async function handleIndependence(adm1Code: string) {
    if (!sessionId || !action.inputValue.trim()) return
    setLoading(true)
    try {
      await regionsApi.declareIndependence(sessionId, adm1Code, action.inputValue.trim())
      await refreshState()
      setAction({ type: null, adm1Code: null, inputValue: '' })
    } finally {
      setLoading(false)
    }
  }

  async function handleReunify(adm1Code: string) {
    if (!sessionId) return
    setLoading(true)
    try {
      await regionsApi.reunify(sessionId, adm1Code)
      await refreshState()
    } finally {
      setLoading(false)
    }
  }

  const selectedCountry = gameState.countries[selectedCountryId]

  const atWarCountries = Object.entries(gameState.countries)
    .filter(([, c]) => c.at_war_with?.length > 0)
    .map(([id]) => id)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-pax-border shrink-0">
        <h2 className="font-semibold text-white flex items-center gap-2 text-sm">
          <Map className="w-4 h-4 text-pax-accent" /> Regions &amp; Occupation
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">Region control for the 9 major powers</p>
      </div>

      {/* War alert */}
      {atWarCountries.length > 0 && (
        <div className="mx-3 mt-2 bg-red-900/20 border border-red-800/50 rounded-lg px-3 py-2 text-xs text-red-300 shrink-0">
          ⚔️ Active conflicts: {atWarCountries.map((id) => gameState.countries[id]?.flag + ' ' + gameState.countries[id]?.name).join(', ')}
          <div className="text-red-400/70 mt-0.5">Regions can be automatically captured during simulation.</div>
        </div>
      )}

      {/* Country tabs */}
      <div className="flex overflow-x-auto border-b border-pax-border shrink-0 px-2 pt-2 gap-1">
        {supportedCountries.map((id) => {
          const c = gameState.countries[id]
          const occCount = Object.values(regionState.occupied).filter((r) => r.country_id === id || r.occupied_by === id).length
          const indCount = Object.values(regionState.independent).filter((r) => r.parent_id === id).length
          return (
            <button
              key={id}
              onClick={() => { setSelectedCountryId(id); setAction({ type: null, adm1Code: null, inputValue: '' }) }}
              className={clsx(
                'flex items-center gap-1 px-2 py-1.5 rounded-t text-xs shrink-0 transition-colors relative',
                selectedCountryId === id
                  ? 'bg-pax-accent/15 text-white border-b-2 border-pax-accent'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              <span>{c?.flag}</span>
              <span className="hidden sm:inline">{c?.name}</span>
              {(occCount > 0 || indCount > 0) && (
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 absolute top-1 right-1" />
              )}
            </button>
          )
        })}
      </div>

      {/* Region list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {regionsMeta.length === 0 && (
          <div className="text-xs text-slate-500 text-center py-8">Loading regions…</div>
        )}
        {regionsMeta.map((region) => {
          const status = getStatus(region.adm1_code)
          const occ = regionState.occupied[region.adm1_code]
          const ind = regionState.independent[region.adm1_code]
          const isExpanded = action.adm1Code === region.adm1_code

          return (
            <div
              key={region.adm1_code}
              className={clsx(
                'rounded-lg border text-xs transition-colors',
                status === 'occupied' ? 'border-red-800/50 bg-red-950/20' :
                status === 'independent' ? 'border-purple-800/50 bg-purple-950/20' :
                'border-pax-border bg-slate-800/30'
              )}
            >
              <div className="flex items-center gap-2 px-2.5 py-2">
                <div className="flex-1 min-w-0">
                  <div className="text-white font-medium truncate">
                    {region.name}
                  </div>
                  {status === 'occupied' && occ && (
                    <div className="text-red-300 mt-0.5">
                      Occupied by {gameState.countries[occ.occupied_by]?.flag} {gameState.countries[occ.occupied_by]?.name ?? occ.occupied_by}
                    </div>
                  )}
                  {status === 'independent' && ind && (
                    <div className="text-purple-300 mt-0.5">
                      {gameState.countries[ind.country_id]?.flag} {gameState.countries[ind.country_id]?.name ?? ind.country_id} (since {ind.since_year})
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  {status === 'free' && (
                    <>
                      <button
                        onClick={() => setAction({ type: 'occupy', adm1Code: region.adm1_code, inputValue: '' })}
                        className="btn-secondary py-0.5 px-1.5 text-xs flex items-center gap-1"
                        title="Occupy this region"
                      >
                        <Shield className="w-3 h-3" /> Occupy
                      </button>
                      <button
                        onClick={() => setAction({ type: 'independence', adm1Code: region.adm1_code, inputValue: '' })}
                        className="btn-secondary py-0.5 px-1.5 text-xs flex items-center gap-1"
                        title="Declare independence"
                      >
                        <Flag className="w-3 h-3" /> Indep.
                      </button>
                    </>
                  )}
                  {status === 'occupied' && (
                    <button
                      onClick={() => handleLiberate(region.adm1_code)}
                      disabled={loading}
                      className="btn-secondary py-0.5 px-1.5 text-xs text-green-400 hover:text-green-300"
                    >
                      Liberate
                    </button>
                  )}
                  {status === 'independent' && (
                    <button
                      onClick={() => handleReunify(region.adm1_code)}
                      disabled={loading}
                      className="btn-secondary py-0.5 px-1.5 text-xs text-orange-400 hover:text-orange-300"
                    >
                      Reunify
                    </button>
                  )}
                </div>
              </div>

              {/* Inline action form */}
              {isExpanded && action.type === 'occupy' && (
                <div className="px-2.5 pb-2 space-y-1.5">
                  <input
                    type="text"
                    value={action.inputValue}
                    onChange={(e) => setAction((a) => ({ ...a, inputValue: e.target.value }))}
                    placeholder="Occupying country ID (e.g. CHN, USA…)"
                    className="w-full bg-slate-800 border border-pax-border rounded px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
                    list="country-ids-list"
                    autoFocus
                  />
                  <datalist id="country-ids-list">
                    {Object.keys(gameState.countries).map((id) => (
                      <option key={id} value={id}>{gameState.countries[id]?.name}</option>
                    ))}
                  </datalist>
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleOccupy(region.adm1_code)}
                      disabled={loading || !action.inputValue.trim()}
                      className="btn-primary py-0.5 px-2 text-xs flex items-center gap-1 disabled:opacity-40"
                    >
                      {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Shield className="w-3 h-3" />}
                      Confirm
                    </button>
                    <button
                      onClick={() => setAction({ type: null, adm1Code: null, inputValue: '' })}
                      className="btn-secondary py-0.5 px-2 text-xs"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {isExpanded && action.type === 'independence' && (
                <div className="px-2.5 pb-2 space-y-1.5">
                  <input
                    type="text"
                    value={action.inputValue}
                    onChange={(e) => setAction((a) => ({ ...a, inputValue: e.target.value }))}
                    placeholder="New state name (e.g. Republic of Siberia)"
                    className="w-full bg-slate-800 border border-pax-border rounded px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
                    autoFocus
                  />
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleIndependence(region.adm1_code)}
                      disabled={loading || !action.inputValue.trim()}
                      className="btn-primary py-0.5 px-2 text-xs flex items-center gap-1 disabled:opacity-40"
                    >
                      {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Flag className="w-3 h-3" />}
                      Declare
                    </button>
                    <button
                      onClick={() => setAction({ type: null, adm1Code: null, inputValue: '' })}
                      className="btn-secondary py-0.5 px-2 text-xs"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer info */}
      <div className="p-2 border-t border-pax-border text-xs text-slate-500 shrink-0">
        {selectedCountry && (
          <span>{selectedCountry.flag} {selectedCountry.name} — {regionsMeta.length} regions
            {' · '}
            {Object.values(regionState.occupied).filter((r) => r.country_id === selectedCountryId).length} occupied
            {' · '}
            {Object.values(regionState.independent).filter((r) => r.parent_id === selectedCountryId).length} independent
          </span>
        )}
      </div>
    </div>
  )
}
