import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
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

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('pd_token'))

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
        <Sidebar onLogout={handleLogout} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/pipeline" element={<RunPipeline />} />
            <Route path="/leads" element={<LeadsTable />} />
            <Route path="/campaigns" element={<Campaigns />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/agents/:agentId" element={<AgentDetail />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:productId" element={<ProductDetail />} />
            <Route path="/dialpad" element={<Dialpad />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
