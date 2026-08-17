"""Risk metrics.

Formulas and assumptions are documented inline and mirrored in
`docs/METHODOLOGY.md` so a reviewer can check the math without reading code.
All "annualized" figures assume 252 trading days/year, the market-standard
convention. Risk-free rate is annualized and configurable (PRD §12).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics.returns import TRADING_DAYS_PER_YEAR, daily_returns


def annualized_volatility(prices: pd.Series) -> float:
    """Std dev of daily returns, annualized by sqrt(252).

    This assumes returns are i.i.d., which real markets violate (volatility
    clusters), so treat this as a standard summary statistic, not a
    forecast of next year's actual volatility.
    """
    rets = daily_returns(prices)
    if len(rets) < 2:
        return 0.0
    return float(rets.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(prices: pd.Series, risk_free_rate: float = 0.04) -> float:
    """Annualized Sharpe ratio: (mean annual return - risk-free rate) / annual volatility.

    `risk_free_rate` is an annualized rate (e.g. 0.04 = 4%); it's converted
    to a daily rate before subtracting from daily returns.
    """
    rets = daily_returns(prices)
    if len(rets) < 2:
        return 0.0
    daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    excess = rets - daily_rf
    vol = excess.std(ddof=1)
    if vol == 0:
        return 0.0
    return float((excess.mean() / vol) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sortino_ratio(prices: pd.Series, risk_free_rate: float = 0.04) -> float:
    """Like Sharpe, but the denominator only penalizes downside deviation
    (returns below the risk-free rate), since upside volatility isn't "risk"
    an investor is trying to avoid."""
    rets = daily_returns(prices)
    if len(rets) < 2:
        return 0.0
    daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    excess = rets - daily_rf
    downside = excess[excess < 0]
    if len(downside) == 0:
        return 0.0
    downside_dev = np.sqrt((downside**2).mean())
    if downside_dev == 0:
        return 0.0
    return float((excess.mean() / downside_dev) * np.sqrt(TRADING_DAYS_PER_YEAR))


def drawdown_series(prices: pd.Series) -> pd.Series:
    """Running drawdown from the trailing peak, as a negative fraction
    (e.g. -0.15 = currently 15% below the highest close to date)."""
    running_max = prices.cummax()
    return prices / running_max - 1


def max_drawdown(prices: pd.Series) -> dict:
    """Worst peak-to-trough decline, plus when it happened and how long
    recovery took (None if the series never recovered)."""
    dd = drawdown_series(prices)
    if dd.empty:
        return {
            "max_drawdown_pct": 0.0,
            "peak_date": None,
            "trough_date": None,
            "recovery_date": None,
            "recovery_days": None,
        }

    trough_idx = dd.idxmin()
    max_dd = float(dd.min())

    prices_before_trough = prices.loc[:trough_idx]
    peak_idx = prices_before_trough.idxmax()

    peak_price = prices.loc[peak_idx]
    after_trough = prices.loc[trough_idx:]
    recovered = after_trough[after_trough >= peak_price]
    recovery_idx = recovered.index[0] if len(recovered) > 0 else None
    recovery_days = (recovery_idx - trough_idx).days if recovery_idx is not None else None

    return {
        "max_drawdown_pct": max_dd,
        "peak_date": peak_idx.date().isoformat() if hasattr(peak_idx, "date") else str(peak_idx),
        "trough_date": trough_idx.date().isoformat() if hasattr(trough_idx, "date") else str(trough_idx),
        "recovery_date": (recovery_idx.date().isoformat() if recovery_idx is not None and hasattr(recovery_idx, "date") else None),
        "recovery_days": recovery_days,
    }


def current_drawdown(prices: pd.Series) -> float:
    """How far below the all-time (in-window) high the latest close sits."""
    dd = drawdown_series(prices)
    return float(dd.iloc[-1]) if len(dd) else 0.0


def value_at_risk(prices: pd.Series, confidence: float = 0.95) -> float:
    """Historical (non-parametric) VaR: the daily loss threshold that
    returns have not exceeded `confidence`% of the time, historically.
    Returned as a negative fraction (e.g. -0.032 = a 3.2% one-day loss)."""
    rets = daily_returns(prices)
    if len(rets) < 2:
        return 0.0
    return float(np.percentile(rets, (1 - confidence) * 100))


def conditional_value_at_risk(prices: pd.Series, confidence: float = 0.95) -> float:
    """Expected shortfall: the average return on the days at or worse than
    the VaR threshold. Always <= VaR in magnitude terms since it captures
    the tail, not just the cutoff."""
    rets = daily_returns(prices)
    if len(rets) < 2:
        return 0.0
    var = value_at_risk(prices, confidence)
    tail = rets[rets <= var]
    if len(tail) == 0:
        return var
    return float(tail.mean())


def beta(asset_prices: pd.Series, benchmark_prices: pd.Series) -> float:
    """Covariance(asset, benchmark) / Variance(benchmark), on daily returns
    aligned by date. Requires at least 2 overlapping observations."""
    asset_rets = daily_returns(asset_prices)
    bench_rets = daily_returns(benchmark_prices)
    aligned = pd.concat([asset_rets, bench_rets], axis=1, join="inner").dropna()
    if len(aligned) < 2:
        return 0.0
    cov_matrix = aligned.cov()
    bench_var = cov_matrix.iloc[1, 1]
    if bench_var == 0:
        return 0.0
    return float(cov_matrix.iloc[0, 1] / bench_var)


def correlation(asset_prices: pd.Series, benchmark_prices: pd.Series) -> float:
    asset_rets = daily_returns(asset_prices)
    bench_rets = daily_returns(benchmark_prices)
    aligned = pd.concat([asset_rets, bench_rets], axis=1, join="inner").dropna()
    if len(aligned) < 2:
        return 0.0
    return float(aligned.corr().iloc[0, 1])


def correlation_matrix(prices_by_ticker: dict[str, pd.Series]) -> dict[str, dict[str, float]]:
    """Pairwise correlation of daily returns across N tickers, aligned by
    date (inner join — only dates every ticker has data for are used)."""
    tickers = list(prices_by_ticker.keys())
    returns_df = pd.concat(
        {ticker: daily_returns(prices) for ticker, prices in prices_by_ticker.items()}, axis=1, join="inner"
    ).dropna()

    if len(returns_df) < 2:
        return {t: {u: (1.0 if t == u else 0.0) for u in tickers} for t in tickers}

    corr = returns_df.corr()
    return {t: {u: float(corr.loc[t, u]) for u in tickers} for t in tickers}


def risk_summary(prices: pd.Series, benchmark_prices: pd.Series | None, risk_free_rate: float = 0.04) -> dict:
    """Bundles every risk metric into one dict for the /risk API endpoint."""
    dd = max_drawdown(prices)
    summary = {
        "annualized_volatility": annualized_volatility(prices),
        "sharpe_ratio": sharpe_ratio(prices, risk_free_rate),
        "sortino_ratio": sortino_ratio(prices, risk_free_rate),
        "max_drawdown_pct": dd["max_drawdown_pct"],
        "max_drawdown_peak_date": dd["peak_date"],
        "max_drawdown_trough_date": dd["trough_date"],
        "max_drawdown_recovery_date": dd["recovery_date"],
        "max_drawdown_recovery_days": dd["recovery_days"],
        "current_drawdown_pct": current_drawdown(prices),
        "value_at_risk_95": value_at_risk(prices, 0.95),
        "conditional_value_at_risk_95": conditional_value_at_risk(prices, 0.95),
        "risk_free_rate_assumed": risk_free_rate,
        "beta": None,
        "correlation_to_benchmark": None,
    }
    if benchmark_prices is not None and len(benchmark_prices) > 1:
        summary["beta"] = beta(prices, benchmark_prices)
        summary["correlation_to_benchmark"] = correlation(prices, benchmark_prices)
    return summary
