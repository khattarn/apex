import { useState, useEffect } from 'react'
import { Menu } from 'lucide-react'

const ZONES = [
  { label: 'UTC',         short: 'UTC', zone: 'UTC',                  flag: '🌐', color: 'slate'   },
  { label: 'New York',    short: 'NY',  zone: 'America/New_York',    flag: '🇺🇸', color: 'indigo'  },
  { label: 'Chicago',     short: 'CHI', zone: 'America/Chicago',     flag: '🇺🇸', color: 'violet'  },
  { label: 'Los Angeles', short: 'LA',  zone: 'America/Los_Angeles', flag: '🇺🇸', color: 'rose'    },
  { label: 'Toronto',     short: 'TOR', zone: 'America/Toronto',     flag: '🇨🇦', color: 'amber'   },
  { label: 'London',      short: 'LON', zone: 'Europe/London',       flag: '🇬🇧', color: 'emerald' },
  { label: 'Sydney',      short: 'SYD', zone: 'Australia/Sydney',    flag: '🇦🇺', color: 'cyan'    },
]

const PALETTES = {
  slate:   { bg: 'bg-slate-800/60',   border: 'border-slate-500/40',  time: 'text-slate-100',   accent: 'text-slate-400'   },
  indigo:  { bg: 'bg-indigo-950/60',  border: 'border-indigo-500/40',  time: 'text-indigo-200',  accent: 'text-indigo-400'  },
  violet:  { bg: 'bg-violet-950/60',  border: 'border-violet-500/40',  time: 'text-violet-200',  accent: 'text-violet-400'  },
  rose:    { bg: 'bg-rose-950/60',    border: 'border-rose-500/40',    time: 'text-rose-200',    accent: 'text-rose-400'    },
  amber:   { bg: 'bg-amber-950/60',   border: 'border-amber-500/40',   time: 'text-amber-200',   accent: 'text-amber-400'   },
  emerald: { bg: 'bg-emerald-950/60', border: 'border-emerald-500/40', time: 'text-emerald-200', accent: 'text-emerald-400' },
  cyan:    { bg: 'bg-cyan-950/60',    border: 'border-cyan-500/40',    time: 'text-cyan-200',    accent: 'text-cyan-400'    },
}

function ClockCard({ label, short, zone, flag, color }) {
  const [now, setNow] = useState(new Date())
  const p = PALETTES[color]

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  const timeStr = now.toLocaleTimeString('en-US', {
    timeZone: zone, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true,
  })
  const dateStr = now.toLocaleDateString('en-US', {
    timeZone: zone, weekday: 'short', month: 'short', day: 'numeric',
  })
  const tzAbbr = new Intl.DateTimeFormat('en-US', { timeZone: zone, timeZoneName: 'short' })
    .formatToParts(now)
    .find(p => p.type === 'timeZoneName')?.value ?? ''

  const parts = timeStr.split(':')
  const hm   = `${parts[0] ?? ''}:${parts[1] ?? ''}`
  const rest  = (parts[2] ?? '').split(' ')
  const sec   = rest[0] ?? ''
  const ampm  = rest[1] ?? ''

  return (
    <div className={`rounded-lg border ${p.bg} ${p.border} px-2 py-2 flex flex-col items-center`}>
      <p className="text-xs font-semibold text-white/90 tracking-wide truncate w-full text-center">
        {flag} <span className="hidden sm:inline">{label}</span><span className="sm:hidden">{short}</span>
      </p>
      <div className="flex items-baseline gap-0.5 mt-0.5">
        <span className={`font-mono font-bold text-sm sm:text-xl leading-none ${p.time} tracking-tight`}>{hm}</span>
        <span className={`font-mono text-xs leading-none ${p.accent} ml-0.5 hidden sm:inline`}>:{sec}</span>
        <span className={`font-mono text-xs font-semibold text-white/80 ml-0.5`}>{ampm}</span>
      </div>
      <p className="text-[10px] mt-0.5 text-slate-300 font-medium hidden sm:block truncate w-full text-center">
        <span className={`${p.accent} font-semibold`}>{tzAbbr}</span> · {dateStr}
      </p>
    </div>
  )
}

export default function TopBar({ onMenuClick }) {
  return (
    <div className="shrink-0 border-b border-slate-700/50 bg-[#0f172a]/80 backdrop-blur px-3 py-2">
      <div className="flex items-center gap-2">
        <button
          onClick={onMenuClick}
          className="lg:hidden shrink-0 p-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-700/60 transition-colors"
          aria-label="Open menu"
        >
          <Menu size={18} />
        </button>
        <div className="grid grid-cols-4 lg:grid-cols-7 gap-1.5 flex-1">
          {ZONES.map((z) => (
            <ClockCard key={z.zone} {...z} />
          ))}
        </div>
      </div>
    </div>
  )
}
