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
