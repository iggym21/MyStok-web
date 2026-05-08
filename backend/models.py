from datetime import date, datetime
from sqlalchemy import String, Float, Integer, BigInteger, Date, DateTime, ForeignKey
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
    market_cap: Mapped[int | None] = mapped_column(BigInteger)
    week52_high: Mapped[float | None] = mapped_column(Float)
    week52_low: Mapped[float | None] = mapped_column(Float)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime)
