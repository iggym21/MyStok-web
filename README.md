# MyStok

A stock recommendation web app. Tell it your sector, risk level, and investment duration — it ranks up to 5 matching stocks with a factor breakdown across momentum, stability, income, value, and size.

**Backend:** FastAPI + SQLite + yfinance  
**Frontend:** React 18 + Vite + Tailwind CSS

---

## How it works

1. Historical price data is loaded from a Kaggle CSV on first startup.
2. Five factors are scored per stock within its sector peers and weighted by your preferences.
3. The nightly scheduler (APScheduler) refreshes fundamentals from yfinance.

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 20+
- A [Kaggle account](https://www.kaggle.com) (for the dataset)

---

### 1. Get the stock data

Download the dataset from Kaggle:

**Dataset:** [World Stock Prices Daily Updating](https://www.kaggle.com/datasets/nelgiriyewithana/world-stock-prices-daily-updating)

Save the CSV as:
```
data/kaggle_stocks.csv
```

---

### 2. Backend

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the server (imports CSV and starts nightly scheduler automatically)
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The backend will import the CSV on first startup (takes ~10–20 seconds for 300k rows). Subsequent starts skip the import if the database is already populated.

**API endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server health + last yfinance refresh time |
| GET | `/sectors` | List of available sectors |
| POST | `/recommend` | Get top-N stock recommendations |
| GET | `/stocks/{ticker}` | Full fundamentals for one stock |

---

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy env file and start dev server
cp .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

> The backend must be running at `http://localhost:8000` (default). Change `VITE_API_URL` in `frontend/.env` to point elsewhere.

---

## Running tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

---

## Project structure

```
MyStok/
├── backend/
│   ├── main.py           # FastAPI app + lifespan startup
│   ├── database.py       # SQLAlchemy engine + session
│   ├── models.py         # ORM models (Stock, DailyPrice, Fundamentals)
│   ├── schemas.py        # Pydantic request/response models
│   ├── importer.py       # Kaggle CSV import
│   ├── scorer.py         # Factor scoring + weight computation
│   ├── scheduler.py      # APScheduler nightly yfinance refresh
│   ├── requirements.txt
│   └── routers/
│       ├── health.py
│       ├── sectors.py
│       ├── stocks.py
│       └── recommend.py
├── frontend/
│   ├── src/
│   │   ├── api.js        # All fetch calls
│   │   ├── App.jsx       # Route definitions
│   │   ├── main.jsx      # React root + BrowserRouter
│   │   ├── components/
│   │   │   ├── Layout.jsx
│   │   │   ├── StockCard.jsx
│   │   │   ├── FactorBar.jsx
│   │   │   ├── CertaintyBadge.jsx
│   │   │   └── FundamentalsGrid.jsx
│   │   └── pages/
│   │       ├── InputPage.jsx
│   │       ├── ResultsPage.jsx
│   │       └── DetailPage.jsx
│   └── .env.example
├── tests/
│   ├── test_importer.py
│   └── test_scorer.py
└── data/                 # gitignored — add kaggle_stocks.csv here
```

---

## Notes

- Stock fundamentals (P/E ratio, market cap, dividend yield, 52-week range) are fetched from yfinance by the nightly scheduler. They show `—` until the first refresh runs.
- The Kaggle dataset covers ~62 stocks across 7 sectors. Momentum scores may be low if the CSV data is older than the current date.
