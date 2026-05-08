import math
from collections import defaultdict
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Stock, DailyPrice, Fundamentals
from backend.schemas import RecommendRequest, RecommendResponse, StockResult
from backend.scorer import score_stocks

router = APIRouter()


def _bulk_fetch_prices(tickers: list[str], db: Session) -> dict[str, list[tuple]]:
    """Fetch all DailyPrice rows for the given tickers over the past 13 months in one query.
    Returns {ticker: [(date, close), ...]} sorted by date ascending."""
    cutoff = date.today() - timedelta(days=395)
    rows = (
        db.query(DailyPrice.ticker, DailyPrice.date, DailyPrice.close)
        .filter(DailyPrice.ticker.in_(tickers), DailyPrice.date >= cutoff)
        .order_by(DailyPrice.ticker, DailyPrice.date)
        .all()
    )
    by_ticker: dict[str, list[tuple]] = defaultdict(list)
    for ticker, dt, close in rows:
        by_ticker[ticker].append((dt, close))
    return dict(by_ticker)


def _momentum_from_prices(prices: list[tuple]) -> float:
    """1-year price change from a pre-fetched [(date, close)] list."""
    if not prices:
        return 0.0
    today = date.today()
    year_ago = today - timedelta(days=365)
    window = timedelta(days=7)

    recent_close = next(
        (close for dt, close in reversed(prices) if close and dt >= today - window), None
    )
    past_close = next(
        (close for dt, close in reversed(prices)
         if close and year_ago - window <= dt <= year_ago + window),
        None,
    )
    if not recent_close or not past_close or past_close == 0:
        return 0.0
    return (recent_close - past_close) / past_close


def _volatility_from_prices(prices: list[tuple]) -> float:
    """Annualised sample std dev of daily returns from a pre-fetched [(date, close)] list."""
    year_ago = date.today() - timedelta(days=365)
    closes = [close for dt, close in prices if close and dt >= year_ago]
    if len(closes) < 2:
        return 0.0
    returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance)


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.sector == req.sector).all()
    if not stocks:
        raise HTTPException(status_code=404, detail=f"No stocks found for sector '{req.sector}'")

    tickers = [s.ticker for s in stocks]

    fund_map = {
        f.ticker: f
        for f in db.query(Fundamentals).filter(Fundamentals.ticker.in_(tickers)).all()
    }

    price_map = _bulk_fetch_prices(tickers, db)

    stock_dicts = []
    for stock in stocks:
        fund = fund_map.get(stock.ticker)
        prices = price_map.get(stock.ticker, [])
        stock_dicts.append({
            "ticker": stock.ticker,
            "company_name": stock.company_name,
            "momentum_raw": _momentum_from_prices(prices),
            "volatility_raw": _volatility_from_prices(prices),
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
