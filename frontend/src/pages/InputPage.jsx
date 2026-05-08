import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSectors, recommend } from '../api.js'

const RISK_LABELS = {
  1: 'Conservative', 2: 'Cautious', 3: 'Moderate', 4: 'Growth', 5: 'Aggressive',
}

const DURATIONS = [
  { value: 'short',  label: 'Short',  sub: '< 1 year' },
  { value: 'medium', label: 'Medium', sub: '1–5 years' },
  { value: 'long',   label: 'Long',   sub: '5+ years' },
]

export default function InputPage() {
  const navigate = useNavigate()
  const [sectors, setSectors]     = useState([])
  const [sector, setSector]       = useState('')
  const [risk, setRisk]           = useState(3)
  const [duration, setDuration]   = useState('medium')
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [fetchError, setFetchError] = useState(null)

  useEffect(() => {
    getSectors()
      .then(data => { setSectors(data); setSector(data[0] ?? '') })
      .catch(() => setFetchError('Could not load sectors — is the backend running?'))
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const data = await recommend({ risk_level: risk, duration, sector })
      navigate('/results', { state: { data, sector, risk, duration } })
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-72px)]">
      <div className="text-center mb-8">
        <h1 className="text-white font-extrabold text-3xl tracking-tight">
          Find your stocks
        </h1>
        <p className="text-white/65 text-sm mt-1">
          Tell us your goals and we'll do the research.
        </p>
      </div>

      {fetchError && (
        <p className="text-red-300 text-sm mb-4 text-center">{fetchError}</p>
      )}

      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-2xl p-7 flex flex-col gap-5"
        style={{
          background: 'rgba(255,255,255,0.15)',
          border: '1px solid rgba(255,255,255,0.25)',
          backdropFilter: 'blur(12px)',
        }}
      >
        {/* Sector */}
        <div>
          <label className="block text-white/80 text-[11px] font-bold uppercase tracking-widest mb-2">
            Sector
          </label>
          <select
            value={sector}
            onChange={e => setSector(e.target.value)}
            className="w-full rounded-xl px-4 py-2.5 text-sm font-medium text-white outline-none"
            style={{
              background: 'rgba(255,255,255,0.15)',
              border: '1px solid rgba(255,255,255,0.25)',
            }}
          >
            {sectors.map(s => (
              <option key={s} value={s} style={{ background: '#6366f1' }}>{s}</option>
            ))}
          </select>
        </div>

        {/* Risk */}
        <div>
          <label className="block text-white/80 text-[11px] font-bold uppercase tracking-widest mb-1">
            Risk Level —{' '}
            <span className="normal-case font-normal tracking-normal">
              {RISK_LABELS[risk]} ({risk})
            </span>
          </label>
          <input
            type="range" min={1} max={5} step={1}
            value={risk}
            onChange={e => setRisk(Number(e.target.value))}
            className="w-full accent-white"
          />
          <div className="flex justify-between text-white/55 text-[10px] mt-1">
            <span>Conservative</span><span>Aggressive</span>
          </div>
        </div>

        {/* Duration */}
        <div>
          <label className="block text-white/80 text-[11px] font-bold uppercase tracking-widest mb-2">
            Investment Duration
          </label>
          <div className="grid grid-cols-3 gap-2">
            {DURATIONS.map(d => (
              <button
                key={d.value}
                type="button"
                onClick={() => setDuration(d.value)}
                className="rounded-xl py-2.5 text-center transition-all"
                style={{
                  background: duration === d.value
                    ? 'rgba(255,255,255,0.30)'
                    : 'rgba(255,255,255,0.10)',
                  border: duration === d.value
                    ? '1.5px solid rgba(255,255,255,0.65)'
                    : '1px solid rgba(255,255,255,0.20)',
                }}
              >
                <div className="text-white font-bold text-sm">{d.label}</div>
                <div className="text-white/65 text-[10px]">{d.sub}</div>
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="text-red-300 text-xs text-center">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading || !sector}
          className="w-full bg-white text-indigo-500 font-bold text-base py-3.5 rounded-xl transition-opacity disabled:opacity-60"
        >
          {loading ? 'Analysing…' : 'Get Recommendations →'}
        </button>
      </form>
    </div>
  )
}
