import { Shield, TrendingUp, Users, Swords, AlertTriangle, Globe, Wheat, Zap, Building2, Flag, Handshake, MessageSquare } from 'lucide-react'
import type { Country, CountryNationalStats, StatSnapshot, Treaty, DiplomaticMessage } from '@/types'

interface Props {
  country: Country
  isPlayer?: boolean
  playerCountry?: Country
  statHistory?: StatSnapshot[]
  treaties?: Treaty[]
  diplomaticHistory?: DiplomaticMessage[]
}

function Sparkline({ data, color = '#3b82f6' }: { data: number[]; color?: string }) {
  if (data.length < 2) return null
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const W = 56, H = 18
  const pts = data
    .map((v, i) => `${(i / (data.length - 1)) * W},${H - ((v - min) / range) * H}`)
    .join(' ')
  return (
    <svg width={W} height={H} style={{ overflow: 'visible', flexShrink: 0 }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function StatBlock({
  icon: Icon,
  label,
  value,
  sub,
  color = 'text-white',
}: {
  icon: React.ElementType
  label: string
  value: string
  sub?: string
  color?: string
}) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-slate-400" />
        <span className="stat-label">{label}</span>
      </div>
      <div className={`stat-value ${color}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  )
}

function RelationBadge({ score }: { score: number }) {
  if (score >= 60) return <span className="text-green-400 text-xs font-medium">Ally</span>
  if (score >= 20) return <span className="text-green-600 text-xs font-medium">Friend</span>
  if (score >= -20) return <span className="text-slate-400 text-xs font-medium">Neutral</span>
  if (score >= -60) return <span className="text-orange-400 text-xs font-medium">Hostile</span>
  return <span className="text-red-400 text-xs font-medium">Enemy</span>
}

function StabilityBar({ value }: { value: number }) {
  const color = value >= 70 ? 'bg-green-500' : value >= 40 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="w-full bg-slate-700 rounded-full h-1.5 mt-1">
      <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${value}%` }} />
    </div>
  )
}

function PercentBar({
  label,
  value,
  max = 100,
  color,
  icon: Icon,
}: {
  label: string
  value: number
  max?: number
  color: string
  icon: React.ElementType
}) {
  const pct = Math.min(100, (value / max) * 100)
  const displayValue = `${value.toFixed(0)}%`
  const tooHigh = value > 100
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-slate-300">
          <Icon className="w-3.5 h-3.5 text-slate-400" />
          <span>{label}</span>
        </div>
        <span className={tooHigh ? 'text-green-300 font-semibold' : 'text-slate-200 font-medium'}>
          {displayValue}
        </span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function SectorsChart({ sectors }: { sectors: Record<string, number> }) {
  const SECTOR_COLORS: Record<string, string> = {
    agriculture: 'bg-green-500',
    industrie: 'bg-blue-500',
    services: 'bg-purple-500',
    energie: 'bg-yellow-500',
    finance: 'bg-cyan-500',
  }
  const SECTOR_LABELS: Record<string, string> = {
    agriculture: 'Agriculture',
    industrie: 'Industry',
    services: 'Services',
    energie: 'Energy',
    finance: 'Finance',
  }
  const entries = Object.entries(sectors).filter(([, v]) => v > 0)
  const total = entries.reduce((s, [, v]) => s + v, 0)

  return (
    <div className="space-y-2">
      <div className="flex h-5 rounded-md overflow-hidden gap-px">
        {entries.map(([key, val]) => (
          <div
            key={key}
            className={`${SECTOR_COLORS[key] ?? 'bg-slate-500'} transition-all`}
            style={{ width: `${(val / total) * 100}%` }}
            title={`${SECTOR_LABELS[key] ?? key}: ${val.toFixed(0)}%`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {entries.map(([key, val]) => (
          <div key={key} className="flex items-center gap-1 text-xs text-slate-400">
            <div className={`w-2 h-2 rounded-sm ${SECTOR_COLORS[key] ?? 'bg-slate-500'}`} />
            <span>{SECTOR_LABELS[key] ?? key}</span>
            <span className="text-slate-500">{val.toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

const EQUIPMENT_META: { key: string; label: string; icon: string }[] = [
  { key: 'chars_combat',   label: 'Battle tanks',          icon: '🛡️' },
  { key: 'avions_chasse',  label: 'Fighter jets',          icon: '✈️' },
  { key: 'navires_guerre', label: 'Warships',              icon: '⚓' },
  { key: 'sous_marins',    label: 'Submarines',            icon: '🌊' },
  { key: 'helicopteres',   label: 'Military helicopters',  icon: '🚁' },
  { key: 'artillerie',     label: 'Artillery pieces',      icon: '💣' },
  { key: 'drones',         label: 'Military drones',       icon: '🛸' },
]

export default function CountryDashboard({ country, isPlayer = false, playerCountry, statHistory, treaties, diplomaticHistory }: Props) {
  const eco = country.economy
  const mil = country.military
  const ns = country.national_stats

  const relationScore = playerCountry?.relations[country.id] ?? null

  return (
    <div className="space-y-4 p-4 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-start gap-3">
        <span className="text-4xl">{country.flag || '🏳️'}</span>
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-bold text-white leading-tight">{country.name}</h2>
          <div className="text-sm text-slate-400">{country.capital} · {country.continent}</div>
          <div className="text-xs text-slate-500 mt-0.5 capitalize">
            {country.government_type?.replace(/_/g, ' ')} · {country.ideology?.replace(/_/g, ' ')}
          </div>
          {country.leader && (
            <div className="text-xs text-pax-gold mt-1">Leader: {country.leader}</div>
          )}
        </div>
        {isPlayer && (
          <span className="bg-pax-gold/20 text-pax-gold text-xs px-2 py-1 rounded-full font-medium shrink-0">
            Your country
          </span>
        )}
        {!isPlayer && relationScore !== null && (
          <div className="shrink-0 text-right">
            <div className="text-xs text-slate-500">Relation</div>
            <div className="text-sm font-bold">{relationScore > 0 ? '+' : ''}{relationScore}</div>
            <RelationBadge score={relationScore} />
          </div>
        )}
      </div>

      {/* Stability */}
      <div className="bg-slate-800/50 rounded-lg p-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-slate-400" />
            <span className="stat-label">National stability</span>
          </div>
          <div className="flex items-center gap-2">
            {statHistory && statHistory.length >= 2 && (
              <Sparkline
                data={statHistory.map(s => s.stability)}
                color={country.stability >= 50 ? '#22c55e' : '#ef4444'}
              />
            )}
            <span className="text-sm font-semibold text-white">{Math.round(country.stability)}/100</span>
          </div>
        </div>
        <StabilityBar value={Math.round(country.stability)} />
      </div>

      {/* Strategic indices */}
      {ns && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Flag className="w-3.5 h-3.5" /> Strategic indices
          </h3>
          <div className="bg-slate-800/50 rounded-lg p-3 space-y-3">
            <PercentBar label="Sovereignty"           value={ns.sovereignty}            max={100} color="bg-purple-500"  icon={Flag} />
            <PercentBar label="Food autonomy"         value={ns.food_autonomy}          max={120} color="bg-green-500"   icon={Wheat} />
            <PercentBar label="Energy autonomy"       value={ns.energy_autonomy}        max={120} color="bg-yellow-500"  icon={Zap} />
            <PercentBar label="Economic independence" value={ns.economic_independence}  max={100} color="bg-cyan-500"    icon={Building2} />
            {(ns as CountryNationalStats & { security?: number }).security !== undefined && (
              <PercentBar label="Internal security"   value={(ns as CountryNationalStats & { security?: number }).security!} max={100} color="bg-rose-500" icon={Shield} />
            )}
          </div>
        </div>
      )}

      {/* Economy */}
      {eco && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5" /> Economy
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-4 h-4 text-slate-400" />
                <span className="stat-label">GDP</span>
              </div>
              <div className="flex items-end justify-between gap-2">
                <div>
                  <div className={`stat-value ${eco.gdp_growth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {(eco.gdp * (country.economy_modifier ?? 1)).toFixed(0)} B$
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">{eco.gdp_growth >= 0 ? '+' : ''}{eco.gdp_growth}% / yr</div>
                </div>
                {statHistory && statHistory.length >= 2 && (
                  <Sparkline
                    data={statHistory.map(s => s.gdp !== undefined ? s.gdp * s.economy_modifier : s.economy_modifier * eco.gdp)}
                    color={eco.gdp_growth >= 0 ? '#22c55e' : '#ef4444'}
                  />
                )}
              </div>
            </div>
            <StatBlock
              icon={Users}
              label="GDP/capita"
              value={`${eco.gdp_per_capita.toLocaleString('en-US')} $`}
              sub={eco.currency}
            />
            <StatBlock
              icon={TrendingUp}
              label="Inflation"
              value={`${eco.inflation}%`}
              color={eco.inflation > 5 ? 'text-red-400' : eco.inflation > 2 ? 'text-yellow-400' : 'text-green-400'}
            />
            <StatBlock
              icon={Users}
              label="Unemployment"
              value={`${eco.unemployment}%`}
              color={eco.unemployment > 10 ? 'text-red-400' : eco.unemployment > 6 ? 'text-yellow-400' : 'text-green-400'}
            />
            <StatBlock
              icon={TrendingUp}
              label="Public debt"
              value={`${eco.debt_pct_gdp.toFixed(1)}% GDP`}
              color={eco.debt_pct_gdp > 100 ? 'text-red-400' : eco.debt_pct_gdp > 60 ? 'text-yellow-400' : 'text-green-400'}
            />
            {eco.budget_balance_pct_gdp !== undefined && (
              <StatBlock
                icon={TrendingUp}
                label="Budget balance"
                value={`${eco.budget_balance_pct_gdp > 0 ? '+' : ''}${eco.budget_balance_pct_gdp.toFixed(1)}% GDP`}
                sub={eco.budget_balance_pct_gdp >= 0 ? 'Surplus' : 'Deficit'}
                color={eco.budget_balance_pct_gdp >= 0 ? 'text-green-400' : eco.budget_balance_pct_gdp > -3 ? 'text-yellow-400' : 'text-red-400'}
              />
            )}
          </div>

          {eco.sectors && Object.keys(eco.sectors).length > 0 && (
            <div className="mt-3 bg-slate-800/50 rounded-lg p-3">
              <div className="text-xs text-slate-400 font-medium mb-2">GDP breakdown</div>
              <SectorsChart sectors={eco.sectors} />
            </div>
          )}
        </div>
      )}

      {/* Military */}
      {mil && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Swords className="w-3.5 h-3.5" /> Military
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <StatBlock
              icon={Shield}
              label="Power"
              value={`${(mil.strength * (country.military_modifier ?? 1.0)).toFixed(1)}/10`}
              sub={`${mil.defense_budget_pct}% of GDP · x${(country.military_modifier ?? 1.0).toFixed(2)}`}
            />
            <StatBlock
              icon={Users}
              label="Active personnel"
              value={mil.active_personnel.toLocaleString('en-US')}
              sub={mil.nuclear_weapons ? '☢ Nuclear' : 'Conventional'}
              color={mil.nuclear_weapons ? 'text-yellow-400' : 'text-white'}
            />
          </div>

          {mil.equipment && Object.keys(mil.equipment).length > 0 && (
            <div className="mt-2 bg-slate-800/50 rounded-lg p-3">
              <div className="text-xs text-slate-400 font-medium mb-2">Arsenal composition</div>
              <div className="space-y-1.5">
                {EQUIPMENT_META.filter(({ key }) => (mil.equipment![key] ?? 0) > 0).map(({ key, label, icon }) => (
                  <div key={key} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 text-slate-300">
                      <span>{icon}</span>
                      <span>{label}</span>
                    </div>
                    <span className="text-slate-200 font-medium tabular-nums">
                      {(mil.equipment![key] ?? 0).toLocaleString('en-US')}
                    </span>
                  </div>
                ))}
                {Object.entries(mil.equipment)
                  .filter(([key]) => !EQUIPMENT_META.some(m => m.key === key))
                  .filter(([, val]) => val > 0)
                  .map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between text-xs">
                      <span className="text-slate-300">{key.replace(/_/g, ' ')}</span>
                      <span className="text-slate-200 font-medium tabular-nums">{val.toLocaleString('en-US')}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Population */}
      {country.population > 0 && (
        <StatBlock
          icon={Users}
          label="Population"
          value={
            country.population >= 1e9
              ? `${(country.population / 1e9).toFixed(2)} B`
              : country.population >= 1e6
              ? `${(country.population / 1e6).toFixed(1)} M`
              : `${(country.population / 1e3).toFixed(0)} K`
          }
        />
      )}

      {/* Alliances */}
      {country.alliances.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5" /> Alliances
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {country.alliances.map((a) => (
              <span key={a} className="bg-pax-accent/20 text-pax-accent text-xs px-2 py-0.5 rounded-full">
                {a}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* At war */}
      {country.at_war_with?.length > 0 && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-3">
          <div className="flex items-center gap-2 text-red-400 text-xs font-semibold mb-1">
            <AlertTriangle className="w-4 h-4" /> At war
          </div>
          <div className="text-xs text-red-300">{country.at_war_with.join(', ')}</div>
        </div>
      )}

      {/* Active treaties (player only) */}
      {isPlayer && treaties && treaties.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Handshake className="w-3.5 h-3.5" /> Active treaties
          </h3>
          <div className="space-y-1.5">
            {treaties.map((t) => (
              <div key={t.id} className="bg-slate-800/50 rounded-lg px-3 py-2 flex items-start justify-between gap-2">
                <div>
                  <div className="text-xs text-white font-medium capitalize">{t.type} — {t.country_b === country.id ? t.country_a : t.country_b}</div>
                  <div className="text-xs text-slate-400 mt-0.5 line-clamp-1">{t.summary}</div>
                </div>
                <div className="shrink-0 text-right text-xs text-slate-500">
                  {t.year}/{String(t.month).padStart(2, '0')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Diplomatic history (foreign country) */}
      {!isPlayer && diplomaticHistory && diplomaticHistory.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5" /> Diplomatic exchanges
          </h3>
          <div className="space-y-2">
            {diplomaticHistory.slice(-6).map((msg) => (
              <div key={msg.id} className="bg-slate-800/50 rounded-lg p-2.5 space-y-1.5">
                {msg.content && (
                  <div className="text-xs">
                    <span className="text-pax-accent font-medium">You: </span>
                    <span className="text-slate-300 line-clamp-2">{msg.content}</span>
                  </div>
                )}
                {msg.response && (
                  <div className="text-xs">
                    <span className="text-pax-gold font-medium">{country.name}: </span>
                    <span className="text-slate-400 line-clamp-3">{msg.response}</span>
                  </div>
                )}
                <div className="text-xs text-slate-600">{new Date(msg.timestamp).toLocaleDateString('en-US')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Description */}
      {country.description && (
        <div className="text-xs text-slate-400 leading-relaxed border-t border-pax-border pt-3">
          {country.description}
        </div>
      )}
    </div>
  )
}
