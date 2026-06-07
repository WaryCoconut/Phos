import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface ApiSettings {
  apiKey: string
  apiBaseUrl: string
  model: string
}

const DEFAULTS: ApiSettings = {
  apiKey: '',
  apiBaseUrl: 'https://app.socle.ai/api/v1',
  model: 'qwen3-235b-a22b-instruct-2507',
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
      isConfigured: () => Boolean(get().settings.apiKey.trim()),
    }),
    { name: 'pax-api-settings' }
  )
)
