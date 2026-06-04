import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Play, Users, Megaphone, Settings, LogOut, Bot, Package, Phone } from 'lucide-react'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/pipeline', icon: Play, label: 'Run Pipeline' },
  { to: '/leads', icon: Users, label: 'Leads' },
  { to: '/campaigns', icon: Megaphone, label: 'Campaigns' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/products', icon: Package, label: 'Products' },
  { to: '/dialpad', icon: Phone, label: 'Dialpad' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar({ onLogout }) {
  return (
    <aside className="w-52 shrink-0 bg-[#1e293b] flex flex-col h-full border-r border-slate-700/50">
      <div className="px-4 py-5 border-b border-slate-700/50">
        <p className="text-indigo-400 font-semibold text-sm tracking-widest uppercase">PracticeDesk</p>
        <p className="text-slate-500 text-xs mt-0.5">Outreach Console</p>
      </div>

      <nav className="flex-1 p-2 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:bg-slate-700/60 hover:text-slate-100'
              }`
            }
          >
            <Icon size={15} strokeWidth={1.75} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-2 border-t border-slate-700/50">
        <button
          onClick={onLogout}
          className="flex items-center gap-3 w-full px-3 py-2 rounded text-sm text-slate-500 hover:bg-slate-700/60 hover:text-slate-200 transition-colors"
        >
          <LogOut size={15} strokeWidth={1.75} />
          Logout
        </button>
      </div>
    </aside>
  )
}
