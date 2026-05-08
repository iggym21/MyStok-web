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
