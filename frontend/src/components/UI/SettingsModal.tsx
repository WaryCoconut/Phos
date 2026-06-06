import { useState } from 'react'
import { Settings, X, Eye, EyeOff, Check, AlertTriangle } from 'lucide-react'
import { useSettingsStore, type ApiSettings } from '@/store/settingsStore'

const PRESETS = [
  { label: 'socle.ai', baseUrl: 'https://app.socle.ai/api/v1', model: 'qwen3-235b-a22b-instruct-2507' },
  { label: 'Ollama (local)', baseUrl: 'http://localhost:11434/v1', model: 'llama3' },
]

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

  if (!open) return null

  function applyPreset(baseUrl: string, model: string) {
    setForm((f) => ({ ...f, apiBaseUrl: baseUrl, model }))
  }

  function save() {
    update(form)
    setSaved(true)
    setTimeout(() => {
      setSaved(false)
      if (form.apiKey.trim()) onClose()
    }, 800)
  }

  const canClose = !required || Boolean(settings.apiKey.trim())

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="panel w-full max-w-md mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-pax-border">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-pax-accent" />
            <h2 className="text-lg font-semibold text-white">Configuration API</h2>
          </div>
          {canClose && (
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        <div className="p-5 space-y-5">
          {required && !settings.apiKey.trim() && (
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-3 flex items-start gap-2 text-sm text-yellow-300">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              Une clé API est requise pour jouer. Entrez votre clé socle.ai ou toute API compatible OpenAI.
            </div>
          )}

          {/* Presets */}
          <div>
            <label className="stat-label block mb-2">Fournisseur</label>
            <div className="grid grid-cols-2 gap-2">
              {PRESETS.map((p) => (
                <button
                  key={p.label}
                  onClick={() => applyPreset(p.baseUrl, p.model)}
                  className={`text-sm px-3 py-2 rounded-lg border transition-colors text-left ${
                    form.apiBaseUrl === p.baseUrl
                      ? 'border-pax-accent bg-pax-accent/10 text-white'
                      : 'border-pax-border text-slate-400 hover:border-slate-500 hover:text-slate-200'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* API Key */}
          <div>
            <label className="stat-label block mb-1.5">Clé API</label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={form.apiKey}
                onChange={(e) => setForm((f) => ({ ...f, apiKey: e.target.value }))}
                placeholder="sk-..."
                className="w-full bg-slate-800 border border-pax-border rounded-lg px-3 py-2.5 pr-10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
              />
              <button
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-1">Stockée uniquement dans votre navigateur (localStorage)</p>
          </div>

          {/* Base URL */}
          <div>
            <label className="stat-label block mb-1.5">URL de base</label>
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
              placeholder="gpt-4o"
              className="w-full bg-slate-800 border border-pax-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pax-accent"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 pt-0 flex gap-3">
          {canClose && (
            <button onClick={onClose} className="btn-secondary flex-1">
              Annuler
            </button>
          )}
          <button
            onClick={save}
            disabled={!form.apiKey.trim()}
            className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {saved ? (
              <><Check className="w-4 h-4" /> Sauvegardé</>
            ) : (
              'Sauvegarder'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
