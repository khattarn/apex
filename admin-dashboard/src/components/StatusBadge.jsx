const STYLES = {
  new: 'bg-slate-700 text-slate-300',
  contacted: 'bg-blue-900/60 text-blue-300',
  replied: 'bg-yellow-900/60 text-yellow-300',
  converted: 'bg-green-900/60 text-green-300',
  dead: 'bg-red-900/60 text-red-400',
}

export default function StatusBadge({ status }) {
  const cls = STYLES[status] || 'bg-slate-700 text-slate-400'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium capitalize ${cls}`}>
      {status || 'unknown'}
    </span>
  )
}
