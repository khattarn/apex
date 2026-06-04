import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Play, Users, Megaphone, Settings, LogOut, Bot, Package, Phone } from 'lucide-react'
import { useState, useEffect } from 'react'

const ZONES = [
  { label: 'New York',    short: 'ET',  zone: 'America/New_York',    flag: '🇺🇸' },
  { label: 'Chicago',     short: 'CT',  zone: 'America/Chicago',     flag: '🇺🇸' },
  { label: 'LA',          short: 'PT',  zone: 'America/Los_Angeles', flag: '🇺🇸' },
  { label: 'Toronto',     short: 'ET',  zone: 'America/Toronto',     flag: '🇨🇦' },
  { label: 'London',      short: 'UK',  zone: 'Europe/London',       flag: '🇬🇧' },
  { label: 'Sydney',      short: 'AET', zone: 'Australia/Sydney',    flag: '🇦🇺' },
]

function WorldClocks() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="mx-2 mb-2 rounded-lg bg-slate-800/60 border border-slate-700/50 p-2">
      <p className="text-slate-500 text-[9px] uppercase tracking-widest text-center mb-1.5 font-medium">World Clocks</p>
      <div className="grid grid-cols-2 gap-1">
        {ZONES.map(({ label, short, zone, flag }) => {
          const time = now.toLocaleTimeString('en-US', {
            timeZone: zone,
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
          })
          const [hm, ampm] = time.split(' ')
          return (
            <div key={zone} className="bg-slate-900/60 rounded-md px-1.5 py-1.5 text-center border border-slate-700/30">
              <p className="text-[9px] text-slate-500 leading-none truncate">{flag} {label}</p>
              <p className="text-indigo-300 font-mono font-semibold leading-none mt-1 text-[11px] tracking-tight">
                {hm}<span className="text-[8px] text-slate-500 ml-0.5">{ampm}</span>
              </p>
              <p className="text-[8px] text-slate-600 mt-0.5">{short}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

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

      <WorldClocks />

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
