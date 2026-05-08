# MyStok Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Vite + React 18 SPA with React Router and Tailwind CSS that lets users pick a sector, risk level, and duration, then displays ranked stock recommendations with factor breakdowns and a drill-down detail page.

**Architecture:** Three pages (`InputPage`, `ResultsPage`, `DetailPage`) wired with React Router v6. All backend calls go through a single `api.js` module. Data flows forward via React Router `location.state` — InputPage fetches and navigates, ResultsPage reads from state, DetailPage merges state scores with a fresh fundamentals fetch.

**Tech Stack:** Vite 5, React 18, React Router v6, Tailwind CSS v3, native fetch, FastAPI CORS middleware on the backend.

---

## File Map

| File | Responsibility |
|---|---|
| `frontend/index.html` | Vite HTML shell |
| `frontend/vite.config.js` | Vite config |
| `frontend/tailwind.config.js` | Tailwind content paths |
| `frontend/postcss.config.js` | PostCSS + Tailwind plugin |
| `frontend/.env.example` | `VITE_API_URL` documentation |
| `frontend/src/main.jsx` | React root + BrowserRouter |
| `frontend/src/App.jsx` | Route definitions |
| `frontend/src/api.js` | All fetch calls |
| `frontend/src/components/Layout.jsx` | Gradient background + app header |
| `frontend/src/components/FactorBar.jsx` | Single labelled progress bar row |
| `frontend/src/components/CertaintyBadge.jsx` | Certainty % glass pill |
| `frontend/src/components/StockCard.jsx` | Stock card with rank, scores, FactorBars |
| `frontend/src/components/FundamentalsGrid.jsx` | 2-col fundamentals cells |
| `frontend/src/pages/InputPage.jsx` | Form — sector, risk, duration |
| `frontend/src/pages/ResultsPage.jsx` | Top-5 recommendations |
| `frontend/src/pages/DetailPage.jsx` | Single stock fundamentals |
| `backend/main.py` | Add FastAPI CORS middleware |

---

### Task 1: Enable CORS on the FastAPI backend

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Read the current main.py**

```bash
cat backend/main.py
```

- [ ] **Step 2: Add CORS middleware**

Add this import and middleware call to `backend/main.py`, immediately after the `app = FastAPI(...)` line:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The full updated `backend/main.py` should look like:

```python
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, SessionLocal
from backend.models import Base
from backend.importer import import_stocks
from backend.scheduler import start_scheduler, stop_scheduler
from backend.routers import health, sectors, stocks, recommend

logging.basicConfig(level=logging.INFO)
CSV_PATH = os.getenv("MYSTOK_CSV_PATH", "data/kaggle_stocks.csv")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if os.path.exists(CSV_PATH):
        db = SessionLocal()
        try:
            import_stocks(CSV_PATH, db)
        finally:
            db.close()
    else:
        logging.warning("CSV not found at %s — skipping import", CSV_PATH)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="MyStok API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sectors.router)
app.include_router(stocks.router)
app.include_router(recommend.router)
```

- [ ] **Step 3: Verify CORS header appears**

Start the backend:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:
```bash
curl -s -H "Origin: http://localhost:5173" -I http://127.0.0.1:8000/health | grep -i access-control
```

Expected output contains:
```
access-control-allow-origin: http://localhost:5173
```

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat: add CORS middleware for Vite dev server origin"
```

---

### Task 2: Scaffold Vite + React + Tailwind + React Router

**Files:**
- Create: `frontend/` (entire directory)

- [ ] **Step 1: Scaffold Vite + React project**

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

- [ ] **Step 2: Install dependencies**

```bash
npm install react-router-dom@6
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 3: Configure Tailwind content paths**

Replace the contents of `frontend/tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 4: Add Tailwind directives to the global CSS**

Replace all contents of `frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 5: Delete Vite boilerplate files**

```bash
rm frontend/src/App.css frontend/src/assets/react.svg public/vite.svg 2>/dev/null || true
```

- [ ] **Step 6: Create `.env.example`**

Create `frontend/.env.example`:

```
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 7: Verify Vite starts**

```bash
cd frontend && npm run dev
```

Expected: terminal shows `Local: http://localhost:5173/`. Open in browser — default Vite page loads (before we've written any app code).

- [ ] **Step 8: Commit**

```bash
cd ..
git add frontend/
git commit -m "chore: scaffold Vite + React + Tailwind + React Router"
```

---

### Task 3: API module

**Files:**
- Create: `frontend/src/api.js`

- [ ] **Step 1: Write `frontend/src/api.js`**

```js
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function checkOk(res) {
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const getSectors = () =>
  fetch(`${BASE}/sectors`).then(checkOk)

export const recommend = ({ risk_level, duration, sector, top_n = 5 }) =>
  fetch(`${BASE}/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ risk_level, duration, sector, top_n }),
  }).then(checkOk)

export const getStock = (ticker) =>
  fetch(`${BASE}/stocks/${ticker}`).then(checkOk)
```

- [ ] **Step 2: Verify no syntax errors**

```bash
cd frontend && node --input-type=module < /dev/null || npx vite build --mode development 2>&1 | head -20
```

Expected: no errors (the module is valid ES module syntax).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat: add API module with getSectors, recommend, getStock"
```

---

### Task 4: Layout component

**Files:**
- Create: `frontend/src/components/Layout.jsx`

- [ ] **Step 1: Write `frontend/src/components/Layout.jsx`**

```jsx
export default function Layout({ children }) {
  return (
    <div
      className="min-h-screen w-full"
      style={{
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)',
      }}
    >
      <header className="flex items-center justify-between px-6 py-4">
        <span className="text-white font-extrabold text-xl tracking-tight">MyStok</span>
      </header>
      <main className="px-4 pb-12 max-w-lg mx-auto">{children}</main>
    </div>
  )
}
```

- [ ] **Step 2: Wire up main.jsx and App.jsx temporarily to verify Layout renders**

Replace `frontend/src/main.jsx`:

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
)
```

Replace `frontend/src/App.jsx`:

```jsx
import Layout from './components/Layout.jsx'

export default function App() {
  return <Layout><p className="text-white">Hello</p></Layout>
}
```

- [ ] **Step 3: Check in browser**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` — should show a purple-to-cyan gradient background with "MyStok" in the header and "Hello" below.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Layout.jsx frontend/src/main.jsx frontend/src/App.jsx
git commit -m "feat: add Layout component with gradient background"
```

---

### Task 5: FactorBar component

**Files:**
- Create: `frontend/src/components/FactorBar.jsx`

- [ ] **Step 1: Write `frontend/src/components/FactorBar.jsx`**

```jsx
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
```

`value` is a float 0–1 (as returned by the backend's `score`, `momentum`, etc. fields).

- [ ] **Step 2: Smoke-test in App.jsx temporarily**

Replace `frontend/src/App.jsx` with:

```jsx
import Layout from './components/Layout.jsx'
import FactorBar from './components/FactorBar.jsx'

export default function App() {
  return (
    <Layout>
      <div className="flex flex-col gap-2 mt-4">
        <FactorBar label="Momentum" value={0.91} />
        <FactorBar label="Stability" value={0.74} />
        <FactorBar label="Income"   value={0.12} />
      </div>
    </Layout>
  )
}
```

Open `http://localhost:5173` — should show three labelled cyan bars of varying widths.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/FactorBar.jsx
git commit -m "feat: add FactorBar component"
```

---

### Task 6: CertaintyBadge component

**Files:**
- Create: `frontend/src/components/CertaintyBadge.jsx`

- [ ] **Step 1: Write `frontend/src/components/CertaintyBadge.jsx`**

```jsx
export default function CertaintyBadge({ certainty }) {
  return (
    <div
      className="text-center px-4 py-3 rounded-xl"
      style={{
        background: 'rgba(255,255,255,0.2)',
        border: '1px solid rgba(255,255,255,0.35)',
      }}
    >
      <div className="text-white font-extrabold text-2xl leading-none">
        {Math.round(certainty)}%
      </div>
      <div className="text-white/65 text-[9px] uppercase tracking-widest mt-1">
        Certainty
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/CertaintyBadge.jsx
git commit -m "feat: add CertaintyBadge component"
```

---

### Task 7: StockCard component

**Files:**
- Create: `frontend/src/components/StockCard.jsx`

- [ ] **Step 1: Write `frontend/src/components/StockCard.jsx`**

```jsx
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
```

- [ ] **Step 2: Smoke-test in App.jsx**

Replace `frontend/src/App.jsx` with:

```jsx
import Layout from './components/Layout.jsx'
import StockCard from './components/StockCard.jsx'

const mockStock = {
  ticker: 'AAPL', company_name: 'apple', score: 0.83,
  momentum: 0.91, stability: 0.74, income: 0.12, value: 0.65, size: 0.99,
}

export default function App() {
  return (
    <Layout>
      <div className="flex flex-col gap-3 mt-4">
        <StockCard stock={mockStock} rank={1} />
        <StockCard stock={{ ...mockStock, ticker: 'MSFT', score: 0.78 }} rank={2} />
      </div>
    </Layout>
  )
}
```

Open `http://localhost:5173` — card #1 should appear slightly more opaque than #2, with all 5 factor bars.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/StockCard.jsx
git commit -m "feat: add StockCard component"
```

---

### Task 8: FundamentalsGrid component

**Files:**
- Create: `frontend/src/components/FundamentalsGrid.jsx`

- [ ] **Step 1: Write `frontend/src/components/FundamentalsGrid.jsx`**

```jsx
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/FundamentalsGrid.jsx
git commit -m "feat: add FundamentalsGrid component with market cap formatting"
```

---

### Task 9: InputPage

**Files:**
- Create: `frontend/src/pages/InputPage.jsx`

- [ ] **Step 1: Write `frontend/src/pages/InputPage.jsx`**

```jsx
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/InputPage.jsx
git commit -m "feat: add InputPage with sector/risk/duration form"
```

---

### Task 10: ResultsPage

**Files:**
- Create: `frontend/src/pages/ResultsPage.jsx`

- [ ] **Step 1: Write `frontend/src/pages/ResultsPage.jsx`**

```jsx
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ResultsPage.jsx
git commit -m "feat: add ResultsPage with stock cards and certainty badge"
```

---

### Task 11: DetailPage

**Files:**
- Create: `frontend/src/pages/DetailPage.jsx`

- [ ] **Step 1: Write `frontend/src/pages/DetailPage.jsx`**

```jsx
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DetailPage.jsx
git commit -m "feat: add DetailPage with fundamentals and score breakdown"
```

---

### Task 12: Wire up App.jsx with all routes

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Write final `frontend/src/App.jsx`**

```jsx
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import InputPage from './pages/InputPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import DetailPage from './pages/DetailPage.jsx'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/"               element={<InputPage />} />
        <Route path="/results"        element={<ResultsPage />} />
        <Route path="/stocks/:ticker" element={<DetailPage />} />
      </Routes>
    </Layout>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: wire up React Router routes in App.jsx"
```

---

### Task 13: End-to-end smoke test

- [ ] **Step 1: Start the backend**

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: Start the frontend**

```bash
cd frontend && npm run dev
```

- [ ] **Step 3: Test the golden path**

Open `http://localhost:5173`:
1. Sector dropdown loads with sectors from `/sectors` (e.g. Technology, Healthcare, …)
2. Risk slider moves and label updates (Conservative → Aggressive)
3. Duration buttons toggle correctly
4. Click **Get Recommendations →** — button shows "Analysing…" while loading
5. `/results` page loads with sector name, certainty badge, and 5 stock cards with factor bars
6. Click any stock card → `/stocks/:ticker` loads with fundamentals grid and score breakdown
7. Click ← Back to results → returns to `/results` with the same data
8. Click ← Try different preferences → returns to `/` (form is empty/reset)

- [ ] **Step 4: Test the edge case — direct URL to /results**

Navigate directly to `http://localhost:5173/results` (no state).

Expected: immediately redirects to `/`.

- [ ] **Step 5: Add `.superpowers` to `.gitignore`**

```bash
echo ".superpowers/" >> .gitignore
git add .gitignore
git commit -m "chore: ignore .superpowers brainstorm directory"
```

- [ ] **Step 6: Final commit**

```bash
git add frontend/
git commit -m "feat: complete MyStok frontend — input, results, detail pages"
git tag v0.1.0-frontend
```
