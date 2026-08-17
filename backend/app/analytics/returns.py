"""Return calculations.

All functions take a pandas Series of adjusted-close prices indexed by
trade date (ascending) and return either a Series or a scalar. Nothing
here looks at data past the last index entry — these are pure, stateless
transforms of whatever history is handed in, which is what keeps them
safe to reuse inside walk-forward forecasting/backtesting later without
introducing look-ahead bias.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def daily_returns(prices: pd.Series) -> pd.Series:
    """Simple daily percentage returns. First value is dropped (no prior day)."""
    return prices.pct_change().dropna()


def log_returns(prices: pd.Series) -> pd.Series:
    """Log returns — additive across time, used by the risk module."""
    return np.log(prices / prices.shift(1)).dropna()


def periodic_returns(prices: pd.Series, rule: str) -> pd.Series:
    """Resample to a coarser period and compute returns over each bucket.

    `rule` is a pandas offset alias: 'W' weekly, 'ME' month-end, 'YE' year-end.
    Buckets are labeled by their start (`label="left"`) so a label is
    always at or before every trading day it summarizes — using the
    default right/end label can date a bucket past the last real trading
    day it contains (e.g. a week ending Sunday when data stops Friday),
    which reads like the return used information from beyond the data.
    """
    resampled = prices.resample(rule, label="left").last().dropna()
    return resampled.pct_change().dropna()


def cumulative_returns(prices: pd.Series) -> pd.Series:
    """Growth of $1 invested at the start of the series, as a return series
    (0.0 = flat, 0.84 = +84%)."""
    rets = daily_returns(prices)
    return (1 + rets).cumprod() - 1


def growth_of_investment(prices: pd.Series, initial_investment: float = 10_000.0) -> pd.Series:
    """Dollar value of a hypothetical initial investment held over the period."""
    cum = cumulative_returns(prices)
    return initial_investment * (1 + cum)


def total_return(prices: pd.Series) -> float:
    """Total return over the full window, e.g. 0.843 for +84.3%."""
    if len(prices) < 2:
        return 0.0
    return float(prices.iloc[-1] / prices.iloc[0] - 1)


def annualized_return(prices: pd.Series) -> float:
    """CAGR based on the number of trading days actually observed."""
    n = len(prices)
    if n < 2:
        return 0.0
    total = prices.iloc[-1] / prices.iloc[0]
    years = (n - 1) / TRADING_DAYS_PER_YEAR
    if years <= 0 or total <= 0:
        return 0.0
    return float(total ** (1 / years) - 1)


def daily_return_distribution(prices: pd.Series, bins: int = 40) -> dict:
    """Histogram-ready bucketing of the daily return distribution."""
    rets = daily_returns(prices) * 100  # as percent for display
    counts, edges = np.histogram(rets, bins=bins)
    return {
        "bin_edges": [float(e) for e in edges],
        "counts": [int(c) for c in counts],
        "mean_pct": float(rets.mean()) if len(rets) else 0.0,
        "std_pct": float(rets.std()) if len(rets) else 0.0,
    }
