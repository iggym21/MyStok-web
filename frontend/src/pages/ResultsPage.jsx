import { useLocation, useNavigate, Navigate } from 'react-router-dom'
import StockCard from '../components/StockCard.jsx'
import CertaintyBadge from '../components/CertaintyBadge.jsx'

const RISK_LABELS = {
  1: 'Conservative', 2: 'Cautious', 3: 'Moderate', 4: 'Growth', 5: 'Aggressive',
}

const DURATION_LABELS = { short: 'Short-term', medium: 'Medium-term', long: 'Long-term' }

export default function ResultsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state

  if (!state?.data) return <Navigate to="/" replace />

  const { data, sector, risk, duration } = state

  return (
    <div className="py-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-white font-extrabold text-2xl leading-tight">{sector}</h2>
          <p className="text-white/65 text-xs mt-1">
            {data.stocks_evaluated} stocks evaluated ·{' '}
            {RISK_LABELS[risk]} · {DURATION_LABELS[duration]}
          </p>
        </div>
        <CertaintyBadge certainty={data.certainty} />
      </div>

      {/* Stock cards */}
      <div className="flex flex-col gap-3">
        {data.recommendations.map((stock, i) => (
          <StockCard key={stock.ticker} stock={stock} rank={i + 1} />
        ))}
      </div>

      {/* Back link */}
      <button
        onClick={() => navigate('/')}
        className="mt-6 w-full text-white/50 text-sm text-center hover:text-white/80 transition-colors"
      >
        ← Try different preferences
      </button>
    </div>
  )
}
