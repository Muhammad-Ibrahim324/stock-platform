"""Portfolio analytics.

The per-holding gain/loss numbers (current value vs. cost basis) are exact
— they come straight from the shares and cost basis the user entered.

The portfolio-level risk numbers (volatility, Sharpe, drawdown, beta) are
a hypothetical: "how would the *current* mix of holdings, at *today's*
share counts, have behaved over the trailing period" — not the portfolio's
actual realized history, since holdings were presumably bought at
different times. This is a standard simplification (most portfolio tools
do this for a quick risk read) but it's a simplification worth being
explicit about rather than presenting as literal realized history.
"""

from __future__ import annotations

import pandas as pd

from app.analytics import returns as returns_analytics
from app.analytics import risk as risk_analytics


def portfolio_value_series(holdings_shares: dict[str, float], prices_by_ticker: dict[str, pd.Series]) -> pd.Series:
    """Combine each held ticker's price history into one portfolio value
    series, using each ticker's CURRENT share count projected across the
    whole window (see module docstring). Aligned by date (inner join —
    only dates every held ticker has data for)."""
    if not holdings_shares or not prices_by_ticker:
        return pd.Series(dtype=float)

    aligned = pd.concat(prices_by_ticker, axis=1, join="inner")
    if aligned.empty:
        return pd.Series(dtype=float)

    value = sum(aligned[ticker] * shares for ticker, shares in holdings_shares.items() if ticker in aligned.columns)
    return value


def portfolio_risk_summary(
    value_series: pd.Series, benchmark_prices: pd.Series | None, risk_free_rate: float = 0.04
) -> dict:
    """Same shape as risk_analytics.risk_summary — the portfolio value
    series is just treated as a price series, since every function in
    the risk module only cares about a chronological series of values."""
    if len(value_series) < 2:
        return {
            "annualized_volatility": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "beta": None,
            "correlation_to_benchmark": None,
        }
    return risk_analytics.risk_summary(value_series, benchmark_prices, risk_free_rate)


def allocation_by_key(current_values: dict[str, float], key_by_ticker: dict[str, str]) -> dict[str, float]:
    """Group current holding values by an arbitrary key (sector, ticker,
    etc.) and return each group's weight as a fraction of total value."""
    total = sum(current_values.values())
    if total <= 0:
        return {}
    grouped: dict[str, float] = {}
    for ticker, value in current_values.items():
        key = key_by_ticker.get(ticker, "Unknown")
        grouped[key] = grouped.get(key, 0.0) + value
    return {key: value / total for key, value in grouped.items()}
