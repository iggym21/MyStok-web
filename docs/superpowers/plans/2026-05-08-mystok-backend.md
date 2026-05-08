# MyStok Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI backend that imports a Kaggle stock CSV into SQLite, refreshes fundamentals nightly via yfinance, scores stocks against user inputs, and exposes 4 REST endpoints.

**Architecture:** One-time CSV import seeds SQLite on first run. APScheduler runs nightly to upsert latest prices and fundamentals via yfinance. Each `/recommend` request queries the DB, runs the pure scorer module, and returns ranked results with a certainty score.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy (SQLite), APScheduler, yfinance, pandas, pydantic

---

## File Map

| File | Responsibility |
|------|---------------|
| `backend/requirements.txt` | Pinned dependencies |
| `backend/database.py` | SQLAlchemy engine, session factory, Base |
| `backend/models.py` | ORM models: Stock, DailyPrice, Fundamentals |
| `backend/schemas.py` | Pydantic request/response models |
| `backend/importer.py` | One-time Kaggle CSV → SQLite import |
| `backend/scorer.py` | Pure scoring logic (no DB/API deps) |
| `backend/scheduler.py` | APScheduler + nightly yfinance refresh job |
| `backend/routers/health.py` | GET /health |
| `backend/routers/sectors.py` | GET /sectors |
| `backend/routers/stocks.py` | GET /stocks/{ticker} |
| `backend/routers/recommend.py` | POST /recommend |
| `backend/main.py` | FastAPI app wiring |
| `tests/test_scorer.py` | Unit tests for scorer.py |
| `tests/test_importer.py` | Unit tests for importer.py |

---

### Task 1: Project scaffold + dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/__init__.py`
- Create: `backend/routers/__init__.py`
- Create: `tests/__init__.py`
- Create: `data/.gitkeep`

- [ ] Create directory structure

```bash
mkdir -p backend/routers tests data
touch backend/__init__.py backend/routers/__init__.py tests/__init__.py data/.gitkeep
```

- [ ] Write `backend/requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
pydantic==2.7.1
yfinance==0.2.40
pandas==2.2.2
apscheduler==3.10.4
pytest==8.2.0
httpx==0.27.0
```

- [ ] Install dependencies

```bash
cd backend && pip install -r requirements.txt
```

- [ ] Commit

```bash
git init
git add .
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: Database setup

**Files:**
- Create: `backend/database.py`

- [ ] Write `backend/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///../mystok.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] Commit

```bash
git add backend/database.py
git commit -m "feat: add database engine and session factory"
```

---

### Task 3: ORM models

**Files:**
- Create: `backend/models.py`

- [ ] Write `backend/models.py`

```python
from datetime import date, datetime
from sqlalchemy import String, Float, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base

class Stock(Base):
    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    company_name: Mapped[str | None] = mapped_column(String)
    sector: Mapped[str | None] = mapped_column(String)
    industry: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    ticker: Mapped[str] = mapped_column(String, ForeignKey("stocks.ticker"), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(Integer)


class Fundamentals(Base):
    __tablename__ = "fundamentals"

    ticker: Mapped[str] = mapped_column(String, ForeignKey("stocks.ticker"), primary_key=True)
    pe_ratio: Mapped[float | None] = mapped_column(Float)
    dividend_yield: Mapped[float | None] = mapped_column(Float)
    market_cap: Mapped[int | None] = mapped_column(Integer)
    week52_high: Mapped[float | None] = mapped_column(Float)
    week52_low: Mapped[float | None] = mapped_column(Float)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime)
```

- [ ] Commit

```bash
git add backend/models.py
git commit -m "feat: add SQLAlchemy ORM models"
```

---

### Task 4: Pydantic schemas

**Files:**
- Create: `backend/schemas.py`

- [ ] Write `backend/schemas.py`

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    risk_level: int = Field(..., ge=1, le=5)
    duration: Literal["short", "medium", "long"]
    sector: str
    top_n: int = Field(default=5, ge=1, le=20)


class StockResult(BaseModel):
    ticker: str
    company_name: str | None
    score: float
    momentum: float
    stability: float
    income: float
    value: float
    size: float


class RecommendResponse(BaseModel):
    recommendations: list[StockResult]
    certainty: float
    sector: str
    stocks_evaluated: int


class HealthResponse(BaseModel):
    status: str
    last_refresh: datetime | None


class StockDetail(BaseModel):
    ticker: str
    company_name: str | None
    sector: str | None
    industry: str | None
    country: str | None
    pe_ratio: float | None
    dividend_yield: float | None
    market_cap: int | None
    week52_high: float | None
    week52_low: float | None
```

- [ ] Commit

```bash
git add backend/schemas.py
git commit -m "feat: add Pydantic request/response schemas"
```

---

### Task 5: CSV importer

**Files:**
- Create: `backend/importer.py`
- Create: `tests/test_importer.py`

- [ ] Write failing test `tests/test_importer.py`

```python
import pytest
import pandas as pd
from unittest.mock import MagicMock
from backend.importer import parse_csv, import_stocks

def test_parse_csv_returns_tickers_and_prices(tmp_path):
    csv = tmp_path / "stocks.csv"
    csv.write_text(
        "Date,Open,High,Low,Close,Volume,Name,ticker,Industry,Country\n"
        "2023-01-01,100,110,90,105,1000000,Apple Inc,AAPL,Software,USA\n"
        "2023-01-02,105,115,100,110,1200000,Apple Inc,AAPL,Software,USA\n"
    )
    stocks, prices = parse_csv(str(csv))
    assert "AAPL" in stocks
    assert stocks["AAPL"]["company_name"] == "Apple Inc"
    assert len(prices) == 2
    assert prices[0]["ticker"] == "AAPL"

def test_parse_csv_deduplicates_stocks(tmp_path):
    csv = tmp_path / "stocks.csv"
    csv.write_text(
        "Date,Open,High,Low,Close,Volume,Name,ticker,Industry,Country\n"
        "2023-01-01,100,110,90,105,1000000,Apple Inc,AAPL,Software,USA\n"
        "2023-01-02,105,115,100,110,1200000,Apple Inc,AAPL,Software,USA\n"
    )
    stocks, prices = parse_csv(str(csv))
    assert len(stocks) == 1
```

- [ ] Run test to verify it fails

```bash
pytest tests/test_importer.py -v
```

Expected: FAIL with `ImportError` or `ModuleNotFoundError`

- [ ] Write `backend/importer.py`

```python
import logging
from datetime import date
from sqlalchemy.orm import Session
import pandas as pd
from backend.models import Stock, DailyPrice

logger = logging.getLogger(__name__)

CSV_COLUMN_MAP = {
    "Date": "date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
    "Name": "company_name",
    "ticker": "ticker",
    "Industry": "industry",
    "Country": "country",
}


def parse_csv(csv_path: str) -> tuple[dict, list[dict]]:
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df.rename(columns=CSV_COLUMN_MAP, inplace=True)

    stocks: dict[str, dict] = {}
    for _, row in df.drop_duplicates("ticker").iterrows():
        stocks[row["ticker"]] = {
            "ticker": row["ticker"],
            "company_name": row.get("company_name"),
            "industry": row.get("industry"),
            "country": row.get("country"),
            "sector": None,
        }

    prices = []
    for _, row in df.iterrows():
        prices.append({
            "ticker": row["ticker"],
            "date": row["date"].date() if hasattr(row["date"], "date") else row["date"],
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
        })

    return stocks, prices


def import_stocks(csv_path: str, db: Session) -> None:
    if db.query(Stock).count() > 0:
        logger.info("Database already populated, skipping import")
        return

    logger.info("Starting CSV import from %s", csv_path)
    stocks, prices = parse_csv(csv_path)

    db.bulk_insert_mappings(Stock, list(stocks.values()))

    batch_size = 10_000
    for i in range(0, len(prices), batch_size):
        db.bulk_insert_mappings(DailyPrice, prices[i : i + batch_size])
        db.commit()

    logger.info("Imported %d stocks and %d price rows", len(stocks), len(prices))
```

- [ ] Run tests to verify they pass

```bash
pytest tests/test_importer.py -v
```

Expected: PASS

- [ ] Commit

```bash
git add backend/importer.py tests/test_importer.py
git commit -m "feat: add Kaggle CSV importer"
```

---

### Task 6: Scorer module

**Files:**
- Create: `backend/scorer.py`
- Create: `tests/test_scorer.py`

- [ ] Write failing tests `tests/test_scorer.py`

```python
import pytest
from backend.scorer import compute_weights, normalize, score_stocks

def test_compute_weights_sum_to_one():
    for risk in range(1, 6):
        for duration in ["short", "medium", "long"]:
            weights = compute_weights(risk, duration)
            assert abs(sum(weights.values()) - 1.0) < 1e-9

def test_compute_weights_aggressive_favors_momentum():
    conservative = compute_weights(1, "long")
    aggressive = compute_weights(5, "long")
    assert aggressive["momentum"] > conservative["momentum"]
    assert aggressive["stability"] < conservative["stability"]

def test_normalize_returns_zero_to_one():
    values = [10.0, 20.0, 30.0]
    result = normalize(values)
    assert result[0] == pytest.approx(0.0)
    assert result[2] == pytest.approx(1.0)

def test_normalize_constant_series_returns_half():
    values = [5.0, 5.0, 5.0]
    result = normalize(values)
    assert all(v == pytest.approx(0.5) for v in result)

def test_score_stocks_returns_sorted_descending():
    stocks = [
        {"ticker": "A", "momentum_raw": 0.5, "volatility_raw": 0.1,
         "dividend_yield": 0.02, "pe_ratio": 15.0, "market_cap": 1_000_000_000},
        {"ticker": "B", "momentum_raw": 0.1, "volatility_raw": 0.5,
         "dividend_yield": 0.00, "pe_ratio": 80.0, "market_cap": 100_000_000},
    ]
    results = score_stocks(stocks, risk_level=5, duration="long")
    assert results[0]["score"] >= results[1]["score"]

def test_score_stocks_includes_factor_breakdown():
    stocks = [
        {"ticker": "A", "momentum_raw": 0.3, "volatility_raw": 0.2,
         "dividend_yield": 0.01, "pe_ratio": 20.0, "market_cap": 500_000_000},
    ]
    results = score_stocks(stocks, risk_level=3, duration="medium")
    assert "momentum" in results[0]
    assert "stability" in results[0]
    assert "income" in results[0]
    assert "value" in results[0]
    assert "size" in results[0]
    assert 0.0 <= results[0]["score"] <= 1.0
```

- [ ] Run tests to verify they fail

```bash
pytest tests/test_scorer.py -v
```

Expected: FAIL with `ImportError`

- [ ] Write `backend/scorer.py`

```python
import math


def compute_weights(risk_level: int, duration: str) -> dict[str, float]:
    r = (risk_level - 1) / 4
    d = {"short": 0.0, "medium": 0.5, "long": 1.0}[duration]

    raw = {
        "momentum":  0.10 + 0.30 * r,
        "stability": 0.35 - 0.25 * r,
        "income":    0.25 - 0.10 * r + 0.10 * d,
        "value":     0.20 - 0.05 * r,
        "size":      0.10 - 0.05 * r,
    }
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}


def normalize(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _value_score_raw(pe_ratio: float | None) -> float:
    if pe_ratio is None or pe_ratio <= 0:
        return 0.0
    return 1.0 / min(pe_ratio, 100.0)


def score_stocks(
    stocks: list[dict],
    risk_level: int,
    duration: str,
) -> list[dict]:
    if not stocks:
        return []

    weights = compute_weights(risk_level, duration)

    momentum_vals  = normalize([s["momentum_raw"] for s in stocks])
    stability_vals = normalize([1.0 - s["volatility_raw"] for s in stocks])
    income_vals    = normalize([s.get("dividend_yield") or 0.0 for s in stocks])
    value_raws     = [_value_score_raw(s.get("pe_ratio")) for s in stocks]
    value_vals     = normalize(value_raws)
    size_vals      = normalize([math.log1p(s.get("market_cap") or 0) for s in stocks])

    results = []
    for i, stock in enumerate(stocks):
        factors = {
            "momentum":  momentum_vals[i],
            "stability": stability_vals[i],
            "income":    income_vals[i],
            "value":     value_vals[i],
            "size":      size_vals[i],
        }
        score = sum(weights[f] * factors[f] for f in factors)
        results.append({**stock, **factors, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
```

- [ ] Run tests to verify they pass

```bash
pytest tests/test_scorer.py -v
```

Expected: all 5 PASS

- [ ] Commit

```bash
git add backend/scorer.py tests/test_scorer.py
git commit -m "feat: add stock scoring module with weight computation"
```

---

### Task 7: Scheduler (yfinance nightly refresh)

**Files:**
- Create: `backend/scheduler.py`

- [ ] Write `backend/scheduler.py`

```python
import logging
import time
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
import yfinance as yf
from backend.database import SessionLocal
from backend.models import Stock, DailyPrice, Fundamentals

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler()

BATCH_SIZE = 50
BATCH_SLEEP = 2.0


def refresh_ticker(ticker: str, db: Session) -> None:
    try:
        info = yf.Ticker(ticker).info

        sector = info.get("sector")
        if sector:
            stock = db.get(Stock, ticker)
            if stock and stock.sector != sector:
                stock.sector = sector

        hist = yf.Ticker(ticker).history(period="1d")
        if not hist.empty:
            row = hist.iloc[-1]
            price = DailyPrice(
                ticker=ticker,
                date=row.name.date(),
                open=row.get("Open"),
                high=row.get("High"),
                low=row.get("Low"),
                close=row.get("Close"),
                volume=int(row.get("Volume", 0)) or None,
            )
            db.merge(price)

        fund = Fundamentals(
            ticker=ticker,
            pe_ratio=info.get("trailingPE"),
            dividend_yield=info.get("dividendYield"),
            market_cap=info.get("marketCap"),
            week52_high=info.get("fiftyTwoWeekHigh"),
            week52_low=info.get("fiftyTwoWeekLow"),
            last_updated=datetime.now(timezone.utc),
        )
        db.merge(fund)
        db.commit()
    except Exception:
        logger.exception("Failed to refresh %s", ticker)
        db.rollback()


def run_refresh() -> None:
    logger.info("Starting nightly refresh")
    db = SessionLocal()
    try:
        tickers = [row.ticker for row in db.query(Stock.ticker).all()]
        for i in range(0, len(tickers), BATCH_SIZE):
            batch = tickers[i : i + BATCH_SIZE]
            for ticker in batch:
                refresh_ticker(ticker, db)
            time.sleep(BATCH_SLEEP)
        logger.info("Nightly refresh complete")
    finally:
        db.close()


def start_scheduler() -> None:
    _scheduler.add_job(run_refresh, "cron", hour=0, minute=0)
    _scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    _scheduler.shutdown()
```

- [ ] Commit

```bash
git add backend/scheduler.py
git commit -m "feat: add APScheduler nightly yfinance refresh job"
```

---

### Task 8: Routers

**Files:**
- Create: `backend/routers/health.py`
- Create: `backend/routers/sectors.py`
- Create: `backend/routers/stocks.py`
- Create: `backend/routers/recommend.py`

- [ ] Write `backend/routers/health.py`

```python
from datetime import timezone
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Fundamentals
from backend.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    last = db.query(func.max(Fundamentals.last_updated)).scalar()
    return HealthResponse(status="ok", last_refresh=last)
```

- [ ] Write `backend/routers/sectors.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Stock

router = APIRouter()

@router.get("/sectors", response_model=list[str])
def sectors(db: Session = Depends(get_db)):
    rows = (
        db.query(Stock.sector)
        .filter(Stock.sector.isnot(None))
        .distinct()
        .order_by(Stock.sector)
        .all()
    )
    return [r.sector for r in rows]
```

- [ ] Write `backend/routers/stocks.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Stock, Fundamentals
from backend.schemas import StockDetail

router = APIRouter()

@router.get("/stocks/{ticker}", response_model=StockDetail)
def get_stock(ticker: str, db: Session = Depends(get_db)):
    stock = db.get(Stock, ticker.upper())
    if not stock:
        raise HTTPException(status_code=404, detail="Ticker not found")
    fund = db.get(Fundamentals, ticker.upper())
    return StockDetail(
        ticker=stock.ticker,
        company_name=stock.company_name,
        sector=stock.sector,
        industry=stock.industry,
        country=stock.country,
        pe_ratio=fund.pe_ratio if fund else None,
        dividend_yield=fund.dividend_yield if fund else None,
        market_cap=fund.market_cap if fund else None,
        week52_high=fund.week52_high if fund else None,
        week52_low=fund.week52_low if fund else None,
    )
```

- [ ] Write `backend/routers/recommend.py`

```python
import math
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Stock, DailyPrice, Fundamentals
from backend.schemas import RecommendRequest, RecommendResponse, StockResult
from backend.scorer import score_stocks

router = APIRouter()


def _compute_momentum(ticker: str, db: Session) -> float:
    today = date.today()
    year_ago = today - timedelta(days=365)

    recent = (
        db.query(DailyPrice.close)
        .filter(DailyPrice.ticker == ticker, DailyPrice.date >= today - timedelta(days=7))
        .order_by(DailyPrice.date.desc())
        .first()
    )
    past = (
        db.query(DailyPrice.close)
        .filter(DailyPrice.ticker == ticker, DailyPrice.date >= year_ago - timedelta(days=7),
                DailyPrice.date <= year_ago + timedelta(days=7))
        .order_by(DailyPrice.date.desc())
        .first()
    )
    if not recent or not past or not past.close or past.close == 0:
        return 0.0
    return (recent.close - past.close) / past.close


def _compute_volatility(ticker: str, db: Session) -> float:
    year_ago = date.today() - timedelta(days=365)
    prices = (
        db.query(DailyPrice.close)
        .filter(DailyPrice.ticker == ticker, DailyPrice.date >= year_ago)
        .order_by(DailyPrice.date)
        .all()
    )
    closes = [p.close for p in prices if p.close]
    if len(closes) < 2:
        return 0.0
    returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    return math.sqrt(variance)


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)):
    stocks = (
        db.query(Stock)
        .filter(Stock.sector == req.sector)
        .all()
    )
    if not stocks:
        raise HTTPException(status_code=404, detail=f"No stocks found for sector '{req.sector}'")

    fund_map = {
        f.ticker: f
        for f in db.query(Fundamentals)
        .filter(Fundamentals.ticker.in_([s.ticker for s in stocks]))
        .all()
    }

    stock_dicts = []
    for stock in stocks:
        fund = fund_map.get(stock.ticker)
        stock_dicts.append({
            "ticker": stock.ticker,
            "company_name": stock.company_name,
            "momentum_raw": _compute_momentum(stock.ticker, db),
            "volatility_raw": _compute_volatility(stock.ticker, db),
            "dividend_yield": fund.dividend_yield if fund else None,
            "pe_ratio": fund.pe_ratio if fund else None,
            "market_cap": fund.market_cap if fund else None,
        })

    ranked = score_stocks(stock_dicts, req.risk_level, req.duration)
    top = ranked[: req.top_n]

    certainty = (sum(s["score"] for s in top) / len(top) * 100) if top else 0.0

    return RecommendResponse(
        recommendations=[
            StockResult(
                ticker=s["ticker"],
                company_name=s.get("company_name"),
                score=round(s["score"], 4),
                momentum=round(s["momentum"], 4),
                stability=round(s["stability"], 4),
                income=round(s["income"], 4),
                value=round(s["value"], 4),
                size=round(s["size"], 4),
            )
            for s in top
        ],
        certainty=round(certainty, 2),
        sector=req.sector,
        stocks_evaluated=len(stock_dicts),
    )
```

- [ ] Commit

```bash
git add backend/routers/
git commit -m "feat: add all four API routers"
```

---

### Task 9: FastAPI app entry point

**Files:**
- Create: `backend/main.py`

- [ ] Write `backend/main.py`

```python
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
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

app.include_router(health.router)
app.include_router(sectors.router)
app.include_router(stocks.router)
app.include_router(recommend.router)
```

- [ ] Start the server and verify it runs

```bash
cd backend && uvicorn main:app --reload
```

Expected: server starts, logs "Scheduler started", no errors. Visit `http://localhost:8000/health` → `{"status":"ok","last_refresh":null}`

- [ ] Commit

```bash
git add backend/main.py
git commit -m "feat: wire up FastAPI app with lifespan startup"
```

---

### Task 10: Run full test suite

- [ ] Run all tests

```bash
pytest tests/ -v
```

Expected: all tests PASS

- [ ] Commit any fixes if needed, then tag

```bash
git tag v0.1.0-backend
```
