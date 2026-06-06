import { useState, useRef, useEffect } from 'react'
import { Send, Globe } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Country, GameState } from '@/types'
import { streamDiplomacy } from '@/api/client'
import { useGameStore } from '@/store/gameStore'
import clsx from 'clsx'

interface Message {
  role: 'player' | 'country'
  content: string
  streaming?: boolean
}

interface Props {
  gameState: GameState
  targetCountry: Country | null
  onSelectTarget: (country: Country) => void
}

export default function DiplomacyPanel({ gameState, targetCountry, onSelectTarget }: Props) {
  const { sessionId, refreshState } = useGameStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const stopStreamRef = useRef<(() => void) | null>(null)

  const otherCountries = Object.values(gameState.countries).filter(
    (c) => c.id !== gameState.player_country.id
  )

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    setMessages([])
  }, [targetCountry?.id])

  function sendMessage() {
    if (!input.trim() || !targetCountry || !sessionId || isSending) return

    const userMsg = input.trim()
    setInput('')
    setIsSending(true)
    setMessages((prev) => [
      ...prev,
      { role: 'player', content: userMsg },
      { role: 'country', content: '', streaming: true },
    ])

    stopStreamRef.current = streamDiplomacy(
      sessionId,
      targetCountry.id,
      userMsg,
      (chunk) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last?.role === 'country') {
            updated[updated.length - 1] = { ...last, content: last.content + chunk }
          }
          return updated
        })
      },
      () => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last?.role === 'country') {
            updated[updated.length - 1] = { ...last, streaming: false }
          }
          return updated
        })
        setIsSending(false)
        refreshState()
      },
      (err) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last?.role === 'country') {
            updated[updated.length - 1] = { ...last, streaming: false, content: `⚠️ Erreur : ${err}` }
          }
          return updated
        })
        setIsSending(false)
      },
    )
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (!targetCountry) {
    return (
      <div className="flex flex-col h-full">
        <div className="p-4 border-b border-pax-border">
          <h2 className="font-semibold text-white flex items-center gap-2">
            <Globe className="w-4 h-4 text-pax-accent" /> Diplomatie
          </h2>
          <p className="text-xs text-slate-400 mt-1">Sélectionnez un pays sur la carte</p>
        </div>
        <div className="p-4 overflow-y-auto">
          <div className="text-sm text-slate-400 mb-3">Pays disponibles :</div>
          <div className="space-y-1.5">
            {otherCountries
              .sort((a, b) => a.name.localeCompare(b.name))
              .map((c) => {
                const rel = gameState.player_country.relations[c.id] ?? 0
                return (
                  <button
                    key={c.id}
                    onClick={() => onSelectTarget(c)}
                    className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-slate-700 transition-colors text-left"
                  >
                    <span className="text-xl">{c.flag || '🏳️'}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-white truncate">{c.name}</div>
                      <div className="text-xs text-slate-500">{c.continent}</div>
                    </div>
                    <div className={clsx('text-xs font-medium', {
                      'text-green-400': rel >= 20,
                      'text-slate-400': rel > -20 && rel < 20,
                      'text-red-400': rel <= -20,
                    })}>
                      {rel > 0 ? '+' : ''}{rel}
                    </div>
                  </button>
                )
              })}
          </div>
        </div>
      </div>
    )
  }

  const rel = gameState.player_country.relations[targetCountry.id] ?? 0

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-pax-border flex items-center gap-3">
        <button
          onClick={() => onSelectTarget(null as unknown as Country)}
          className="text-slate-400 hover:text-white text-xs"
        >
          ← Retour
        </button>
        <span className="text-2xl">{targetCountry.flag || '🏳️'}</span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-white truncate">{targetCountry.name}</div>
          <div className="text-xs text-slate-500">{targetCountry.leader}</div>
        </div>
        <div className={clsx('text-xs font-bold', {
          'text-green-400': rel >= 20,
          'text-slate-400': rel > -20 && rel < 20,
          'text-red-400': rel <= -20,
        })}>
          {rel > 0 ? '+' : ''}{rel}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-xs text-slate-500 text-center py-8">
            Ouvrez le dialogue diplomatique avec {targetCountry.name}.<br />
            Vos messages seront traités par l'IA représentant ce pays.
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={clsx('flex gap-2', msg.role === 'player' ? 'justify-end' : 'justify-start')}
          >
            {msg.role === 'country' && (
              <span className="text-xl self-start mt-1">{targetCountry.flag || '🏳️'}</span>
            )}
            <div
              className={clsx(
                'max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed',
                msg.role === 'player'
                  ? 'bg-pax-accent text-white'
                  : 'bg-slate-800 text-slate-200 border border-pax-border prose prose-invert prose-sm max-w-none'
              )}
            >
              {msg.role === 'country' && msg.content
                ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                : msg.content || (msg.streaming ? '' : '...')}
              {msg.streaming && msg.content && <span className="cursor-blink" />}
              {msg.streaming && !msg.content && (
                <span className="text-slate-400 text-xs animate-pulse">rédaction...</span>
              )}
            </div>
            {msg.role === 'player' && (
              <span className="text-xl self-start mt-1">{gameState.player_country.flag || '🏳️'}</span>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-pax-border">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Message à ${targetCountry.name}...`}
            rows={2}
            disabled={isSending}
            className="flex-1 bg-slate-800 border border-pax-border rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 resize-none focus:outline-none focus:border-pax-accent disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isSending}
            className="btn-primary self-end px-3 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="text-xs text-slate-500 mt-1">Entrée pour envoyer · Shift+Entrée pour nouvelle ligne</div>
      </div>
    </div>
  )
}
