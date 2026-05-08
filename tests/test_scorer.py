import pytest
from backend.scorer import compute_weights, normalize, score_stocks

def test_compute_weights_sum_to_one():
    for risk in range(1, 6):
        for duration in ["short", "medium", "long"]:
            weights = compute_weights(risk, duration)
            assert abs(sum(weights.values()) - 1.0) < 1e-9

def test_compute_weights_aggressive_favors_momentum():
    conservative = compute_weights(1, "long")
    aggressive = compute_weights(5, "long")
    assert aggressive["momentum"] > conservative["momentum"]
    assert aggressive["stability"] < conservative["stability"]

def test_normalize_returns_zero_to_one():
    values = [10.0, 20.0, 30.0]
    result = normalize(values)
    assert result[0] == pytest.approx(0.0)
    assert result[2] == pytest.approx(1.0)

def test_normalize_constant_series_returns_half():
    values = [5.0, 5.0, 5.0]
    result = normalize(values)
    assert all(v == pytest.approx(0.5) for v in result)

def test_score_stocks_returns_sorted_descending():
    stocks = [
        {"ticker": "A", "momentum_raw": 0.5, "volatility_raw": 0.1,
         "dividend_yield": 0.02, "pe_ratio": 15.0, "market_cap": 1_000_000_000},
        {"ticker": "B", "momentum_raw": 0.1, "volatility_raw": 0.5,
         "dividend_yield": 0.00, "pe_ratio": 80.0, "market_cap": 100_000_000},
    ]
    results = score_stocks(stocks, risk_level=5, duration="long")
    assert results[0]["score"] >= results[1]["score"]

def test_score_stocks_includes_factor_breakdown():
    stocks = [
        {"ticker": "A", "momentum_raw": 0.3, "volatility_raw": 0.2,
         "dividend_yield": 0.01, "pe_ratio": 20.0, "market_cap": 500_000_000},
    ]
    results = score_stocks(stocks, risk_level=3, duration="medium")
    assert "momentum" in results[0]
    assert "stability" in results[0]
    assert "income" in results[0]
    assert "value" in results[0]
    assert "size" in results[0]
    assert 0.0 <= results[0]["score"] <= 1.0

def test_score_stocks_empty_returns_empty():
    assert score_stocks([], risk_level=3, duration="medium") == []

def test_score_stocks_negative_pe_gives_zero_value():
    stocks = [
        {"ticker": "A", "momentum_raw": 0.3, "volatility_raw": 0.2,
         "dividend_yield": 0.01, "pe_ratio": -5.0, "market_cap": 500_000_000},
        {"ticker": "B", "momentum_raw": 0.3, "volatility_raw": 0.2,
         "dividend_yield": 0.01, "pe_ratio": 20.0, "market_cap": 500_000_000},
    ]
    results = score_stocks(stocks, risk_level=3, duration="medium")
    a = next(r for r in results if r["ticker"] == "A")
    b = next(r for r in results if r["ticker"] == "B")
    # A has negative P/E → value_raw=0; B has positive P/E → value_raw>0
    # After normalization B should have higher value score than A
    assert b["value"] >= a["value"]
