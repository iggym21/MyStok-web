function fmt(label, value) {
  if (value === null || value === undefined) return '—'
  if (label === 'Market Cap') {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`
    if (value >= 1e9)  return `$${(value / 1e9).toFixed(1)}B`
    if (value >= 1e6)  return `$${(value / 1e6).toFixed(1)}M`
    return `$${value}`
  }
  if (label === 'Dividend Yield') return `${(value * 100).toFixed(2)}%`
  if (label === 'P/E Ratio') return value.toFixed(1)
  if (label === '52-Week High') return `$${value.toFixed(2)}`
  if (label === '52-Week Low')  return `$${value.toFixed(2)}`
  return value
}

export default function FundamentalsGrid({ stock }) {
  const cells = [
    { label: 'Market Cap',     value: stock.market_cap },
    { label: 'P/E Ratio',      value: stock.pe_ratio },
    { label: 'Dividend Yield', value: stock.dividend_yield },
    { label: '52-Week High',   value: stock.week52_high },
    { label: '52-Week Low',    value: stock.week52_low },
    { label: 'Industry',       value: stock.industry },
  ]

  return (
    <div
      className="rounded-2xl p-4"
      style={{
        background: 'rgba(255,255,255,0.15)',
        border: '1px solid rgba(255,255,255,0.25)',
      }}
    >
      <p className="text-white/60 text-[10px] font-bold uppercase tracking-widest mb-3">
        Fundamentals
      </p>
      <div className="grid grid-cols-2 gap-3">
        {cells.map(({ label, value }) => (
          <div key={label}>
            <div className="text-white/55 text-[10px]">{label}</div>
            <div className="text-white font-bold text-base mt-0.5">
              {fmt(label, value)}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
