import logging
import math
from sqlalchemy.orm import Session
from sqlalchemy import insert
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

    stocks: dict[str, dict] = {}
    for _, row in df.drop_duplicates("ticker").iterrows():
        stocks[row["ticker"]] = {
            "ticker": row["ticker"],
            "company_name": _none_if_nan(row.get("company_name")),
            "industry": _none_if_nan(row.get("industry")),
            "country": _none_if_nan(row.get("country")),
            "sector": None,
        }

    prices = []
    for _, row in df.iterrows():
        prices.append({
            "ticker": row["ticker"],
            "date": row["date"].date() if hasattr(row["date"], "date") else row["date"],
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
