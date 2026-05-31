const COLOR_MAP = {
  default: 'text-white',
  blue: 'text-blue-400',
  yellow: 'text-yellow-400',
  green: 'text-green-400',
  red: 'text-red-400',
}

export default function StatCard({ label, value, icon: Icon, color = 'default', sub }) {
  return (
    <div className="bg-[#1e293b] rounded-lg p-4 border border-slate-700/40">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">{label}</p>
        {Icon && <Icon size={15} className={COLOR_MAP[color]} strokeWidth={1.75} />}
      </div>
      <p className={`text-2xl font-semibold ${COLOR_MAP[color]}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}
