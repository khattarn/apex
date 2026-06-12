import { useEffect, useState, useRef } from 'react'
import { MessageSquare, Send, X, Phone, RefreshCw } from 'lucide-react'
import { getWaInbox, replyWaInbox } from '../api'

function fmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('en-GB', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

function IntentBadge({ intent }) {
  const map = {
    interested:    'bg-green-900/50 text-green-300',
    question:      'bg-amber-900/50 text-amber-300',
    not_interested:'bg-red-900/50 text-red-400',
    out_of_office: 'bg-slate-700 text-slate-400',
  }
  if (!intent) return null
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${map[intent] || 'bg-slate-700 text-slate-400'}`}>
      {intent.replace('_', ' ')}
    </span>
  )
}

function NumberBadge({ number }) {
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${number === 'IN' ? 'bg-orange-900/50 text-orange-300' : 'bg-blue-900/50 text-blue-300'}`}>
      {number}
    </span>
  )
}

function StatusDot({ status }) {
  if (status === 'new') return <span className="inline-block w-2 h-2 rounded-full bg-indigo-400 animate-pulse" title="Unread" />
  if (status === 'replied') return <span className="inline-block w-2 h-2 rounded-full bg-green-500" title="Replied" />
  return <span className="inline-block w-2 h-2 rounded-full bg-slate-600" title="Read" />
}

function ReplyModal({ message, onClose, onSent }) {
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => { textareaRef.current?.focus() }, [])

  async function handleSend() {
    if (!text.trim()) return
    setSending(true)
    setError('')
    try {
      await replyWaInbox(message.id, text.trim())
      onSent()
      onClose()
    } catch (e) {
      setError(e.message || 'Failed to send')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-[#1e293b] border border-slate-700/60 rounded-lg w-full max-w-lg shadow-xl">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/40">
          <div className="flex items-center gap-2">
            <MessageSquare size={14} className="text-indigo-400" />
            <span className="text-sm font-medium">Reply to {message.lead_name || message.from_phone}</span>
            <NumberBadge number={message.to_number} />
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X size={16} />
          </button>
        </div>

        <div className="px-4 py-3 bg-slate-800/40 mx-4 mt-3 rounded text-xs text-slate-400 border border-slate-700/30">
          <p className="text-slate-500 text-[10px] mb-1">Their message:</p>
          {message.message}
        </div>

        <div className="p-4 space-y-3">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            rows={4}
            placeholder="Type your reply..."
            className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-slate-100 placeholder-slate-500 resize-none focus:outline-none focus:border-indigo-500"
            onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) handleSend() }}
          />
          {error && <p className="text-xs text-red-400">{error}</p>}
          <div className="flex justify-end gap-2">
            <button onClick={onClose} className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
              Cancel
            </button>
            <button
              onClick={handleSend}
              disabled={sending || !text.trim()}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium rounded transition-colors"
            >
              <Send size={12} />
              {sending ? 'Sending…' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Inbox() {
  const [messages, setMessages] = useState([])
  const [unread, setUnread] = useState(0)
  const [loading, setLoading] = useState(true)
  const [replyTarget, setReplyTarget] = useState(null)
  const [filter, setFilter] = useState('all')

  async function load() {
    try {
      const data = await getWaInbox()
      setMessages(data.messages || [])
      setUnread(data.unread || 0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const filtered = filter === 'all' ? messages : messages.filter(m => m.status === filter)

  return (
    <div className="p-4 md:p-6 space-y-4">
      {replyTarget && (
        <ReplyModal message={replyTarget} onClose={() => setReplyTarget(null)} onSent={load} />
      )}

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold">WA Inbox</h2>
          {unread > 0 && (
            <span className="bg-indigo-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
              {unread}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="flex text-xs rounded overflow-hidden border border-slate-700/40">
            {['all', 'new', 'replied'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 capitalize transition-colors ${filter === f ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}
              >
                {f}
              </button>
            ))}
          </div>
          <button
            onClick={load}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/60 rounded transition-colors"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[700px]">
            <thead>
              <tr className="border-b border-slate-700/40 text-slate-400 text-xs">
                {['', 'Time', 'From', 'Via', 'Lead', 'Message', 'Intent', 'Status', ''].map((h, i) => (
                  <th key={i} className="text-left px-4 py-2.5 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-slate-500 text-xs">Loading…</td></tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-slate-500 text-xs">No messages yet</td></tr>
              )}
              {filtered.map(m => (
                <tr key={m.id} className={`border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors ${m.status === 'new' ? 'bg-indigo-950/20' : ''}`}>
                  <td className="px-3 py-2.5 w-6"><StatusDot status={m.status} /></td>
                  <td className="px-4 py-2.5 text-xs text-slate-400 whitespace-nowrap">{fmt(m.received_at)}</td>
                  <td className="px-4 py-2.5 text-xs font-mono text-slate-300 whitespace-nowrap">
                    <a href={`tel:${m.from_phone}`} className="flex items-center gap-1 hover:text-indigo-400 transition-colors">
                      <Phone size={10} className="text-slate-500" />
                      {m.from_phone}
                    </a>
                  </td>
                  <td className="px-4 py-2.5"><NumberBadge number={m.to_number} /></td>
                  <td className="px-4 py-2.5 text-xs text-slate-200 whitespace-nowrap">
                    {m.lead_name || <span className="text-slate-500 italic">Unknown</span>}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-slate-300 max-w-[260px]">
                    <span className="line-clamp-2" title={m.message}>{m.message}</span>
                  </td>
                  <td className="px-4 py-2.5"><IntentBadge intent={m.intent} /></td>
                  <td className="px-4 py-2.5 text-xs text-slate-400 capitalize">{m.status}</td>
                  <td className="px-4 py-2.5">
                    {m.status !== 'replied' && (
                      <button
                        onClick={() => setReplyTarget(m)}
                        className="flex items-center gap-1 text-[11px] px-2 py-1 bg-indigo-900/40 hover:bg-indigo-600 text-indigo-300 hover:text-white rounded transition-colors"
                      >
                        <Send size={10} /> Reply
                      </button>
                    )}
                    {m.status === 'replied' && m.reply_sent && (
                      <span className="text-[10px] text-slate-500 italic" title={m.reply_sent}>Replied</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
