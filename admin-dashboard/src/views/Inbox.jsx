import { useEffect, useState, useRef, useMemo } from 'react'
import { MessageSquare, Send, RefreshCw, Search, Users, Megaphone, Phone, Radio } from 'lucide-react'
import { getWaInbox, replyWaInbox, markWaRead, getLeads, getCampaigns } from '../api'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtShort(ts) {
  if (!ts) return '—'
  const d = new Date(ts)
  const diffMs = Date.now() - d.getTime()
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return d.toLocaleDateString('en-GB', { weekday: 'short' })
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

function fmtFull(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

function initials(name) {
  if (!name) return '?'
  return name.split(' ').filter(Boolean).map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

function buildChatMsgs(msgs) {
  const out = []
  msgs.forEach(m => {
    out.push({ type: 'inbound', text: m.message, time: m.received_at, intent: m.intent, id: m.id })
    if (m.reply_sent) {
      out.push({ type: 'outbound', text: m.reply_sent, time: m.received_at, id: m.id + '_r' })
    }
  })
  return out
}

// ─── Atom components ──────────────────────────────────────────────────────────

function Avatar({ name, size = 'md' }) {
  const cls = size === 'sm' ? 'w-9 h-9 text-sm' : 'w-10 h-10 text-base'
  return (
    <div className={`${cls} rounded-full bg-indigo-600 text-white flex items-center justify-center font-semibold shrink-0 select-none`}>
      {initials(name)}
    </div>
  )
}

function NumberBadge({ label }) {
  const cls = label === 'IN'
    ? 'bg-orange-900/50 text-orange-300'
    : 'bg-blue-900/50 text-blue-300'
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${cls}`}>{label}</span>
  )
}

function IntentBadge({ intent }) {
  const map = {
    interested:     'bg-green-900/50 text-green-300',
    question:       'bg-amber-900/50 text-amber-300',
    not_interested: 'bg-red-900/50 text-red-400',
    out_of_office:  'bg-slate-700 text-slate-400',
  }
  if (!intent) return null
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${map[intent] || 'bg-slate-700 text-slate-400'}`}>
      {intent.replace(/_/g, ' ')}
    </span>
  )
}

// ─── Thread list item ─────────────────────────────────────────────────────────

function ThreadItem({ thread, selected, onClick }) {
  const unread = thread.msgs.filter(m => m.status === 'new').length
  const display = thread.name || thread.phone

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-3 border-b border-slate-800/50 transition-colors text-left ${
        selected
          ? 'bg-indigo-900/25 border-l-2 border-l-indigo-500'
          : 'hover:bg-slate-800/30 border-l-2 border-l-transparent'
      }`}
    >
      <Avatar name={display} size="sm" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-1">
          <span className={`text-sm truncate ${unread > 0 ? 'font-semibold text-white' : 'font-medium text-slate-200'}`}>
            {display}
          </span>
          <span className="text-[10px] text-slate-500 shrink-0">{fmtShort(thread.last.received_at)}</span>
        </div>
        <div className="flex items-center justify-between gap-1 mt-0.5">
          <span className="text-xs text-slate-500 truncate">{thread.last.message}</span>
          <div className="flex items-center gap-1 shrink-0">
            <NumberBadge label={thread.last.to_number} />
            {unread > 0 && (
              <span className="bg-indigo-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center leading-none">
                {unread}
              </span>
            )}
          </div>
        </div>
      </div>
    </button>
  )
}

// ─── Message bubble ───────────────────────────────────────────────────────────

function Bubble({ msg }) {
  const isOut = msg.type === 'outbound'
  return (
    <div className={`flex ${isOut ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[72%] rounded-xl px-3 py-2 text-sm shadow-sm ${
        isOut
          ? 'bg-indigo-600 text-white rounded-tr-sm'
          : 'bg-[#1e293b] text-slate-100 border border-slate-700/40 rounded-tl-sm'
      }`}>
        <p className="whitespace-pre-wrap break-words leading-relaxed">{msg.text}</p>
        <div className={`text-[10px] mt-1 flex items-center gap-1.5 ${isOut ? 'text-indigo-200 justify-end' : 'text-slate-500'}`}>
          <span>{fmtFull(msg.time)}</span>
          {!isOut && msg.intent && <IntentBadge intent={msg.intent} />}
        </div>
      </div>
    </div>
  )
}

// ─── Reply box ────────────────────────────────────────────────────────────────

function ReplyBox({ onSend }) {
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const ref = useRef(null)

  useEffect(() => { ref.current?.focus() }, [])

  async function handleSend() {
    const val = text.trim()
    if (!val || sending) return
    setSending(true)
    setError('')
    try {
      await onSend(val)
      setText('')
      if (ref.current) { ref.current.style.height = 'auto' }
    } catch (e) {
      setError(e.message || 'Failed to send')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="shrink-0 px-3 py-3 border-t border-slate-700/40 bg-[#0f172a]">
      {error && <p className="text-xs text-red-400 mb-2">{error}</p>}
      <div className="flex items-end gap-2 bg-[#1e293b] border border-slate-600/40 rounded-xl px-3 py-2">
        <textarea
          ref={ref}
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Type a message…"
          rows={1}
          disabled={sending}
          className="flex-1 bg-transparent border-none outline-none resize-none text-sm text-slate-100 placeholder-slate-500 max-h-28 leading-relaxed"
          onInput={e => {
            e.target.style.height = 'auto'
            e.target.style.height = Math.min(e.target.scrollHeight, 112) + 'px'
          }}
          onKeyDown={e => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); handleSend() }
          }}
        />
        <button
          onClick={handleSend}
          disabled={!text.trim() || sending}
          className="shrink-0 w-8 h-8 rounded-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white flex items-center justify-center transition-colors"
        >
          {sending
            ? <span className="block w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            : <Send size={13} />}
        </button>
      </div>
      <p className="text-[10px] text-slate-600 mt-1.5 text-center">Ctrl+Enter to send · message goes via the number that received it</p>
    </div>
  )
}

// ─── Chat area ────────────────────────────────────────────────────────────────

function ChatArea({ thread, onReply }) {
  const chatMsgs = buildChatMsgs(thread.msgs)
  const last = thread.msgs[thread.msgs.length - 1]
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMsgs.length])

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Chat header */}
      <div className="shrink-0 px-4 py-3 border-b border-slate-700/40 bg-[#1e293b] flex items-center gap-3">
        <Avatar name={thread.name || thread.phone} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-slate-100 text-sm">{thread.name || thread.phone}</span>
            <NumberBadge label={last.to_number} />
            {last.intent && <IntentBadge intent={last.intent} />}
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
            <Phone size={10} className="shrink-0" />
            <span className="font-mono">{thread.phone}</span>
          </div>
        </div>
        <span className="text-[11px] text-slate-500 shrink-0">
          {thread.msgs.length} message{thread.msgs.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2.5">
        {chatMsgs.map(m => <Bubble key={m.id} msg={m} />)}
        <div ref={bottomRef} />
      </div>

      {/* Reply */}
      <ReplyBox onSend={text => onReply(last.id, text)} />
    </div>
  )
}

// ─── Inbox panel (thread list + chat) ────────────────────────────────────────

function InboxPanel({ messages, loading, onReply, onOpenThread }) {
  const [selectedPhone, setSelectedPhone] = useState(null)
  const [filter, setFilter] = useState('all')
  const [searchQ, setSearchQ] = useState('')

  const threads = useMemo(() => {
    const byPhone = {}
    messages.forEach(m => {
      if (!byPhone[m.from_phone]) byPhone[m.from_phone] = []
      byPhone[m.from_phone].push(m)
    })
    return Object.values(byPhone)
      .map(msgs => {
        const sorted = [...msgs].sort((a, b) => new Date(a.received_at) - new Date(b.received_at))
        const last = sorted[sorted.length - 1]
        const name = sorted.find(m => m.lead_name)?.lead_name || null
        const unread = sorted.filter(m => m.status === 'new').length
        return { phone: last.from_phone, name, msgs: sorted, last, unread }
      })
      .sort((a, b) => new Date(b.last.received_at) - new Date(a.last.received_at))
  }, [messages])

  const filtered = useMemo(() => {
    let t = threads
    if (filter === 'unread') t = t.filter(th => th.unread > 0)
    if (filter === 'replied') t = t.filter(th => th.msgs.some(m => m.reply_sent))
    if (searchQ) {
      const q = searchQ.toLowerCase()
      t = t.filter(th => (th.name || th.phone).toLowerCase().includes(q))
    }
    return t
  }, [threads, filter, searchQ])

  const selectedThread = threads.find(t => t.phone === selectedPhone)
  const totalUnread = threads.reduce((s, t) => s + t.unread, 0)

  const filterOpts = [
    { id: 'all', label: totalUnread > 0 ? `All (${totalUnread})` : 'All' },
    { id: 'unread', label: 'Unread' },
    { id: 'replied', label: 'Replied' },
  ]

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left: thread list */}
      <div className="w-72 shrink-0 border-r border-slate-700/40 flex flex-col bg-[#0f172a]">
        {/* Search */}
        <div className="px-2 pt-2 pb-1 shrink-0">
          <div className="flex items-center gap-2 bg-[#1e293b] border border-slate-700/40 rounded-lg px-3 py-1.5">
            <Search size={12} className="text-slate-500 shrink-0" />
            <input
              type="text"
              value={searchQ}
              onChange={e => setSearchQ(e.target.value)}
              placeholder="Search conversations…"
              className="bg-transparent flex-1 text-xs text-slate-200 placeholder-slate-500 outline-none"
            />
          </div>
        </div>

        {/* Filter chips */}
        <div className="flex px-2 pb-2 gap-1 shrink-0">
          {filterOpts.map(f => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`text-[11px] px-2.5 py-0.5 rounded-full transition-colors ${
                filter === f.id
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 border border-slate-700/40'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Thread list */}
        <div className="flex-1 overflow-y-auto">
          {loading && <p className="p-4 text-xs text-slate-500 text-center">Loading…</p>}
          {!loading && filtered.length === 0 && (
            <p className="p-6 text-xs text-slate-500 text-center">No conversations</p>
          )}
          {filtered.map(thread => (
            <ThreadItem
              key={thread.phone}
              thread={thread}
              selected={selectedPhone === thread.phone}
              onClick={() => {
                setSelectedPhone(thread.phone)
                if (thread.unread > 0) onOpenThread(thread)
              }}
            />
          ))}
        </div>
      </div>

      {/* Right: chat */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#0a1020]" style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.015'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")" }}>
        {!selectedThread ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-slate-700">
            <MessageSquare size={48} strokeWidth={1} />
            <p className="text-sm text-slate-500">Select a conversation</p>
          </div>
        ) : (
          <ChatArea key={selectedThread.phone} thread={selectedThread} onReply={onReply} />
        )}
      </div>
    </div>
  )
}

// ─── Contacts panel ───────────────────────────────────────────────────────────

function ContactsPanel() {
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    getLeads({ limit: 100 })
      .then(r => setLeads(r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    if (!search) return leads
    const q = search.toLowerCase()
    return leads.filter(l =>
      (l.name || '').toLowerCase().includes(q) ||
      (l.phone || '').includes(q) ||
      (l.city || '').toLowerCase().includes(q)
    )
  }, [leads, search])

  const statusCls = {
    converted: 'bg-green-900/50 text-green-300',
    replied:   'bg-blue-900/50 text-blue-300',
    contacted: 'bg-indigo-900/50 text-indigo-300',
    dead:      'bg-red-900/50 text-red-400',
    new:       'bg-slate-700 text-slate-400',
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="mb-3 flex items-center gap-3">
        <div className="flex items-center gap-2 bg-[#1e293b] border border-slate-700/40 rounded-lg px-3 py-1.5">
          <Search size={12} className="text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search leads…"
            className="bg-transparent text-xs text-slate-200 placeholder-slate-500 outline-none w-44"
          />
        </div>
        <span className="text-xs text-slate-500">{filtered.length} leads</span>
      </div>

      <div className="bg-[#1e293b] rounded-lg border border-slate-700/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs min-w-[600px]">
            <thead>
              <tr className="border-b border-slate-700/40 text-slate-400">
                {['Name', 'Phone', 'Business Type', 'City', 'Status', 'WA Sent'].map(h => (
                  <th key={h} className="text-left px-4 py-2.5 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">Loading…</td></tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No leads found</td></tr>
              )}
              {filtered.map(l => (
                <tr key={l.id} className="border-b border-slate-800/60 hover:bg-slate-800/20 transition-colors">
                  <td className="px-4 py-2 text-slate-200">{l.name || '—'}</td>
                  <td className="px-4 py-2 font-mono text-slate-300">{l.phone || '—'}</td>
                  <td className="px-4 py-2 capitalize text-slate-300">{l.business_type || '—'}</td>
                  <td className="px-4 py-2 text-slate-300">{l.city || '—'}</td>
                  <td className="px-4 py-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${statusCls[l.status] || statusCls.new}`}>
                      {l.status || 'new'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-slate-400">
                    {l.outreach_sent ? <span className="text-green-400">✓</span> : '—'}
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

// ─── Broadcasts panel ─────────────────────────────────────────────────────────

function BroadcastsPanel() {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCampaigns()
      .then(r => {
        const all = Array.isArray(r) ? r : r?.data || []
        setCampaigns(all.filter(c => c.mode === 'wa_blast').slice(0, 50))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">WA Broadcast History</h3>
          <p className="text-xs text-slate-500 mt-0.5">Campaigns run in WA Blast mode</p>
        </div>
        <a
          href="/pipeline"
          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors border border-indigo-800/50 hover:border-indigo-600 px-3 py-1.5 rounded-lg"
        >
          Run new blast →
        </a>
      </div>

      {loading && <p className="text-xs text-slate-500 text-center py-8">Loading…</p>}
      {!loading && campaigns.length === 0 && (
        <div className="text-center py-12">
          <Radio size={32} className="text-slate-700 mx-auto mb-3" strokeWidth={1} />
          <p className="text-sm text-slate-500">No WA broadcasts yet.</p>
          <p className="text-xs text-slate-600 mt-1">Go to Run Pipeline and choose WA Blast mode.</p>
        </div>
      )}

      <div className="space-y-3">
        {campaigns.map(c => (
          <div key={c.id} className="bg-[#1e293b] rounded-lg border border-slate-700/40 p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium text-slate-200 capitalize">
                  {c.business_type} · {c.city}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-900/50 text-purple-300 font-bold">BLAST</span>
              </div>
              <span className="text-[11px] text-slate-500 shrink-0">
                {new Date(c.created_at).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <div className="flex items-center gap-5 mt-2 text-xs text-slate-400">
              <span>Found <strong className="text-slate-300">{c.prospects_found ?? '—'}</strong></span>
              <span>New leads <strong className="text-slate-300">{c.new_leads ?? '—'}</strong></span>
              <span>Sent <strong className="text-green-400">{c.messages_sent ?? '—'}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function Inbox() {
  const [tab, setTab] = useState('inbox')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      const data = await getWaInbox()
      setMessages(data.messages || [])
    } catch (e) {
      console.error('Inbox load error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleReply(inboxId, text) {
    await replyWaInbox(inboxId, text)
    setMessages(prev =>
      prev.map(m => m.id === inboxId ? { ...m, status: 'replied', reply_sent: text } : m)
    )
  }

  async function handleOpenThread(thread) {
    const unreadIds = thread.msgs.filter(m => m.status === 'new').map(m => m.id)
    setMessages(prev =>
      prev.map(m => unreadIds.includes(m.id) ? { ...m, status: 'read' } : m)
    )
    await Promise.all(unreadIds.map(id => markWaRead(id).catch(() => {})))
  }

  const tabs = [
    { id: 'inbox',      label: 'Inbox',      Icon: MessageSquare },
    { id: 'contacts',   label: 'Contacts',   Icon: Users },
    { id: 'broadcasts', label: 'Broadcasts', Icon: Megaphone },
  ]

  const unread = messages.filter(m => m.status === 'new').length

  return (
    <div className="h-full overflow-hidden flex flex-col">
      {/* Tab bar */}
      <div className="shrink-0 flex items-center border-b border-slate-700/40 bg-[#1e293b] px-2">
        {tabs.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === id
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Icon size={14} />
            {label}
            {id === 'inbox' && unread > 0 && (
              <span className="bg-indigo-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center leading-none">
                {unread}
              </span>
            )}
          </button>
        ))}
        <div className="flex-1" />
        <button
          onClick={load}
          className="p-2 text-slate-500 hover:text-slate-300 hover:bg-slate-700/40 rounded transition-colors mr-1"
          title="Refresh"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Panel content */}
      {tab === 'inbox' && (
        <InboxPanel messages={messages} loading={loading} onReply={handleReply} onOpenThread={handleOpenThread} />
      )}
      {tab === 'contacts' && <ContactsPanel />}
      {tab === 'broadcasts' && <BroadcastsPanel />}
    </div>
  )
}
