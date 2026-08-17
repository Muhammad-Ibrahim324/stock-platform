"""Strategy backtesting.

A signal (the position to hold each day) is turned into an equity curve
that accounts for transaction costs and slippage, then scored with the
exact same risk/return functions used everywhere else in this app —
`app/analytics/risk.py` and `app/analytics/returns.py` don't know or care
whether the series they're handed is a stock price or a backtest's
equity curve, so nothing new had to be built to score one.

No-lookahead is enforced structurally, not just by convention: a signal
computed from data through day t can only be acted on starting day t+1
(`positions.shift(1)`) — you can't trade at today's close using a
same-day-close-derived signal before the market has actually closed.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from app.analytics import technicals

StrategyName = Literal["sma_crossover", "rsi_mean_reversion", "buy_and_hold"]


def sma_crossover_signal(close: pd.Series, fast: int = 20, slow: int = 50) -> pd.Series:
    """Long while the fast SMA is above the slow SMA, flat otherwise.
    Long-only (0/1) — no shorting, which keeps the transaction-cost and
    drawdown story simple to reason about."""
    fast_sma = technicals.sma(close, fast)
    slow_sma = technicals.sma(close, slow)
    signal = (fast_sma > slow_sma).astype(float)
    signal[fast_sma.isna() | slow_sma.isna()] = 0.0
    return signal


def rsi_mean_reversion_signal(close: pd.Series, window: int = 14, oversold: float = 30, overbought: float = 70) -> pd.Series:
    """Enter long when RSI drops below `oversold`, exit back to flat once
    RSI rises above `overbought`. Stateful (needs a loop — this isn't a
    simple pointwise threshold since the position persists between the
    entry and exit signals)."""
    rsi = technicals.rsi(close, window)
    position = 0.0
    values = []
    for val in rsi:
        if pd.isna(val):
            values.append(0.0)
            continue
        if val < oversold:
            position = 1.0
        elif val > overbought:
            position = 0.0
        values.append(position)
    return pd.Series(values, index=close.index)


def run_backtest(
    close: pd.Series,
    positions: pd.Series,
    *,
    transaction_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict:
    """Simulate holding `positions` (0-1, or -1 to 1 if shorting) against
    `close`, deducting costs whenever the position changes.

    Returns a dict with the equity curve (starting at 1.0), the
    buy-and-hold equity curve for comparison, and the number of position
    changes ("trades").
    """
    asset_returns = close.pct_change().fillna(0)
    held_position = positions.shift(1).fillna(0)  # can only act on yesterday's signal

    position_change = held_position.diff().abs()
    position_change.iloc[0] = held_position.iloc[0]  # entering the very first position is also a "trade"
    cost_rate = (transaction_cost_bps + slippage_bps) / 10_000
    costs = position_change * cost_rate

    strategy_returns = held_position * asset_returns - costs
    equity_curve = (1 + strategy_returns).cumprod()
    buy_hold_curve = (1 + asset_returns).cumprod()

    num_trades = int((position_change > 0).sum())

    return {
        "equity_curve": equity_curve,
        "buy_hold_curve": buy_hold_curve,
        "strategy_returns": strategy_returns,
        "num_trades": num_trades,
        "total_costs_pct": float(costs.sum() * 100),
    }
