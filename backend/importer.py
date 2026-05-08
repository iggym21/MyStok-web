import logging
import math
from sqlalchemy.orm import Session
from sqlalchemy import insert
import pandas as pd
from backend.models import Stock, DailyPrice

logger = logging.getLogger(__name__)

INDUSTRY_TO_SECTOR: dict[str, str] = {
    "technology": "Technology",
    "social media": "Technology",
    "gaming": "Technology",
    "entertainment": "Communication Services",
    "music": "Communication Services",
    "finance": "Financial Services",
    "financial services": "Financial Services",
    "cryptocurrency": "Financial Services",
    "healthcare": "Healthcare",
    "automotive": "Consumer Cyclical",
    "retail": "Consumer Cyclical",
    "e-commerce": "Consumer Cyclical",
    "apparel": "Consumer Cyclical",
    "footwear": "Consumer Cyclical",
    "luxury goods": "Consumer Cyclical",
    "hospitality": "Consumer Cyclical",
    "fitness": "Consumer Cyclical",
    "consumer goods": "Consumer Defensive",
    "food": "Consumer Defensive",
    "food & beverage": "Consumer Defensive",
    "logistics": "Industrials",
    "manufacturing": "Industrials",
    "aviation": "Industrials",
}

CSV_COLUMN_MAP = {
    "Date": "date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
    "Brand_Name": "company_name",
    "Ticker": "ticker",
    "Industry_Tag": "industry",
    "Country": "country",
}


def _none_if_nan(value):
    if value is None:
        return None
    try:
        if math.isnan(float(value)):
            return None
    except (TypeError, ValueError):
        pass
    return value


def parse_csv(csv_path: str) -> tuple[dict, list[dict]]:
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df.rename(columns=CSV_COLUMN_MAP, inplace=True)

    # Normalize date to date-only (strips timezone and time components)
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.date

    # Drop duplicate (ticker, date) rows — dataset occasionally has multiple
    # entries per trading day; keep the last one for each pair
    df = df.drop_duplicates(subset=["ticker", "date"], keep="last")

    stocks: dict[str, dict] = {}
    for _, row in df.drop_duplicates("ticker").iterrows():
        stocks[row["ticker"]] = {
            "ticker": row["ticker"],
            "company_name": _none_if_nan(row.get("company_name")),
            "industry": _none_if_nan(row.get("industry")),
            "country": _none_if_nan(row.get("country")),
            "sector": INDUSTRY_TO_SECTOR.get((row.get("industry") or "").lower()),
        }

    prices = []
    for _, row in df.iterrows():
        prices.append({
            "ticker": row["ticker"],
            "date": row["date"],
            "open": _none_if_nan(row.get("open")),
            "high": _none_if_nan(row.get("high")),
            "low": _none_if_nan(row.get("low")),
            "close": _none_if_nan(row.get("close")),
            "volume": _none_if_nan(row.get("volume")),
        })

    return stocks, prices


def import_stocks(csv_path: str, db: Session) -> None:
    if db.query(Stock).count() > 0:
        logger.info("Database already populated, skipping import")
        return

    logger.info("Starting CSV import from %s", csv_path)
    stocks, prices = parse_csv(csv_path)

    if not stocks:
        logger.warning("CSV produced no stocks, skipping import")
        return

    batch_size = 10_000
    try:
        db.execute(insert(Stock), list(stocks.values()))
        for i in range(0, len(prices), batch_size):
            db.execute(insert(DailyPrice), prices[i : i + batch_size])
        db.commit()
        logger.info("Imported %d stocks and %d price rows", len(stocks), len(prices))
    except Exception:
        db.rollback()
        raise
