# MyStok — Design Spec
**Date:** 2026-05-08

## Problem & Motivation

People who want to invest in the stock market face a research barrier — finding stocks that match their goals, risk appetite, and timeline takes hours. MyStok removes that barrier by accepting three simple user inputs (risk level, investment duration, sector) and returning the top 5 stocks that best match their profile, with a certainty score showing how well the results fit.

---

## Architecture Overview

```
Kaggle CSV
    │
    ▼ (one-time import on first run)
SQLite DB ◄──── APScheduler (nightly) ◄──── yfinance
    │
    ▼
FastAPI backend
    │
    ▼
React + Tailwind frontend (deferred)
```

**Components:**
- **SQLite** — stores stock metadata, OHLCV price history, and fundamentals
- **APScheduler** — nightly job refreshes prices and fundamentals via yfinance
- **FastAPI** — REST API consumed by the frontend
- **scorer.py** — pure Python scoring module; no DB or API dependencies; takes stock data in, returns ranked results out

---

## Data Pipeline

### One-Time CSV Import (first run)
On startup, if the DB is empty, the Kaggle CSV is parsed with pandas and loaded into SQLite:
- Each row → `daily_prices`
- Unique tickers → `stocks` (company name, industry from CSV; `sector` left NULL until yfinance fetch)

### Sector Mapping
During the initial fundamentals fetch, `yfinance.Ticker(ticker).info['sector']` populates `stocks.sector`. yfinance is the authoritative source for sector labels — the Kaggle `industry` string is stored as metadata only. Tickers with no yfinance record (delisted, invalid) keep `sector = NULL` and are excluded from recommendations.

### Nightly Refresh (APScheduler)
Runs at midnight. Iterates over all tickers in `stocks`, calls yfinance, and upserts:
- Latest closing price → `daily_prices`
- P/E ratio, dividend yield, market cap, 52-week high/low → `fundamentals`

Tickers are batched in groups of 50 with a short sleep between batches to avoid rate limits. Failures are logged and skipped — no crash.

### Database Schema

```
stocks:
    ticker          TEXT  PRIMARY KEY
    company_name    TEXT
    sector          TEXT  (from yfinance)
    industry        TEXT  (from Kaggle, display only)
    country         TEXT

daily_prices:
    ticker          TEXT
    date            DATE
    open            REAL
    high            REAL
    low             REAL
    close           REAL
    volume          INTEGER
    PRIMARY KEY (ticker, date)

fundamentals:
    ticker          TEXT  PRIMARY KEY
    pe_ratio        REAL
    dividend_yield  REAL
    market_cap      INTEGER
    week52_high     REAL
    week52_low      REAL
    last_updated    TIMESTAMP
```

---

## Scoring Algorithm

### Inputs
- `risk_level`: integer 1–5 (1 = very conservative, 5 = very aggressive)
- `duration`: `"short"` (<1 year), `"medium"` (1–5 years), `"long"` (5+ years)
- `sector`: string matching a yfinance sector label

### Five Factors
All factors normalized 0–1 using min-max within the chosen sector, so scores are relative to sector peers.

| Factor | Measures | Source | Notes |
|--------|----------|--------|-------|
| Momentum | 1-year price change (%) | `daily_prices` | Higher = better for growth |
| Stability | Inverse of daily return volatility (past year) | `daily_prices` | `1 − normalized_volatility` |
| Income | Dividend yield | `fundamentals` | Higher = better for income investors |
| Value | Inverse of P/E ratio (capped at 100) | `fundamentals` | Lower P/E = more undervalued |
| Size | log(market_cap), normalized | `fundamentals` | Proxy for stability |

### Weight Computation

```python
risk_ratio = (risk_level - 1) / 4      # 0.0 (conservative) → 1.0 (aggressive)
dur_ratio  = {"short": 0.0, "medium": 0.5, "long": 1.0}[duration]

weights = {
    "momentum":  0.10 + 0.30 * risk_ratio,
    "stability": 0.35 - 0.25 * risk_ratio,
    "income":    0.25 - 0.10 * risk_ratio + 0.10 * dur_ratio,
    "value":     0.20 - 0.05 * risk_ratio,
    "size":      0.10 - 0.05 * risk_ratio,
}
# Normalize to sum to 1.0
total = sum(weights.values())
weights = {k: v / total for k, v in weights.items()}
```

### Final Score
```
score = Σ (weight[factor] × normalized_factor_value)
```

### Edge Cases
- **Negative P/E** (company losing money) → `value_score = 0`
- **All sector peers share the same value for a factor** (e.g., zero dividends across all tech stocks) → assign `0.5` to every stock for that factor so it doesn't distort rankings
- **Missing fundamentals** (no yfinance data) → ticker excluded from scoring

### Certainty Score
```
certainty = mean(top_5_scores) × 100   [as a percentage]
```
Indicates how well the top results match the user's profile.

---

## API Design

### `GET /sectors`
Returns available sectors from the DB.
```json
["Technology", "Healthcare", "Financial Services", "Energy", ...]
```

### `POST /recommend`
Core endpoint. Runs the scoring pipeline and returns top-N results.

Request:
```json
{
  "risk_level": 3,
  "duration": "medium",
  "sector": "Technology",
  "top_n": 5
}
```

Response:
```json
{
  "recommendations": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "score": 0.83,
      "momentum": 0.91,
      "stability": 0.74,
      "income": 0.12,
      "value": 0.65,
      "size": 0.99
    }
  ],
  "certainty": 78.4,
  "sector": "Technology",
  "stocks_evaluated": 142
}
```

### `GET /health`
Returns API status and data freshness.
```json
{ "status": "ok", "last_refresh": "2026-05-08T00:00:00" }
```

### `GET /stocks/{ticker}`
Returns full profile for a single ticker (fundamentals + recent price history). Used for a future stock detail page.

---

## Project Structure

```
MyStok/
├── backend/
│   ├── main.py                 # FastAPI app, router registration, startup events
│   ├── database.py             # SQLAlchemy engine, session factory, table definitions
│   ├── scheduler.py            # APScheduler setup, nightly yfinance refresh job
│   ├── importer.py             # One-time Kaggle CSV → SQLite import logic
│   ├── scorer.py               # Pure scoring logic (no DB/API deps)
│   ├── routers/
│   │   ├── recommend.py        # POST /recommend
│   │   ├── sectors.py          # GET /sectors
│   │   ├── health.py           # GET /health
│   │   └── stocks.py           # GET /stocks/{ticker}
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response models
│   └── requirements.txt
├── data/
│   └── kaggle_stocks.csv       # Raw Kaggle dataset (user places this here)
├── mystok.db                   # SQLite database (auto-created on first run)
└── frontend/                   # Placeholder — React app goes here later
```

---

## Out of Scope (for now)
- User accounts / authentication
- Frontend implementation (deferred until core backend is complete)
- Real-time price streaming
- Portfolio tracking
- Push notifications / alerts
