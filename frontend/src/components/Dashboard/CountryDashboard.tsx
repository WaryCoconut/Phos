import { Shield, TrendingUp, Users, Swords, AlertTriangle, Globe } from 'lucide-react'
import type { Country } from '@/types'

interface Props {
  country: Country
  isPlayer?: boolean
  playerCountry?: Country
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
  if (score >= 60) return <span className="text-green-400 text-xs font-medium">Allié</span>
  if (score >= 20) return <span className="text-green-600 text-xs font-medium">Ami</span>
  if (score >= -20) return <span className="text-slate-400 text-xs font-medium">Neutre</span>
  if (score >= -60) return <span className="text-orange-400 text-xs font-medium">Hostile</span>
  return <span className="text-red-400 text-xs font-medium">Ennemi</span>
}

function StabilityBar({ value }: { value: number }) {
  const color = value >= 70 ? 'bg-green-500' : value >= 40 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="w-full bg-slate-700 rounded-full h-1.5 mt-1">
      <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${value}%` }} />
    </div>
  )
}

export default function CountryDashboard({ country, isPlayer = false, playerCountry }: Props) {
  const eco = country.economy
  const mil = country.military

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
            <div className="text-xs text-pax-gold mt-1">Dirigeant : {country.leader}</div>
          )}
        </div>
        {isPlayer && (
          <span className="bg-pax-gold/20 text-pax-gold text-xs px-2 py-1 rounded-full font-medium shrink-0">
            Votre pays
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

      {/* Stabilité */}
      <div className="bg-slate-800/50 rounded-lg p-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-slate-400" />
            <span className="stat-label">Stabilité nationale</span>
          </div>
          <span className="text-sm font-semibold text-white">{country.stability}/100</span>
        </div>
        <StabilityBar value={country.stability} />
      </div>

      {/* Stats économiques */}
      {eco && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5" /> Économie
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <StatBlock
              icon={TrendingUp}
              label="PIB"
              value={`${(eco.gdp * (country.economy_modifier ?? 1)).toFixed(0)} Md$`}
              sub={`${eco.gdp_growth >= 0 ? '+' : ''}${eco.gdp_growth}% / an`}
              color={eco.gdp_growth >= 0 ? 'text-green-400' : 'text-red-400'}
            />
            <StatBlock
              icon={Users}
              label="PIB/hab."
              value={`${eco.gdp_per_capita.toLocaleString('fr-FR')} $`}
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
              label="Chômage"
              value={`${eco.unemployment}%`}
              color={eco.unemployment > 10 ? 'text-red-400' : eco.unemployment > 6 ? 'text-yellow-400' : 'text-green-400'}
            />
          </div>
          {eco.main_sectors?.length > 0 && (
            <div className="mt-2 text-xs text-slate-500">
              <span className="text-slate-400">Secteurs : </span>
              {eco.main_sectors.slice(0, 4).join(', ')}
            </div>
          )}
        </div>
      )}

      {/* Stats militaires */}
      {mil && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Swords className="w-3.5 h-3.5" /> Militaire
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <StatBlock
              icon={Shield}
              label="Puissance"
              value={`${mil.strength}/10`}
              sub={`${mil.defense_budget_pct}% du PIB`}
            />
            <StatBlock
              icon={Users}
              label="Personnel actif"
              value={mil.active_personnel.toLocaleString('fr-FR')}
              sub={mil.nuclear_weapons ? '☢ Nucléaire' : 'Conventionnel'}
              color={mil.nuclear_weapons ? 'text-yellow-400' : 'text-white'}
            />
          </div>
        </div>
      )}

      {/* Population */}
      {country.population > 0 && (
        <StatBlock
          icon={Users}
          label="Population"
          value={
            country.population >= 1e9
              ? `${(country.population / 1e9).toFixed(2)} Md`
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

      {/* Situation de guerre */}
      {country.at_war_with?.length > 0 && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-3">
          <div className="flex items-center gap-2 text-red-400 text-xs font-semibold mb-1">
            <AlertTriangle className="w-4 h-4" /> En guerre
          </div>
          <div className="text-xs text-red-300">{country.at_war_with.join(', ')}</div>
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
