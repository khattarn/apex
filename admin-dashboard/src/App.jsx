import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import Login from './views/Login'
import Dashboard from './views/Dashboard'
import RunPipeline from './views/RunPipeline'
import LeadsTable from './views/LeadsTable'
import Campaigns from './views/Campaigns'
import Settings from './views/Settings'
import Agents from './views/Agents'
import AgentDetail from './views/AgentDetail'
import Products from './views/Products'
import ProductDetail from './views/ProductDetail'
import Dialpad from './views/Dialpad'
import LiveActivity from './views/LiveActivity'
import Inbox from './views/Inbox'
import Content from './views/Content'
import VPMarketing from './views/VPMarketing'
import Assets from './views/Assets'
import { getActiveCalls, getWaInbox } from './api'

function LiveCallBanner({ calls }) {
  if (!calls || calls.length === 0) return null
  return (
    <div className="bg-green-900/80 border-b border-green-700/60 px-4 py-1.5 flex items-center gap-3">
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-400"></span>
      </span>
      <span className="text-xs font-medium text-green-200">
        {calls.length === 1
          ? `Aria is on a call — ${calls[0].direction === 'inbound' ? 'Inbound from' : 'Calling'} ${calls[0].lead_name || calls[0].phone}`
          : `${calls.length} active calls in progress`}
      </span>
      <span className="text-xs text-green-500 ml-auto">
        {calls.map(c => c.phone).join(' · ')}
      </span>
    </div>
  )
}

function RouteContent({ activeCalls, onMenuClick, onLogout, sidebarOpen, setSidebarOpen, inboxUnread }) {
  const location = useLocation()
  const isInbox = location.pathname === '/inbox'
  return (
    <>
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onLogout={onLogout} inboxUnread={inboxUnread} />
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}
      <main className="flex-1 flex flex-col overflow-hidden min-w-0">
        <TopBar onMenuClick={onMenuClick} />
        <LiveCallBanner calls={activeCalls} />
        <div className={`flex-1 ${isInbox ? 'overflow-hidden flex flex-col' : 'overflow-y-auto'}`}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/live" element={<LiveActivity />} />
            <Route path="/pipeline" element={<RunPipeline />} />
            <Route path="/leads" element={<LeadsTable />} />
            <Route path="/campaigns" element={<Campaigns />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/agents/:agentId" element={<AgentDetail />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:productId" element={<ProductDetail />} />
            <Route path="/dialpad" element={<Dialpad />} />
            <Route path="/inbox" element={<Inbox />} />
            <Route path="/content" element={<Content />} />
            <Route path="/vp-marketing" element={<VPMarketing />} />
            <Route path="/assets" element={<Assets />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
    </>
  )
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('pd_token'))
  const [activeCalls, setActiveCalls] = useState([])
  const [inboxUnread, setInboxUnread] = useState(0)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    if (!token) return
    const poll = () => getActiveCalls().then(r => setActiveCalls(r?.calls || [])).catch(() => {})
    poll()
    const id = setInterval(poll, 10000)
    return () => clearInterval(id)
  }, [token])

  useEffect(() => {
    if (!token) return
    const poll = () => getWaInbox().then(r => setInboxUnread(r?.unread || 0)).catch(() => {})
    poll()
    const id = setInterval(poll, 30000)
    return () => clearInterval(id)
  }, [token])

  function handleLogin(t) {
    localStorage.setItem('pd_token', t)
    setToken(t)
  }

  function handleLogout() {
    localStorage.removeItem('pd_token')
    setToken(null)
  }

  if (!token) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-[#0f172a] text-white overflow-hidden">
        <RouteContent
          activeCalls={activeCalls}
          onMenuClick={() => setSidebarOpen(true)}
          onLogout={handleLogout}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          inboxUnread={inboxUnread}
        />
      </div>
    </BrowserRouter>
  )
}
