import logging
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

    db.execute(insert(Stock), list(stocks.values()))

    batch_size = 10_000
    for i in range(0, len(prices), batch_size):
        db.execute(insert(DailyPrice), prices[i : i + batch_size])
        db.commit()

    logger.info("Imported %d stocks and %d price rows", len(stocks), len(prices))
