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
