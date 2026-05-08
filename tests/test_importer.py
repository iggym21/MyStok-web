import pytest
import pandas as pd
from unittest.mock import MagicMock
from backend.importer import parse_csv, import_stocks

def test_parse_csv_returns_tickers_and_prices(tmp_path):
    csv = tmp_path / "stocks.csv"
    csv.write_text(
        "Date,Open,High,Low,Close,Volume,Brand_Name,Ticker,Industry_Tag,Country\n"
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
        "Date,Open,High,Low,Close,Volume,Brand_Name,Ticker,Industry_Tag,Country\n"
        "2023-01-01,100,110,90,105,1000000,Apple Inc,AAPL,Software,USA\n"
        "2023-01-02,105,115,100,110,1200000,Apple Inc,AAPL,Software,USA\n"
    )
    stocks, prices = parse_csv(str(csv))
    assert len(stocks) == 1
