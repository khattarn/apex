import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, RefreshCw, Save, Send, Mail } from 'lucide-react'
import { getSetting, putSetting, getHealth, clearAllLeads, resetOutreach, getTemplateStatuses, submitTemplates, previewEmail } from '../api'

const STATUS_STYLES = {
  APPROVED:      'bg-green-900/50 text-green-400 border-green-700/50',
  PENDING:       'bg-yellow-900/50 text-yellow-400 border-yellow-700/50',
  REJECTED:      'bg-red-900/50 text-red-400 border-red-700/50',
  NOT_SUBMITTED: 'bg-slate-800 text-slate-400 border-slate-600/50',
  ALREADY_EXISTS:'bg-green-900/50 text-green-400 border-green-700/50',
  UNKNOWN:       'bg-slate-800 text-slate-400 border-slate-600/50',
}

function TemplateStatusBadge({ status }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.UNKNOWN
  const label = status === 'NOT_SUBMITTED' ? 'Not Submitted' : status.replace(/_/g, ' ')
  return (
    <span className={`text-xs border px-2 py-0.5 rounded-full font-medium ${style}`}>
      {label}
    </span>
  )
}

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

  const [templates, setTemplates] = useState([])
  const [loadingTemplates, setLoadingTemplates] = useState(false)
  const [templatesError, setTemplatesError] = useState(null)
  const [submittingTemplate, setSubmittingTemplate] = useState(null) // name or 'all'
  const [templateSubmitMsg, setTemplateSubmitMsg] = useState(null)

  const [emailPreview, setEmailPreview] = useState(null)
  const [emailPreviewLoading, setEmailPreviewLoading] = useState(false)
  const [emailPreviewNum, setEmailPreviewNum] = useState(1)
  const [emailPreviewMarket, setEmailPreviewMarket] = useState('CA')

  useEffect(() => {
    getSetting('whatsapp_prompt_template')
      .then(({ value }) => { setTemplate(value); setSavedTemplate(value) })
      .catch(() => {})

    checkHealth()
    loadTemplates()
    loadEmailPreview(1, 'CA')
  }, [])

  async function loadEmailPreview(num, market) {
    setEmailPreviewLoading(true)
    setEmailPreview(null)
    try {
      const data = await previewEmail(num, 'dentist', market)
      setEmailPreview(data)
    } catch {
      setEmailPreview(null)
    } finally {
      setEmailPreviewLoading(false)
    }
  }

  function handlePreviewChange(num, market) {
    setEmailPreviewNum(num)
    setEmailPreviewMarket(market)
    loadEmailPreview(num, market)
  }

  async function loadTemplates() {
    setLoadingTemplates(true)
    setTemplatesError(null)
    try {
      const data = await getTemplateStatuses()
      setTemplates(data)
    } catch (e) {
      setTemplatesError(e.message)
      setTemplates([])
    } finally {
      setLoadingTemplates(false)
    }
  }

  async function handleSubmitTemplate(name) {
    setSubmittingTemplate(name)
    setTemplateSubmitMsg(null)
    try {
      await submitTemplates(name)
      setTemplateSubmitMsg({ ok: true, text: name === 'all' ? 'All templates submitted to Meta' : 'Template submitted to Meta' })
      await loadTemplates()
    } catch (e) {
      setTemplateSubmitMsg({ ok: false, text: e.message })
    } finally {
      setSubmittingTemplate(null)
    }
  }

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

      {/* WA Templates */}
      <section className="bg-[#1e293b] rounded-lg border border-slate-700/40 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">WhatsApp Message Templates</p>
            <p className="text-xs text-slate-500 mt-0.5">Submitted to Meta for approval. Required for cold outreach.</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadTemplates}
              disabled={loadingTemplates}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            >
              <RefreshCw size={12} className={loadingTemplates ? 'animate-spin' : ''} />
              Refresh
            </button>
            <button
              onClick={() => handleSubmitTemplate('all')}
              disabled={submittingTemplate !== null}
              className="flex items-center gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-3 py-1.5 rounded transition-colors"
            >
              <Send size={11} />
              {submittingTemplate === 'all' ? 'Submitting…' : 'Submit All'}
            </button>
          </div>
        </div>

        {templateSubmitMsg && (
          <p className={`text-xs ${templateSubmitMsg.ok ? 'text-green-400' : 'text-red-400'}`}>
            {templateSubmitMsg.text}
          </p>
        )}

        <div className="space-y-2">
          {loadingTemplates && (
            <p className="text-xs text-slate-500">Loading…</p>
          )}
          {templatesError && (
            <p className="text-xs text-red-400">Error: {templatesError}</p>
          )}
          {!loadingTemplates && templates.map((t) => (
            <div key={t.name} className="flex items-center justify-between py-1.5 border-b border-slate-700/30 last:border-0">
              <div className="flex flex-col gap-0.5">
                <span className="text-sm text-slate-200">{t.display_name}</span>
                <span className="text-xs text-slate-500 font-mono">{t.name}</span>
              </div>
              <div className="flex items-center gap-3">
                {t.rejected_reason && (
                  <span className="text-xs text-red-400 max-w-[160px] truncate" title={t.rejected_reason}>
                    {t.rejected_reason}
                  </span>
                )}
                <TemplateStatusBadge status={t.status} />
                {(t.status === 'NOT_SUBMITTED' || t.status === 'REJECTED') && (
                  <button
                    onClick={() => handleSubmitTemplate(t.name)}
                    disabled={submittingTemplate !== null}
                    className="text-xs bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-300 px-2 py-1 rounded transition-colors"
                  >
                    {submittingTemplate === t.name ? 'Submitting…' : 'Submit'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Email template preview */}
      <section className="bg-[#1e293b] rounded-lg border border-slate-700/40 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium flex items-center gap-2"><Mail size={14} className="text-indigo-400" /> Email Templates — Dentist Preview</p>
            <p className="text-xs text-slate-500 mt-0.5">Rendered with sample data (Sunrise Dental). Tracking pixel + footer included.</p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 flex-wrap">
          <div>
            <label className="text-xs text-slate-500 block mb-1">Email</label>
            <select
              value={emailPreviewNum}
              onChange={e => handlePreviewChange(Number(e.target.value), emailPreviewMarket)}
              className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              <option value={1}>Email 1 — Day 1 (AU/US)</option>
              <option value={2}>Email 2 — Review pain (Day 1)</option>
              <option value={3}>Email 3 — Day 3 follow-up</option>
              <option value={4}>Email 4 — Day 6 social proof</option>
              <option value={5}>Email 5 — Day 9 objections</option>
              <option value={6}>Email 6 — Day 1 (Canada CDCP)</option>
              <option value={7}>Email 7 — Day 12 break-up</option>
              <option value={8}>Email 8 — Day 42 re-engage</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Market</label>
            <select
              value={emailPreviewMarket}
              onChange={e => handlePreviewChange(emailPreviewNum, e.target.value)}
              className="bg-slate-800 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="CA">Canada (CA)</option>
              <option value="US">United States (US)</option>
              <option value="AU">Australia (AU)</option>
            </select>
          </div>
        </div>

        {/* Subject line */}
        {emailPreview && (
          <div className="bg-slate-800/60 border border-slate-700/40 rounded px-3 py-2">
            <span className="text-xs text-slate-500">Subject: </span>
            <span className="text-sm text-white">{emailPreview.subject}</span>
            <span className="ml-2 text-xs text-slate-600">variant {emailPreview.variant}</span>
          </div>
        )}

        {/* HTML preview */}
        {emailPreviewLoading && (
          <div className="h-64 flex items-center justify-center">
            <p className="text-xs text-slate-500">Rendering…</p>
          </div>
        )}
        {!emailPreviewLoading && emailPreview && (
          <div className="rounded-lg overflow-hidden border border-slate-700/40">
            <iframe
              srcDoc={emailPreview.html}
              title="Email preview"
              className="w-full bg-white"
              style={{ height: '520px', border: 'none' }}
              sandbox="allow-same-origin"
            />
          </div>
        )}
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
