import { create } from 'zustand'
import type { GameState, PanelView, Country } from '@/types'
import { gameApi } from '@/api/client'

interface GameStore {
  sessionId: string | null
  gameState: GameState | null
  activePanel: PanelView
  selectedCountry: Country | null
  isLoading: boolean
  error: string | null
  isEndingTurn: boolean

  setSessionId: (id: string) => void
  setGameState: (state: GameState) => void
  setActivePanel: (panel: PanelView) => void
  setSelectedCountry: (country: Country | null) => void
  setError: (err: string | null) => void

  loadGame: (sessionId: string) => Promise<void>
  endTurn: () => Promise<void>
  refreshState: () => Promise<void>
}

export const useGameStore = create<GameStore>((set, get) => ({
  sessionId: null,
  gameState: null,
  activePanel: 'dashboard',
  selectedCountry: null,
  isLoading: false,
  error: null,
  isEndingTurn: false,

  setSessionId: (id) => set({ sessionId: id }),
  setGameState: (state) => set({ gameState: state }),
  setActivePanel: (panel) => set({ activePanel: panel }),
  setSelectedCountry: (country) => set({ selectedCountry: country }),
  setError: (err) => set({ error: err }),

  loadGame: async (sessionId) => {
    set({ isLoading: true, error: null, sessionId })
    try {
      const state = await gameApi.getState(sessionId)
      set({ gameState: state, isLoading: false })
    } catch {
      set({ error: 'Failed to load game', isLoading: false })
    }
  },

  endTurn: async () => {
    const { sessionId } = get()
    if (!sessionId) return
    set({ isEndingTurn: true })
    try {
      await gameApi.endTurn(sessionId)
      const state = await gameApi.getState(sessionId)
      set({ gameState: state, isEndingTurn: false })
    } catch {
      set({ error: 'Failed to advance turn', isEndingTurn: false })
    }
  },

  refreshState: async () => {
    const { sessionId } = get()
    if (!sessionId) return
    try {
      const state = await gameApi.getState(sessionId)
      set({ gameState: state })
    } catch {
      // silently fail on refresh
    }
  },
}))
