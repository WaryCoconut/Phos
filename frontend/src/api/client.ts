import axios from 'axios'
import type { GameState, ScenarioSummary, ActionResult, SimEvent, DiplomaticEffect, RegionState, RegionMeta } from '@/types'
import { useSettingsStore } from '@/store/settingsStore'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const { apiKey, apiBaseUrl, model } = useSettingsStore.getState().settings
  if (apiKey) config.headers['x-api-key'] = apiKey
  if (apiBaseUrl) config.headers['x-api-base-url'] = apiBaseUrl
  if (model) config.headers['x-api-model'] = model
  return config
})

function apiHeaders(): Record<string, string> {
  const { apiKey, apiBaseUrl, model } = useSettingsStore.getState().settings
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (apiKey) h['x-api-key'] = apiKey
  if (apiBaseUrl) h['x-api-base-url'] = apiBaseUrl
  if (model) h['x-api-model'] = model
  return h
}

export const scenariosApi = {
  list: (): Promise<ScenarioSummary[]> =>
    api.get('/scenarios/').then((r) => r.data),
  get: (id: string) => api.get(`/scenarios/${id}`).then((r) => r.data),
  create: (data: object) => api.post('/scenarios/', data).then((r) => r.data),
  update: (id: string, data: object) =>
    api.put(`/scenarios/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/scenarios/${id}`).then((r) => r.data),
}

export const gameApi = {
  create: (scenarioId: string, playerCountryId: string) =>
    api
      .post('/game/', { scenario_id: scenarioId, player_country_id: playerCountryId })
      .then((r) => r.data),

  getState: (sessionId: string): Promise<GameState> =>
    api.get(`/game/${sessionId}`).then((r) => r.data),

  submitAction: (sessionId: string, content: string, year: number, month: number): Promise<ActionResult> =>
    api
      .post(`/game/${sessionId}/action`, { content, year, month })
      .then((r) => r.data),

  endTurn: (sessionId: string) =>
    api.post(`/game/${sessionId}/end-turn`).then((r) => r.data),

  listSessions: () => api.get('/game/sessions').then((r) => r.data),

  listSnapshots: (sessionId: string) =>
    api.get(`/game/${sessionId}/snapshots`).then((r) => r.data),

  restoreSnapshot: (sessionId: string, turn: number) =>
    api.post(`/game/${sessionId}/restore/${turn}`).then((r) => r.data),

  deleteSession: (sessionId: string) =>
    api.delete(`/game/${sessionId}`).then((r) => r.data),

  queueAction: (sessionId: string, content: string) =>
    api.post(`/game/${sessionId}/queue`, { content }).then((r) => r.data),

  removeQueuedAction: (sessionId: string, index: number) =>
    api.delete(`/game/${sessionId}/queue/${index}`).then((r) => r.data),
}

export const mapsApi = {
  upload: async (file: File): Promise<{ map_id: string; feature_count: number; available_properties: string[] }> => {
    const { apiKey, apiBaseUrl, model } = useSettingsStore.getState().settings
    const headers: Record<string, string> = {}
    if (apiKey) headers['x-api-key'] = apiKey
    if (apiBaseUrl) headers['x-api-base-url'] = apiBaseUrl
    if (model) headers['x-api-model'] = model
    const form = new FormData()
    form.append('file', file)
    const res = await fetch('/api/maps/upload', { method: 'POST', headers, body: form })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload échoué' }))
      throw new Error(err.detail ?? 'Upload échoué')
    }
    return res.json()
  },
  getUrl: (mapId: string): string => `/api/maps/${mapId}`,
}

export const regionsApi = {
  getMeta: (): Promise<Record<string, RegionMeta>> =>
    api.get('/regions/meta').then((r) => r.data),

  getCountryMeta: (countryId: string): Promise<RegionMeta[]> =>
    api.get(`/regions/meta/${countryId}`).then((r) => r.data),

  getState: (sessionId: string): Promise<RegionState> =>
    api.get(`/regions/${sessionId}`).then((r) => r.data),

  occupy: (sessionId: string, adm1Code: string, occupyingCountryId: string): Promise<RegionState> =>
    api.post(`/regions/${sessionId}/occupy`, {
      adm1_code: adm1Code,
      occupying_country_id: occupyingCountryId,
    }).then((r) => r.data),

  liberate: (sessionId: string, adm1Code: string): Promise<RegionState> =>
    api.delete(`/regions/${sessionId}/occupy/${adm1Code}`).then((r) => r.data),

  declareIndependence: (
    sessionId: string,
    adm1Code: string,
    newCountryName: string,
    flag: string = '🏳️',
  ): Promise<{ new_country_id: string; region_state: RegionState }> =>
    api.post(`/regions/${sessionId}/independence`, {
      adm1_code: adm1Code,
      new_country_name: newCountryName,
      new_country_flag: flag,
    }).then((r) => r.data),

  reunify: (sessionId: string, adm1Code: string): Promise<RegionState> =>
    api.delete(`/regions/${sessionId}/independence/${adm1Code}`).then((r) => r.data),
}

export function streamSimulation(
  sessionId: string,
  months: number,
  onEvent: (event: import('@/types').SimEvent) => void,
  onDone: () => void,
  onError?: (msg: string) => void,
): () => void {
  const ctrl = new AbortController()
  ;(async () => {
    try {
      const res = await fetch(`/api/game/${sessionId}/simulate`, {
        method: 'POST',
        headers: apiHeaders(),
        body: JSON.stringify({ months }),
        signal: ctrl.signal,
      })
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        for (const line of decoder.decode(value).split('\n')) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6)) as SimEvent
            if (event.type === 'done') { onDone(); return }
            if (event.type === 'error') { onError?.(event.message ?? 'Erreur') }
            onEvent(event)
          } catch { /* skip */ }
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') onError?.((e as Error).message)
    }
  })()
  return () => ctrl.abort()
}

async function readSSEStream(
  url: string,
  method: 'GET' | 'POST',
  body: object | null,
  onChunk: (text: string) => void,
  onDone: () => void,
  signal: AbortSignal,
  onError?: (msg: string) => void,
) {
  const res = await fetch(url, {
    method,
    headers: apiHeaders(),
    body: body ? JSON.stringify(body) : undefined,
    signal,
  })
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    for (const line of decoder.decode(value).split('\n')) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.chunk) onChunk(data.chunk)
        if (data.done) onDone()
        if (data.error) {
          onError?.(data.error)
          onDone()
        }
      } catch { /* skip */ }
    }
  }
}

export function streamDiplomacy(
  sessionId: string,
  targetCountryId: string,
  message: string,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError?: (msg: string) => void,
  onGameEffect?: (effect: DiplomaticEffect) => void,
): () => void {
  const ctrl = new AbortController()
  ;(async () => {
    try {
      const res = await fetch(`/api/diplomacy/${sessionId}/message`, {
        method: 'POST',
        headers: apiHeaders(),
        body: JSON.stringify({ target_country_id: targetCountryId, message }),
        signal: ctrl.signal,
      })
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        for (const line of decoder.decode(value).split('\n')) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.chunk) onChunk(data.chunk)
            if (data.error) { onError?.(data.error); onDone(); return }
            if (data.done) {
              if (data.game_effect) onGameEffect?.(data.game_effect as DiplomaticEffect)
              onDone()
              return
            }
          } catch { /* skip */ }
        }
      }
    } catch (e) {
      if (!(e instanceof DOMException && e.name === 'AbortError')) onError?.('Connexion interrompue')
    }
  })().catch(() => {})
  return () => ctrl.abort()
}

export function streamAdvisor(
  sessionId: string,
  question: string,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError?: (msg: string) => void,
): () => void {
  const ctrl = new AbortController()
  readSSEStream(
    `/api/advisor/${sessionId}/ask`,
    'POST',
    { question },
    onChunk, onDone, ctrl.signal, onError,
  ).catch(() => {})
  return () => ctrl.abort()
}

export function streamBriefing(
  sessionId: string,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError?: (msg: string) => void,
): () => void {
  const ctrl = new AbortController()
  readSSEStream(
    `/api/advisor/${sessionId}/briefing`,
    'GET',
    null,
    onChunk, onDone, ctrl.signal, onError,
  ).catch(() => {})
  return () => ctrl.abort()
}
