import { useState, useEffect } from 'react'

const ZONES = [
  { label: 'New York',  short: 'ET',  zone: 'America/New_York',    flag: '🇺🇸', color: 'indigo'  },
  { label: 'Chicago',   short: 'CT',  zone: 'America/Chicago',     flag: '🇺🇸', color: 'violet'  },
  { label: 'Los Angeles', short: 'PT', zone: 'America/Los_Angeles', flag: '🇺🇸', color: 'rose'    },
  { label: 'Toronto',   short: 'ET',  zone: 'America/Toronto',     flag: '🇨🇦', color: 'amber'   },
  { label: 'London',    short: 'GMT', zone: 'Europe/London',       flag: '🇬🇧', color: 'emerald' },
  { label: 'Sydney',    short: 'AET', zone: 'Australia/Sydney',    flag: '🇦🇺', color: 'cyan'    },
]

const PALETTES = {
  indigo:  { bg: 'bg-indigo-950/60',  border: 'border-indigo-500/30',  time: 'text-indigo-200',  label: 'text-indigo-400/70',  ampm: 'text-indigo-400/50'  },
  violet:  { bg: 'bg-violet-950/60',  border: 'border-violet-500/30',  time: 'text-violet-200',  label: 'text-violet-400/70',  ampm: 'text-violet-400/50'  },
  rose:    { bg: 'bg-rose-950/60',    border: 'border-rose-500/30',    time: 'text-rose-200',    label: 'text-rose-400/70',    ampm: 'text-rose-400/50'    },
  amber:   { bg: 'bg-amber-950/60',   border: 'border-amber-500/30',   time: 'text-amber-200',   label: 'text-amber-400/70',   ampm: 'text-amber-400/50'   },
  emerald: { bg: 'bg-emerald-950/60', border: 'border-emerald-500/30', time: 'text-emerald-200', label: 'text-emerald-400/70', ampm: 'text-emerald-400/50' },
  cyan:    { bg: 'bg-cyan-950/60',    border: 'border-cyan-500/30',    time: 'text-cyan-200',    label: 'text-cyan-400/70',    ampm: 'text-cyan-400/50'    },
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

  // split "09:41:05 AM" → hm = "09:41", sec = "05", ampm = "AM"
  const parts = timeStr.split(':')
  const hm   = `${parts[0]}:${parts[1]}`
  const rest  = parts[2].split(' ')
  const sec   = rest[0]
  const ampm  = rest[1]

  return (
    <div className={`flex-1 min-w-0 rounded-lg border ${p.bg} ${p.border} px-3 py-2 flex flex-col items-center`}>
      <p className={`text-[10px] font-medium tracking-wide ${p.label} whitespace-nowrap`}>
        {flag} {label}
      </p>
      <div className="flex items-baseline gap-0.5 mt-0.5">
        <span className={`font-mono font-bold text-xl leading-none ${p.time} tracking-tight`}>{hm}</span>
        <span className={`font-mono text-xs leading-none ${p.ampm} ml-0.5`}>:{sec}</span>
        <span className={`font-mono text-xs leading-none ${p.ampm} ml-1`}>{ampm}</span>
      </div>
      <p className={`text-[9px] mt-0.5 ${p.ampm} tracking-widest`}>{dateStr}</p>
    </div>
  )
}

export default function TopBar() {
  return (
    <div className="shrink-0 border-b border-slate-700/50 bg-[#0f172a]/80 backdrop-blur px-4 py-2">
      <div className="flex gap-2">
        {ZONES.map((z) => (
          <ClockCard key={z.zone} {...z} />
        ))}
      </div>
    </div>
  )
}
