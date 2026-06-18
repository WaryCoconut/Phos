import { useState, useRef, useEffect } from 'react'
import { Send, Globe, Search } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Country, GameState, DiplomaticEffect } from '@/types'
import { streamDiplomacy, gameApi } from '@/api/client'
import { useGameStore } from '@/store/gameStore'
import clsx from 'clsx'

interface Message {
  role: 'player' | 'country'
  content: string
  streaming?: boolean
  effect?: DiplomaticEffect
  senderId?: string
}

interface Props {
  gameState: GameState
  targetCountry: Country | null
  onSelectTarget: (country: Country) => void
}

function DiplomaticEffectBadge({ effect, targetName }: { effect: DiplomaticEffect; targetName: string }) {
  const parts: string[] = []
  if (effect.agreement_reached && effect.summary) parts.push(`✅ ${effect.summary}`)
  if (effect.relation_delta > 0) parts.push(`Relations +${effect.relation_delta}`)
  else if (effect.relation_delta < 0) parts.push(`Relations ${effect.relation_delta}`)
  if (effect.economy_delta > 0) parts.push(`Economy +${(effect.economy_delta * 100).toFixed(1)}%`)
  else if (effect.economy_delta < 0) parts.push(`Economy ${(effect.economy_delta * 100).toFixed(1)}%`)
  if (!parts.length) return null
  const isPositive = effect.relation_delta >= 0 && !effect.summary?.includes('refus')
  return (
    <div className={clsx(
      'ml-9 rounded-md px-3 py-1.5 text-xs flex flex-wrap gap-x-3 gap-y-0.5 border',
      isPositive
        ? 'bg-green-950/50 border-green-800/50 text-green-300'
        : 'bg-red-950/50 border-red-800/50 text-red-300'
    )}>
      {parts.map((p, i) => <span key={i}>{p}</span>)}
    </div>
  )
}

export default function DiplomacyPanel({ gameState, targetCountry, onSelectTarget }: Props) {
  const { sessionId, refreshState } = useGameStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [search, setSearch] = useState('')
  const [isCreatingGroup, setIsCreatingGroup] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [selectedMembers, setSelectedMembers] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const stopStreamRef = useRef<(() => void) | null>(null)

  const otherCountries = Object.values(gameState.countries).filter(
    (c) => c.id !== gameState.player_country.id
  )

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!targetCountry) {
      setMessages([])
      return
    }
    const isGroup = targetCountry.id.startsWith('group:')
    const past = gameState.diplomatic_history.filter(m => {
      if (isGroup) {
        return m.to_country === targetCountry.id
      } else {
        return (m.from_country === gameState.player_country.id && m.to_country === targetCountry.id) ||
               (m.from_country === targetCountry.id && m.to_country === gameState.player_country.id)
      }
    })
    const converted: Message[] = []
    for (const m of past) {
      if (m.from_country === gameState.player_country.id) {
        converted.push({ role: 'player', content: m.content })
      } else {
        converted.push({ role: 'country', content: m.content || m.response || '', senderId: m.from_country })
      }
    }
    setMessages(converted)
  }, [targetCountry?.id])

  function sendMessage() {
    if (!input.trim() || !targetCountry || !sessionId || isSending) return

    const userMsg = input.trim()
    setInput('')
    setIsSending(true)
    setMessages((prev) => [
      ...prev,
      { role: 'player', content: userMsg },
    ])

    stopStreamRef.current = streamDiplomacy(
      sessionId,
      targetCountry.id,
      userMsg,
      (chunk, senderId) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          const currentSender = senderId || targetCountry.id
          if (last?.role === 'country' && last.senderId === currentSender && last.streaming) {
            updated[updated.length - 1] = { ...last, content: last.content + chunk }
          } else {
            if (last?.role === 'country' && last.streaming) {
              updated[updated.length - 1] = { ...last, streaming: false }
            }
            updated.push({
              role: 'country',
              senderId: currentSender,
              content: chunk,
              streaming: true
            })
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
            updated[updated.length - 1] = { ...last, streaming: false, content: `⚠️ Error: ${err}` }
          }
          return updated
        })
        setIsSending(false)
      },
      (effect) => {
        if (!effect.relation_delta && !effect.economy_delta && !effect.domestic_events?.length) return
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last?.role === 'country') {
            updated[updated.length - 1] = { ...last, effect }
          }
          return updated
        })
      },
    )
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (isCreatingGroup) {
    return (
      <div className="flex flex-col h-full p-3 space-y-3">
        <div className="flex items-center justify-between border-b border-pax-border pb-2 shrink-0">
          <h3 className="font-semibold text-white text-xs">Create Group Chat</h3>
          <button
            onClick={() => { setIsCreatingGroup(false); setNewGroupName(''); setSelectedMembers([]) }}
            className="text-[10px] text-slate-400 hover:text-white"
          >
            Cancel
          </button>
        </div>
        <div className="space-y-1 shrink-0">
          <label className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">Group Name</label>
          <input
            type="text"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            placeholder="e.g. Coalition Council, Trade Bloc..."
            className="w-full bg-slate-800 border border-pax-border rounded-md px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
          />
        </div>
        <div className="space-y-1 flex-1 flex flex-col min-h-0">
          <label className="text-[9px] text-slate-500 font-medium uppercase tracking-wider mb-0.5">Select Members</label>
          <div className="flex-1 overflow-y-auto border border-pax-border rounded-md p-2 bg-slate-900/40 space-y-1">
            {otherCountries
              .sort((a, b) => a.name.localeCompare(b.name))
              .map((c) => (
                <label key={c.id} className="flex items-center gap-2 p-1 rounded hover:bg-slate-850 cursor-pointer text-xs text-slate-200">
                  <input
                    type="checkbox"
                    checked={selectedMembers.includes(c.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedMembers(prev => [...prev, c.id])
                      } else {
                        setSelectedMembers(prev => prev.filter(id => id !== c.id))
                      }
                    }}
                    className="rounded border-slate-700 bg-slate-800 text-pax-accent focus:ring-pax-accent"
                  />
                  <span>{c.flag}</span>
                  <span className="truncate">{c.name}</span>
                </label>
              ))}
          </div>
        </div>
        <button
          onClick={async () => {
            if (!newGroupName.trim() || selectedMembers.length < 2 || !sessionId) return
            try {
              setIsSending(true)
              await gameApi.createCustomGroup(sessionId, newGroupName.trim(), selectedMembers)
              await refreshState()
              setIsCreatingGroup(false)
              setNewGroupName('')
              setSelectedMembers([])
            } catch (err) {
              console.error(err)
            } finally {
              setIsSending(false)
            }
          }}
          disabled={!newGroupName.trim() || selectedMembers.length < 2 || isSending}
          className="w-full btn-primary text-xs py-2 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
        >
          Create Group
        </button>
      </div>
    )
  }

  if (!targetCountry) {
    const filtered = otherCountries
      .filter((c) =>
        !search ||
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.continent?.toLowerCase().includes(search.toLowerCase())
      )
      .sort((a, b) => a.name.localeCompare(b.name))

    const alliances = Object.values(gameState.alliances || {})
    const customGroups = gameState.custom_groups || []

    return (
      <div className="flex flex-col h-full">
        <div className="p-3 border-b border-pax-border space-y-2 shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-white flex items-center gap-2 text-sm">
              <Globe className="w-4 h-4 text-pax-accent" /> Diplomacy
            </h2>
            <button
              onClick={() => setIsCreatingGroup(true)}
              className="text-[10px] bg-pax-accent/20 text-pax-accent hover:bg-pax-accent hover:text-white px-2 py-0.5 rounded transition-colors"
            >
              + Create Group
            </button>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter by country or continent…"
              className="w-full bg-slate-800 border border-pax-border rounded-md pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-4">
          {/* Alliances preset groups */}
          {!search && alliances.length > 0 && (
            <div className="space-y-1">
              <div className="text-[9px] text-slate-500 font-bold uppercase tracking-wider px-2">Preset Alliance Groups</div>
              <div className="space-y-0.5">
                {alliances.map((all) => (
                  <button
                    key={all.id}
                    onClick={() => {
                      const virtualGroup = {
                        id: `group:${all.id}`,
                        name: `${all.name} Group Chat`,
                        flag: '🌐',
                        capital: 'Alliance Headquarters',
                        continent: all.type,
                        leader: `${all.members.length} members`,
                        relations: {},
                        stability: 100,
                        population: 0,
                        government_type: 'alliance',
                        ideology: all.type,
                        personality_traits: [],
                        description: all.description
                      } as unknown as Country
                      onSelectTarget(virtualGroup)
                    }}
                    className="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-800/60 transition-colors text-left"
                  >
                    <div className="w-7 h-7 rounded bg-pax-accent/10 border border-pax-accent/20 flex items-center justify-center text-sm shrink-0">
                      🌐
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold text-white truncate">{all.name} Group</div>
                      <div className="text-[10px] text-slate-500 truncate">{all.members.length} members · {all.type}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Custom groups */}
          {!search && customGroups.length > 0 && (
            <div className="space-y-1">
              <div className="text-[9px] text-slate-500 font-bold uppercase tracking-wider px-2">Custom Groups</div>
              <div className="space-y-0.5">
                {customGroups.map((cg) => (
                  <button
                    key={cg.id}
                    onClick={() => {
                      const virtualGroup = {
                        id: `group:${cg.id}`,
                        name: `${cg.name} Group Chat`,
                        flag: '👥',
                        capital: 'Custom Group Headquarters',
                        continent: 'Custom',
                        leader: `${cg.members.length} members`,
                        relations: {},
                        stability: 100,
                        population: 0,
                        government_type: 'custom_group',
                        ideology: 'Custom',
                        personality_traits: [],
                        description: `Custom group with ${cg.members.join(', ')}.`
                      } as unknown as Country
                      onSelectTarget(virtualGroup)
                    }}
                    className="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-800/60 transition-colors text-left"
                  >
                    <div className="w-7 h-7 rounded bg-slate-700/30 border border-slate-750 flex items-center justify-center text-sm shrink-0">
                      👥
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold text-white truncate">{cg.name}</div>
                      <div className="text-[10px] text-slate-500 truncate">{cg.members.length} countries</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-1">
            <div className="text-[9px] text-slate-500 font-bold uppercase tracking-wider px-2">Countries</div>
            {filtered.length === 0 ? (
              <div className="text-xs text-slate-500 text-center py-4">No countries found</div>
            ) : (
              <div className="space-y-0.5">
                {filtered.map((c) => {
                  const relScore = gameState.player_country.relations[c.id] ?? 0
                  return (
                    <button
                      key={c.id}
                      onClick={() => onSelectTarget(c)}
                      className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-slate-700 transition-colors text-left"
                    >
                      <span className="text-xl shrink-0">{c.flag || '🏳️'}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs text-white truncate">{c.name}</div>
                        <div className="text-[10px] text-slate-500">{c.continent}</div>
                      </div>
                      <div className={clsx('text-xs font-medium shrink-0', {
                        'text-green-400': relScore >= 20,
                        'text-slate-400': relScore > -20 && relScore < 20,
                        'text-red-400': relScore <= -20,
                      })}>
                        {relScore > 0 ? '+' : ''}{relScore}
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
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
          ← Back
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
            Open a diplomatic dialogue with {targetCountry.name}.<br />
            Your messages will be handled by the AI representing this country.
          </div>
        )}
        {messages.length > 0 && (
          <div className="text-xs text-slate-600 text-center py-1 border-b border-pax-border/40 mb-2">
            — Past exchanges —
          </div>
        )}
        {messages.map((msg, i) => {
          const isGroupChat = targetCountry.id.startsWith('group:')
          const senderCountry = msg.senderId ? gameState.countries[msg.senderId] : targetCountry
          return (
            <div key={i} className="space-y-1.5">
              <div className={clsx('flex gap-2', msg.role === 'player' ? 'justify-end' : 'justify-start')}>
                {msg.role === 'country' && (
                  <span className="text-xl self-start mt-1">{senderCountry?.flag || '🏳️'}</span>
                )}
                <div
                  className={clsx(
                    'max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed',
                    msg.role === 'player'
                      ? 'bg-pax-accent text-white'
                      : 'bg-slate-800 text-slate-200 border border-pax-border prose prose-invert prose-sm max-w-none'
                  )}
                >
                  {isGroupChat && msg.role === 'country' && senderCountry && (
                    <div className="text-[10px] text-pax-gold font-bold mb-0.5">{senderCountry.name}</div>
                  )}
                  {msg.role === 'country' && msg.content
                    ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                    : msg.content || (msg.streaming ? '' : '...')}
                  {msg.streaming && msg.content && <span className="cursor-blink" />}
                  {msg.streaming && !msg.content && (
                    <span className="text-slate-400 text-xs animate-pulse">typing...</span>
                  )}
                </div>
                {msg.role === 'player' && (
                  <span className="text-xl self-start mt-1">{gameState.player_country.flag || '🏳️'}</span>
                )}
              </div>
              {msg.effect && <DiplomaticEffectBadge effect={msg.effect} targetName={senderCountry?.name || targetCountry.name} />}
            </div>
          )
        })}
        {isSending && messages[messages.length - 1]?.role === 'player' && (
          <div className="flex gap-2 justify-start">
            <span className="text-xl self-start mt-1">{targetCountry.flag || '🏳️'}</span>
            <div className="bg-slate-800 border border-pax-border rounded-lg px-4 py-2.5 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-pax-border">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Message to ${targetCountry.name}...`}
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
        <div className="text-xs text-slate-500 mt-1">Enter to send · Shift+Enter for new line</div>
      </div>
    </div>
  )
}
