import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { getStock } from '../api.js'
import FundamentalsGrid from '../components/FundamentalsGrid.jsx'
import FactorBar from '../components/FactorBar.jsx'

export default function DetailPage() {
  const { ticker } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const stock = location.state?.stock ?? null

  const [fundamentals, setFundamentals] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getStock(ticker)
      .then(setFundamentals)
      .catch(() => setError('Could not load fundamentals.'))
  }, [ticker])

  return (
    <div className="py-4">
      {/* Back nav */}
      <button
        onClick={() => navigate(-1)}
        className="text-white/60 text-xs mb-5 hover:text-white/90 transition-colors"
      >
        ← Back to results
      </button>

      {/* Stock header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-white font-black text-4xl tracking-tight">{ticker}</h2>
          <p className="text-white/65 text-sm mt-1">
            {fundamentals?.company_name ?? stock?.company_name ?? ''}
            {fundamentals?.sector ? ` · ${fundamentals.sector}` : ''}
          </p>
          {fundamentals?.country && (
            <p className="text-white/45 text-xs mt-0.5">{fundamentals.country}</p>
          )}
        </div>
        {stock && (
          <div
            className="text-center px-4 py-3 rounded-xl"
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: '1px solid rgba(255,255,255,0.3)',
            }}
          >
            <div className="text-white font-extrabold text-2xl leading-none">
              {Math.round(stock.score * 100)}%
            </div>
            <div className="text-white/65 text-[9px] uppercase tracking-widest mt-1">Match</div>
          </div>
        )}
      </div>

      {/* Fundamentals */}
      {error && <p className="text-red-300 text-sm mb-4">{error}</p>}
      {fundamentals ? (
        <FundamentalsGrid stock={fundamentals} />
      ) : !error ? (
        <div
          className="rounded-2xl p-4 animate-pulse"
          style={{ background: 'rgba(255,255,255,0.12)', height: '160px' }}
        />
      ) : null}

      {/* Score breakdown */}
      {stock && (
        <div
          className="rounded-2xl p-4 mt-4"
          style={{
            background: 'rgba(255,255,255,0.12)',
            border: '1px solid rgba(255,255,255,0.20)',
          }}
        >
          <p className="text-white/60 text-[10px] font-bold uppercase tracking-widest mb-3">
            Score Breakdown
          </p>
          <div className="flex flex-col gap-2">
            <FactorBar label="Momentum" value={stock.momentum} />
            <FactorBar label="Stability" value={stock.stability} />
            <FactorBar label="Income"   value={stock.income} />
            <FactorBar label="Value"    value={stock.value} />
            <FactorBar label="Size"     value={stock.size} />
          </div>
        </div>
      )}
    </div>
  )
}
