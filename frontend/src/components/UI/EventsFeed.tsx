import { useState } from 'react'
import { Newspaper } from 'lucide-react'
import type { WorldEvent } from '@/types'

interface Props {
  events: WorldEvent[]
}

const months = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

const EVENT_TYPES = [
  { id: 'all', label: 'All' },
  { id: 'diplomatic', label: '🤝 Diplomatic' },
  { id: 'economic', label: '📈 Economic' },
  { id: 'military', label: '⚔️ Military' },
  { id: 'political', label: '🏛️ Political' },
  { id: 'humanitarian', label: '🏥 Humanitarian' },
  { id: 'natural', label: '🌪️ Natural' },
  { id: 'reaction', label: '💬 Reaction' },
  { id: 'consequence', label: '⏳ Consequence' },
] as const

type FilterType = typeof EVENT_TYPES[number]['id']

const TYPE_BADGE: Record<string, { icon: string; color: string }> = {
  diplomatic:   { icon: '🤝', color: 'bg-blue-900/40 text-blue-300 border border-blue-700/40' },
  economic:     { icon: '📈', color: 'bg-green-900/40 text-green-300 border border-green-700/40' },
  military:     { icon: '⚔️', color: 'bg-red-900/40 text-red-300 border border-red-700/40' },
  political:    { icon: '🏛️', color: 'bg-purple-900/40 text-purple-300 border border-purple-700/40' },
  humanitarian: { icon: '🏥', color: 'bg-pink-900/40 text-pink-300 border border-pink-700/40' },
  natural:      { icon: '🌪️', color: 'bg-slate-700/60 text-slate-300 border border-slate-600/40' },
  reaction:     { icon: '💬', color: 'bg-yellow-900/40 text-yellow-300 border border-yellow-700/40' },
  consequence:  { icon: '⏳', color: 'bg-orange-900/40 text-orange-300 border border-orange-700/40' },
  general:      { icon: '🌍', color: 'bg-slate-700/40 text-slate-300 border border-slate-600/30' },
}

export default function EventsFeed({ events }: Props) {
  const [filter, setFilter] = useState<FilterType>('all')

  const sorted = [...events].reverse()
  const filtered = filter === 'all' ? sorted : sorted.filter(e => (e.type ?? 'general') === filter)

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-pax-border">
        <h2 className="font-semibold text-white flex items-center gap-2 text-sm">
          <Newspaper className="w-4 h-4 text-pax-accent" /> News Feed
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">{filtered.length} / {sorted.length} events</p>
      </div>

      {/* Filter chips */}
      <div className="px-3 py-2 border-b border-pax-border flex flex-wrap gap-1">
        {EVENT_TYPES.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setFilter(id)}
            className={`text-xs px-2 py-0.5 rounded-full transition-colors ${
              filter === id
                ? 'bg-pax-accent text-white'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {filtered.length === 0 && (
          <div className="text-center py-10 text-slate-500 text-sm">
            No events {filter !== 'all' ? `of type "${filter}"` : ''}
          </div>
        )}
        {filtered.map((evt) => {
          const badge = TYPE_BADGE[evt.type ?? 'general'] ?? TYPE_BADGE.general
          return (
            <div
              key={evt.id}
              className={`border rounded-lg p-3 text-sm ${
                evt.triggered_by_player
                  ? 'bg-blue-900/20 border-blue-800'
                  : 'bg-slate-800/50 border-pax-border'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="font-medium text-white leading-tight text-xs">{evt.title}</div>
                <div className="text-xs text-slate-500 whitespace-nowrap shrink-0">
                  {months[evt.month - 1]} {evt.year}
                  {evt.day && evt.day !== 1 ? ` d${evt.day}` : ''}
                </div>
              </div>
              <span className={`inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded mb-1.5 ${badge.color}`}>
                {badge.icon} {evt.type ?? 'general'}
              </span>
              <div className="text-xs text-slate-400 leading-relaxed">{evt.description}</div>
              {evt.affected_countries?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {evt.affected_countries.map((c) => (
                    <span key={c} className="text-xs bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded">
                      {c}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
