import { useState } from 'react'
import { Settings, X, Eye, EyeOff, Check, AlertTriangle, Info } from 'lucide-react'
import { useSettingsStore, type ApiSettings } from '@/store/settingsStore'

const PRESETS = [
  { label: 'Socle', baseUrl: 'https://app.socle.ai/api/v1', model: 'qwen3-235b-a22b-instruct-2507' },
  { label: 'Ollama (local)', baseUrl: 'http://host.docker.internal:11434/v1', model: 'llama3.2' },
]


function isSocle(url: string) {
  return url.includes('socle.ai')
}

async function syncAgent(settings: ApiSettings) {
  try {
    await fetch('/api/ai/sync-agent', {
      method: 'POST',
      headers: {
        'x-api-key': settings.apiKey,
        'x-api-base-url': settings.apiBaseUrl,
        'x-api-model': settings.model,
      },
    })
  } catch {
    // non-blocking
  }
}

interface Props {
  open: boolean
  onClose: () => void
  required?: boolean
}

export default function SettingsModal({ open, onClose, required = false }: Props) {
  const { settings, update } = useSettingsStore()
  const [form, setForm] = useState<ApiSettings>({ ...settings })
  const [showKey, setShowKey] = useState(false)
  const [saved, setSaved] = useState(false)
  const [provider, setProvider] = useState<'socle' | 'ollama'>(settings.provider ?? 'socle')

  if (!open) return null

  function applyPreset(p: typeof PRESETS[number]) {
    const prov = p.label === 'Socle' ? 'socle' : 'ollama'
    setProvider(prov)
    setForm((f) => ({ ...f, apiBaseUrl: p.baseUrl, model: p.model, provider: prov }))
  }

  async function save() {
    update({ ...form, provider })
    if (provider === 'socle' && form.apiKey.trim()) {
      syncAgent(form)
    }
    setSaved(true)
    setTimeout(() => {
      setSaved(false)
      onClose()
    }, 800)
  }

  const socle = provider === 'socle'
  const isValid = !socle || Boolean(form.apiKey.trim())
  const canClose = !required || isValid

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="panel w-full max-w-md mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-pax-border">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-pax-accent" />
            <h2 className="text-lg font-semibold text-white">API Configuration</h2>
          </div>
          {canClose && (
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        <div className="p-5 space-y-5">
          {required && !isValid && (
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-3 flex items-start gap-2 text-sm text-yellow-300">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              {isSocle(form.apiBaseUrl)
                ? 'Une clé API Socle est requise pour jouer.'
                : 'Configure le modèle et l\'URL Ollama, puis sauvegarde.'}
            </div>
          )}

          {/* Presets */}
          <div>
            <label className="stat-label block mb-2">Provider</label>
            <div className="grid grid-cols-2 gap-2">
              {PRESETS.map((p) => {
                const prov = p.label === 'Socle' ? 'socle' : 'ollama'
                return (
                  <button
                    key={p.label}
                    onClick={() => applyPreset(p)}
                    className={`text-sm px-3 py-2 rounded-lg border transition-colors text-left ${
                      provider === prov
                        ? 'border-pax-accent bg-pax-accent/10 text-white'
                        : 'border-pax-border text-slate-400 hover:border-slate-500 hover:text-slate-200'
                    }`}
                  >
                    {p.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* API Key */}
          <div>
            <label className="stat-label block mb-1.5">
              API Key {!socle && <span className="text-slate-500 font-normal">(optionnel avec Ollama)</span>}
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={form.apiKey}
                onChange={(e) => setForm((f) => ({ ...f, apiKey: e.target.value }))}
                placeholder={socle ? 'sk-...' : 'ollama (laisser vide)'}
                className="w-full bg-slate-800 border border-pax-border rounded-lg px-3 py-2.5 pr-10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
              />
              <button
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-1">Stockée uniquement dans ton navigateur (localStorage)</p>
          </div>

          {/* Base URL */}
          <div>
            <label className="stat-label block mb-1.5">Base URL</label>
            <input
              type="text"
              value={form.apiBaseUrl}
              onChange={(e) => setForm((f) => ({ ...f, apiBaseUrl: e.target.value }))}
              className="w-full bg-slate-800 border border-pax-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
            />
          </div>

          {/* Model */}
          <div>
            <label className="stat-label block mb-1.5">Modèle</label>
            <input
              type="text"
              value={form.model}
              onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
              placeholder={socle ? 'qwen3-235b-a22b-instruct-2507' : 'llama3.2'}
              className="w-full bg-slate-800 border border-pax-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
            />
            {socle ? (
              <div className="mt-2 flex items-start gap-1.5 text-xs text-slate-400 bg-slate-800/60 border border-pax-border rounded-lg px-3 py-2">
                <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-pax-accent" />
                <span>
                  L'agent <span className="text-white font-medium">MJ Phos</span> sera créé ou mis à jour automatiquement sur ton instance Socle.
                </span>
              </div>
            ) : (
              <div className="mt-2 space-y-1.5">
                <div className="flex items-start gap-1.5 text-xs text-slate-400 bg-slate-800/60 border border-pax-border rounded-lg px-3 py-2">
                  <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-yellow-400" />
                  <span>
                    Recommandé : <span className="text-white font-medium">llama3.2</span>, <span className="text-white font-medium">mistral</span>, <span className="text-white font-medium">qwen2.5</span> (≥ 7B).
                    Les petits modèles peuvent produire du JSON invalide.
                  </span>
                </div>
                <div className="flex items-start gap-1.5 text-xs text-slate-400 bg-slate-800/60 border border-pax-border rounded-lg px-3 py-2">
                  <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-500" />
                  <span>
                    URL depuis Docker : <span className="text-white font-mono text-xs">host.docker.internal:11434</span>.
                    La mémoire de conversation entre tours n'est pas disponible en local (pas de Responses API).
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 pt-0 flex gap-3">
          {canClose && (
            <button onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
          )}
          <button
            onClick={save}
            disabled={!isValid}
            className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {saved ? (
              <><Check className="w-4 h-4" /> Saved</>
            ) : (
              'Save'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
