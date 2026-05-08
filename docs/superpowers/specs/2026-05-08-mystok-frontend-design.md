# MyStok Frontend — Design Spec
**Date:** 2026-05-08

## Overview

React + Tailwind SPA that wraps the MyStok FastAPI backend. Users fill in three preferences (sector, risk level, investment duration), receive a ranked list of up to 5 stock recommendations with a factor breakdown per card, and can drill into a detail page for any stock's fundamentals.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Bundler | Vite |
| Framework | React 18 |
| Routing | React Router v6 |
| Styling | Tailwind CSS v3 |
| State | React `useState` / `useEffect` (no external store) |
| API calls | Native `fetch`, centralised in `src/api.js` |

---

## Visual Design

**Theme:** Modern gradient with glassmorphism.
- Background: `linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)`
- Cards: `background: rgba(255,255,255,0.15)`, `backdrop-filter: blur(12px)`, `border: 1px solid rgba(255,255,255,0.25)`, `border-radius: 14px`
- Primary text: `white`
- Secondary text: `rgba(255,255,255,0.65)`
- Factor bar fill: `#a5f3fc` (cyan-200)
- CTA button: white background, `#6366f1` text

---

## Routes

| Path | Component | Data source |
|---|---|---|
| `/` | `InputPage` | `GET /sectors` on mount |
| `/results` | `ResultsPage` | React Router `location.state` (set by InputPage) |
| `/stocks/:ticker` | `DetailPage` | `GET /stocks/:ticker` on mount + `location.state` for scores |

If `/results` is visited with no `location.state` (e.g. direct URL), redirect to `/`.

---

## Pages

### InputPage (`/`)

Three inputs, one submit button.

**Sector** — dropdown populated from `GET /sectors` on mount. Shows a loading skeleton while fetching. Shows an error message if the fetch fails.

**Risk Level** — range slider, 1–5. Label updates live: `1=Conservative`, `2=Cautious`, `3=Moderate`, `4=Growth`, `5=Aggressive`.

**Investment Duration** — three toggle buttons: `Short (<1 yr)`, `Medium (1–5 yrs)`, `Long (5+ yrs)`. Exactly one is active at a time.

**Submit** — calls `POST /recommend` with `{ risk_level, duration, sector, top_n: 5 }`. Button shows spinner + "Analysing…" while in flight. On success, navigates to `/results` with the full response in router state. On error, shows an inline error message below the button.

---

### ResultsPage (`/results`)

Reads `useLocation().state`. If state is null, redirects to `/`.

**Header row:**
- Left: sector name (large), sub-line with stocks evaluated count, risk label, duration
- Right: `CertaintyBadge` showing `certainty` percentage

**Stock cards:** 5 `<StockCard>` components stacked vertically. The `#1` card uses slightly higher opacity (`rgba(255,255,255,0.20)`) vs cards `#2–5` (`rgba(255,255,255,0.12)`) to draw the eye to the best match.

**Each StockCard shows:**
- Rank badge (`#1`–`#5`), ticker, company name
- Match score (large, top-right)
- 5 `<FactorBar>` rows: Momentum, Stability, Income, Value, Size — each with label, filled bar, percentage
- "Tap for full details →" hint; clicking navigates to `/stocks/:ticker` passing the stock's score data in router state

**Footer:** "← Try different preferences" link back to `/`.

---

### DetailPage (`/stocks/:ticker`)

Reads `ticker` from `useParams()`. Fetches `GET /stocks/:ticker` on mount. Score data (momentum, stability, income, value, size, overall score) comes from `location.state` passed by ResultsPage — no second fetch needed for scores.

**Stock header:** Ticker (large), company name · sector, country.
Match score badge (top-right, same style as ResultsPage).

**Fundamentals grid (2-column):**
- Market Cap (formatted: `$3.4T`, `$245B`, `$12M`)
- P/E Ratio
- Dividend Yield (`0.44%` or `—` if null)
- 52-Week Range (`$164 – $237`)
- Sector
- Industry

Any null fundamental displays as `—`.

**Score Breakdown section:** Same 5 `<FactorBar>` rows as StockCard, using values from `location.state`.

**Back nav:** "← Back to results" — `navigate(-1)`.

---

## Component Inventory

| Component | Responsibility |
|---|---|
| `Layout` | Full-height gradient wrapper, app name header |
| `StockCard` | Card shell + 5 FactorBars + rank/score/ticker header |
| `FactorBar` | Single labelled progress bar row |
| `CertaintyBadge` | Glass pill showing certainty percentage |
| `FundamentalsGrid` | 2-column grid of labelled stat cells |

---

## API Module (`src/api.js`)

```js
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const getSectors = () =>
  fetch(`${BASE}/sectors`).then(r => { if (!r.ok) throw new Error(r.status); return r.json() })

export const recommend = ({ risk_level, duration, sector, top_n = 5 }) =>
  fetch(`${BASE}/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ risk_level, duration, sector, top_n }),
  }).then(r => { if (!r.ok) throw new Error(r.status); return r.json() })

export const getStock = (ticker) =>
  fetch(`${BASE}/stocks/${ticker}`).then(r => { if (!r.ok) throw new Error(r.status); return r.json() })
```

---

## Project Structure

```
frontend/
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env.example              # VITE_API_URL=http://localhost:8000
├── src/
│   ├── main.jsx              # ReactDOM.createRoot + BrowserRouter
│   ├── App.jsx               # <Routes> definitions
│   ├── api.js                # All fetch calls
│   ├── pages/
│   │   ├── InputPage.jsx
│   │   ├── ResultsPage.jsx
│   │   └── DetailPage.jsx
│   └── components/
│       ├── Layout.jsx
│       ├── StockCard.jsx
│       ├── FactorBar.jsx
│       ├── CertaintyBadge.jsx
│       └── FundamentalsGrid.jsx
```

---

## Environment

`.env.example`:
```
VITE_API_URL=http://localhost:8000
```

The frontend and backend run as separate dev servers. CORS must be enabled on the FastAPI backend for `http://localhost:5173` (Vite's default port).

---

## Out of Scope

- Authentication
- Portfolio tracking
- Charts / price history graphs
- Dark/light mode toggle
- Mobile-specific layouts (responsive but not mobile-first)
