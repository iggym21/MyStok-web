import { useNavigate } from 'react-router-dom'
import FactorBar from './FactorBar.jsx'

export default function StockCard({ stock, rank }) {
  const navigate = useNavigate()
  const isTop = rank === 1
  const bgAlpha = isTop ? '0.20' : '0.12'
  const borderAlpha = isTop ? '0.35' : '0.20'

  function handleClick() {
    navigate(`/stocks/${stock.ticker}`, { state: { stock } })
  }

  return (
    <div
      onClick={handleClick}
      className="rounded-2xl p-4 cursor-pointer"
      style={{
        background: `rgba(255,255,255,${bgAlpha})`,
        border: `1px solid rgba(255,255,255,${borderAlpha})`,
      }}
    >
      {/* Header row */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2">
          <span
            className="text-white text-[9px] font-bold px-2 py-0.5 rounded-full"
            style={{ background: 'rgba(255,255,255,0.25)' }}
          >
            #{rank}
          </span>
          <span className="text-white font-extrabold text-lg">{stock.ticker}</span>
          <span className="text-white/65 text-xs">{stock.company_name}</span>
        </div>
        <div className="text-right">
          <div className="text-white font-extrabold text-xl leading-none">
            {Math.round(stock.score * 100)}%
          </div>
          <div className="text-white/55 text-[9px]">match score</div>
        </div>
      </div>

      {/* Factor bars */}
      <div className="flex flex-col gap-1.5">
        <FactorBar label="Momentum" value={stock.momentum} />
        <FactorBar label="Stability" value={stock.stability} />
        <FactorBar label="Income"   value={stock.income} />
        <FactorBar label="Value"    value={stock.value} />
        <FactorBar label="Size"     value={stock.size} />
      </div>

      <div className="mt-2 text-right text-white/40 text-[10px]">
        Tap for full details →
      </div>
    </div>
  )
}
