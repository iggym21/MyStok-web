import math


def compute_weights(risk_level: int, duration: str) -> dict[str, float]:
    r = (risk_level - 1) / 4
    d = {"short": 0.0, "medium": 0.5, "long": 1.0}[duration]

    raw = {
        "momentum":  0.10 + 0.30 * r,
        "stability": 0.35 - 0.25 * r,
        "income":    0.25 - 0.10 * r + 0.10 * d,
        "value":     0.20 - 0.05 * r,
        "size":      0.10 - 0.05 * r,
    }
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}


def normalize(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _value_score_raw(pe_ratio: float | None) -> float:
    if pe_ratio is None or pe_ratio <= 0:
        return 0.0
    return 1.0 / min(pe_ratio, 100.0)


def score_stocks(
    stocks: list[dict],
    risk_level: int,
    duration: str,
) -> list[dict]:
    if not stocks:
        return []

    weights = compute_weights(risk_level, duration)

    momentum_vals  = normalize([s["momentum_raw"] for s in stocks])
    stability_vals = normalize([1.0 - s["volatility_raw"] for s in stocks])
    income_vals    = normalize([s.get("dividend_yield") or 0.0 for s in stocks])
    value_raws     = [_value_score_raw(s.get("pe_ratio")) for s in stocks]
    value_vals     = normalize(value_raws)
    size_vals      = normalize([math.log1p(s.get("market_cap") or 0) for s in stocks])

    results = []
    for i, stock in enumerate(stocks):
        factors = {
            "momentum":  momentum_vals[i],
            "stability": stability_vals[i],
            "income":    income_vals[i],
            "value":     value_vals[i],
            "size":      size_vals[i],
        }
        score = sum(weights[f] * factors[f] for f in factors)
        results.append({**stock, **factors, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
