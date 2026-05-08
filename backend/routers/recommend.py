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
        .filter(
            DailyPrice.ticker == ticker,
            DailyPrice.date >= year_ago - timedelta(days=7),
            DailyPrice.date <= year_ago + timedelta(days=7),
        )
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
    stocks = db.query(Stock).filter(Stock.sector == req.sector).all()
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
