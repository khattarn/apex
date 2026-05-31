import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, RefreshCw, Save } from 'lucide-react'
import { getSetting, putSetting, getHealth, clearAllLeads, resetOutreach } from '../api'

function HealthDot({ ok }) {
  if (ok === undefined) return <span className="w-2 h-2 rounded-full bg-slate-600 inline-block" />
  return ok
    ? <CheckCircle size={14} className="text-green-400 inline" />
    : <XCircle size={14} className="text-red-400 inline" />
}

export default function Settings() {
  const [template, setTemplate] = useState('')
  const [savedTemplate, setSavedTemplate] = useState('')
  const [savingTemplate, setSavingTemplate] = useState(false)
  const [templateMsg, setTemplateMsg] = useState(null)

  const [health, setHealth] = useState({})
  const [checkingHealth, setCheckingHealth] = useState(false)

  useEffect(() => {
    getSetting('whatsapp_prompt_template')
      .then(({ value }) => { setTemplate(value); setSavedTemplate(value) })
      .catch(() => {})

    checkHealth()
  }, [])

  async function checkHealth() {
    setCheckingHealth(true)
    setHealth({})
    try {
      const h = await getHealth()
      setHealth(h)
    } catch {
      setHealth({})
    } finally {
      setCheckingHealth(false)
    }
  }

  async function saveTemplate() {
    setSavingTemplate(true)
    setTemplateMsg(null)
    try {
      await putSetting('whatsapp_prompt_template', template)
      setSavedTemplate(template)
      setTemplateMsg({ ok: true, text: 'Saved' })
    } catch (e) {
      setTemplateMsg({ ok: false, text: e.message })
    } finally {
      setSavingTemplate(false)
    }
  }

  async function handleClearLeads() {
    if (!confirm('Delete ALL leads? This cannot be undone.')) return
    if (!confirm('Are you absolutely sure?')) return
    try {
      await clearAllLeads()
      alert('All leads cleared.')
    } catch (e) {
      alert(`Failed: ${e.message}`)
    }
  }

  async function handleResetOutreach() {
    if (!confirm('Reset outreach flags for all leads? Status will be set back to "new".')) return
    try {
      await resetOutreach()
      alert('Outreach flags reset.')
    } catch (e) {
      alert(`Failed: ${e.message}`)
    }
  }

  const API_KEYS = [
    { key: 'google_maps', label: 'Google Maps' },
    { key: 'anthropic', label: 'Anthropic (Claude)' },
    { key: 'whatsapp', label: 'WhatsApp Cloud API' },
    { key: 'supabase', label: 'Supabase' },
  ]

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <h2 className="text-base font-semibold">Settings</h2>

      {/* Message template */}
      <section className="bg-[#1e293b] rounded-lg border border-slate-700/40 p-5 space-y-4">
        <div>
          <p className="text-sm font-medium">Outreach Message Template</p>
          <p className="text-xs text-slate-500 mt-0.5">
            Used by the personalizer agent. Supports <code className="text-indigo-400">&#123;name&#125;</code>,{' '}
            <code className="text-indigo-400">&#123;business_type&#125;</code>,{' '}
            <code className="text-indigo-400">&#123;city&#125;</code>.
          </p>
        </div>
        <textarea
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
          rows={6}
          className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white font-mono placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none leading-5"
        />
        <div className="flex items-center gap-3">
          <button
            onClick={saveTemplate}
            disabled={savingTemplate || template === savedTemplate}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded transition-colors"
          >
            <Save size={13} />
            {savingTemplate ? 'Saving…' : 'Save'}
          </button>
          {templateMsg && (
            <p className={`text-xs ${templateMsg.ok ? 'text-green-400' : 'text-red-400'}`}>
              {templateMsg.text}
            </p>
          )}
        </div>
      </section>

      {/* API key status */}
      <section className="bg-[#1e293b] rounded-lg border border-slate-700/40 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">API Keys Status</p>
          <button
            onClick={checkHealth}
            disabled={checkingHealth}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw size={12} className={checkingHealth ? 'animate-spin' : ''} />
            {checkingHealth ? 'Checking…' : 'Test Connections'}
          </button>
        </div>
        <div className="space-y-2">
          {API_KEYS.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-slate-300">{label}</span>
              <div className="flex items-center gap-2">
                <HealthDot ok={health[key]} />
                <span className="text-xs text-slate-500">
                  {health[key] === undefined ? '—' : health[key] ? 'OK' : 'Missing / Error'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Danger zone */}
      <section className="bg-[#1e293b] rounded-lg border border-red-900/40 p-5 space-y-4">
        <p className="text-sm font-medium text-red-400">Danger Zone</p>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">Clear all leads</p>
              <p className="text-xs text-slate-500">Permanently deletes every lead from the database</p>
            </div>
            <button
              onClick={handleClearLeads}
              className="text-xs bg-red-900/50 hover:bg-red-800 border border-red-700/50 text-red-300 px-3 py-1.5 rounded transition-colors"
            >
              Clear Leads
            </button>
          </div>
          <div className="border-t border-slate-700/40 pt-3 flex items-center justify-between">
            <div>
              <p className="text-sm">Reset outreach flags</p>
              <p className="text-xs text-slate-500">
                Sets <code className="text-indigo-400">outreach_sent = false</code> for all leads — useful after testing
              </p>
            </div>
            <button
              onClick={handleResetOutreach}
              className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1.5 rounded transition-colors"
            >
              Reset Flags
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
