export default function FactorBar({ label, value }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-white/75 w-16 flex-shrink-0">{label}</span>
      <div className="flex-1 h-[5px] rounded-full" style={{ background: 'rgba(255,255,255,0.2)' }}>
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, background: '#a5f3fc' }}
        />
      </div>
      <span className="text-[10px] text-white w-7 text-right">{pct}%</span>
    </div>
  )
}
