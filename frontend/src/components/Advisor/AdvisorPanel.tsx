import { useState, useRef, useEffect } from 'react'
import { Send, BookOpen, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { streamAdvisor, streamBriefing } from '@/api/client'
import { useGameStore } from '@/store/gameStore'
import type { GameState } from '@/types'

interface Message {
  role: 'user' | 'advisor'
  content: string
  streaming?: boolean
}

const SUGGESTED_QUESTIONS = [
  'Donne-moi un briefing de la situation actuelle',
  'Quelles sont mes principales menaces ?',
  'Comment améliorer mes relations avec nos voisins ?',
  'Quelle politique économique recommandes-tu ?',
  'Dois-je rejoindre ou quitter des alliances ?',
  'Quelles sont nos opportunités diplomatiques ?',
]

interface Props {
  gameState: GameState
}

export default function AdvisorPanel({ gameState }: Props) {
  const { sessionId } = useGameStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isBriefing, setIsBriefing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function askAdvisor(question: string) {
    if (!question.trim() || !sessionId || isSending) return

    setInput('')
    setIsSending(true)
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question },
      { role: 'advisor', content: '', streaming: true },
    ])

    const finalize = (error?: string) => {
      setMessages((prev) => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last?.role === 'advisor') {
          updated[updated.length - 1] = {
            ...last,
            streaming: false,
            content: error ? `⚠️ Erreur : ${error}` : last.content,
          }
        }
        return updated
      })
      setIsSending(false)
    }

    streamAdvisor(
      sessionId,
      question,
      (chunk) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last?.role === 'advisor') {
            updated[updated.length - 1] = { ...last, content: last.content + chunk }
          }
          return updated
        })
      },
      () => finalize(),
      (err) => finalize(err),
    )
  }

  function requestBriefing() {
    if (!sessionId || isBriefing || isSending) return
    setIsBriefing(true)
    setMessages((prev) => [
      ...prev,
      { role: 'advisor', content: '', streaming: true },
    ])

    const finalizeBriefing = (error?: string) => {
      setMessages((prev) => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last?.role === 'advisor') {
          updated[updated.length - 1] = {
            ...last,
            streaming: false,
            content: error ? `⚠️ Erreur : ${error}` : last.content,
          }
        }
        return updated
      })
      setIsBriefing(false)
    }

    streamBriefing(
      sessionId,
      (chunk) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last?.role === 'advisor') {
            updated[updated.length - 1] = { ...last, content: last.content + chunk }
          }
          return updated
        })
      },
      () => finalizeBriefing(),
      (err) => finalizeBriefing(err),
    )
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      askAdvisor(input)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-pax-border">
        <h2 className="font-semibold text-white flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-pax-accent" /> Conseiller Politique
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          {gameState.player_country.name} · {gameState.year}/{String(gameState.month).padStart(2, '0')}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-4">
            <div className="text-center py-4">
              <BookOpen className="w-10 h-10 text-slate-600 mx-auto mb-2" />
              <p className="text-sm text-slate-400">Votre conseiller politique est prêt.</p>
              <button
                onClick={requestBriefing}
                disabled={isBriefing}
                className="mt-3 btn-primary flex items-center gap-2 mx-auto"
              >
                <Sparkles className="w-4 h-4" />
                {isBriefing ? 'Rédaction...' : 'Briefing de situation'}
              </button>
            </div>
            <div>
              <div className="text-xs text-slate-500 mb-2">Questions suggérées :</div>
              <div className="space-y-1.5">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => askAdvisor(q)}
                    disabled={isSending}
                    className="w-full text-left text-xs text-slate-300 bg-slate-800/50 hover:bg-slate-700 px-3 py-2 rounded-lg transition-colors border border-transparent hover:border-pax-border disabled:opacity-50"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === 'user' && (
              <div className="flex justify-end">
                <div className="max-w-[85%] bg-pax-accent text-white rounded-lg px-3 py-2 text-sm">
                  {msg.content}
                </div>
              </div>
            )}
            {msg.role === 'advisor' && (
              <div className="flex gap-2">
                <div className="w-7 h-7 bg-pax-accent/20 rounded-full flex items-center justify-center shrink-0 mt-1">
                  <BookOpen className="w-3.5 h-3.5 text-pax-accent" />
                </div>
                <div className="flex-1 bg-slate-800 border border-pax-border rounded-lg px-3 py-2 text-sm text-slate-200 leading-relaxed prose prose-invert prose-sm max-w-none">
                  {msg.content
                    ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                    : msg.streaming && <span className="text-slate-400 text-xs animate-pulse">analyse en cours...</span>}
                  {msg.streaming && msg.content && <span className="cursor-blink" />}
                </div>
              </div>
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
            placeholder="Posez une question à votre conseiller..."
            rows={2}
            disabled={isSending}
            className="flex-1 bg-slate-800 border border-pax-border rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 resize-none focus:outline-none focus:border-pax-accent disabled:opacity-50"
          />
          <button
            onClick={() => askAdvisor(input)}
            disabled={!input.trim() || isSending}
            className="btn-primary self-end px-3 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
