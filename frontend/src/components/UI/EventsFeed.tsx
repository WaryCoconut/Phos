import { Newspaper } from 'lucide-react'
import type { WorldEvent } from '@/types'

interface Props {
  events: WorldEvent[]
}

const months = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

export default function EventsFeed({ events }: Props) {
  const sorted = [...events].reverse()

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-pax-border">
        <h2 className="font-semibold text-white flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-pax-accent" /> News Feed
        </h2>
        <p className="text-xs text-slate-400 mt-1">{sorted.length} events</p>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {sorted.length === 0 && (
          <div className="text-center py-10 text-slate-500 text-sm">
            No events yet
          </div>
        )}
        {sorted.map((evt) => (
          <div
            key={evt.id}
            className={`border rounded-lg p-3 text-sm ${
              evt.triggered_by_player
                ? 'bg-blue-900/20 border-blue-800'
                : 'bg-slate-800/50 border-pax-border'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="font-medium text-white leading-tight">{evt.title}</div>
              <div className="text-xs text-slate-500 whitespace-nowrap shrink-0">
                {months[evt.month - 1]} {evt.year}
              </div>
            </div>
            <div className="text-xs text-slate-400 mt-1.5 leading-relaxed">{evt.description}</div>
            {evt.affected_countries?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {evt.affected_countries.map((c) => (
                  <span key={c} className="text-xs bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded">
                    {c}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
