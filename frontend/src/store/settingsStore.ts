import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface ApiSettings {
  apiKey: string
  apiBaseUrl: string
  model: string
  provider: 'socle' | 'ollama' | 'deepseek'
  language: string
}

const DEFAULTS: ApiSettings = {
  apiKey: '',
  apiBaseUrl: 'https://app.socle.ai/api/v1',
  model: 'qwen3-235b-a22b-instruct-2507',
  provider: 'socle',
  language: 'English',
}

interface SettingsStore {
  settings: ApiSettings
  update: (patch: Partial<ApiSettings>) => void
  reset: () => void
  isConfigured: () => boolean
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      settings: DEFAULTS,
      update: (patch) =>
        set((s) => ({ settings: { ...s.settings, ...patch } })),
      reset: () => set({ settings: DEFAULTS }),
      isConfigured: () => {
        const s = get().settings
        if (s.provider === 'ollama') return Boolean(s.apiBaseUrl.trim())
        return Boolean(s.apiKey.trim())
      },
    }),
    { name: 'pax-api-settings' }
  )
)
