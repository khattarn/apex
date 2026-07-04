import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Play, Users, Megaphone, Settings, LogOut, Bot, Package, Phone, X, Radio, Inbox, Wand2, TrendingUp, Archive, Instagram, Map, PhoneCall, Crown } from 'lucide-react'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/live', icon: Radio, label: 'Live Activity' },
  { to: '/pipeline', icon: Play, label: 'Run Pipeline' },
  { to: '/leads', icon: Users, label: 'Leads' },
  { to: '/campaigns', icon: Megaphone, label: 'Campaigns' },
  { to: '/call-sessions', icon: PhoneCall, label: 'Call Sessions' },
  { to: '/ceo-report', icon: Crown, label: 'CEO Report' },
  { to: '/inbox', icon: Inbox, label: 'WA Inbox' },
  { to: '/vp-marketing', icon: TrendingUp, label: 'VP Marketing' },
  { to: '/content', icon: Wand2, label: 'Content' },
  { to: '/affiliates', icon: Instagram, label: 'Affiliates' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/products', icon: Package, label: 'Products' },
  { to: '/dialpad', icon: Phone, label: 'Dialpad' },
  { to: '/assets', icon: Archive, label: 'Assets' },
  { to: '/mandate', icon: Map, label: 'Mandate' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar({ isOpen, onClose, onLogout, inboxUnread = 0 }) {
  return (
    <aside className={`
      fixed lg:static inset-y-0 left-0 z-40
      w-52 shrink-0 bg-[#1e293b] flex flex-col h-full border-r border-slate-700/50
      transition-transform duration-200 ease-in-out
      ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
    `}>
      <div className="px-4 py-5 border-b border-slate-700/50 flex items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="text-indigo-400 font-semibold text-sm tracking-widest uppercase truncate">PracticeDesk</p>
          <p className="text-slate-500 text-xs mt-0.5">Outreach Console</p>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden shrink-0 p-1 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-700/60 transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:bg-slate-700/60 hover:text-slate-100'
              }`
            }
          >
            <Icon size={15} strokeWidth={1.75} />
            <span className="flex-1">{label}</span>
            {to === '/inbox' && inboxUnread > 0 && (
              <span className="bg-indigo-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                {inboxUnread}
              </span>
            )}
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
