from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics import backtesting


def test_sma_crossover_goes_long_on_a_sustained_uptrend(monotonic_up_prices):
    signal = backtesting.sma_crossover_signal(monotonic_up_prices, fast=10, slow=30)
    # Once both SMAs are defined on a strict uptrend, fast > slow, so the
    # tail of the signal should be long.
    assert signal.iloc[-1] == 1.0


def test_sma_crossover_is_flat_before_both_averages_are_defined(monotonic_up_prices):
    signal = backtesting.sma_crossover_signal(monotonic_up_prices, fast=10, slow=30)
    assert (signal.iloc[:9] == 0.0).all()


def test_rsi_mean_reversion_never_enters_on_a_pure_uptrend(monotonic_up_prices):
    # RSI stays pinned near 100 on an unbroken uptrend, so it never drops
    # below the oversold threshold and the strategy should stay flat.
    signal = backtesting.rsi_mean_reversion_signal(monotonic_up_prices, oversold=30, overbought=70)
    assert (signal == 0.0).all()


def test_rsi_mean_reversion_enters_and_exits_on_known_series():
    # A round trip designed to push RSI below 30 then back above 70.
    down = np.linspace(100, 70, 20)
    up = np.linspace(70, 130, 20)
    prices = pd.Series(np.concatenate([down, up]), index=pd.bdate_range("2024-01-01", periods=40))
    signal = backtesting.rsi_mean_reversion_signal(prices, window=14, oversold=30, overbought=70)
    assert signal.max() == 1.0  # it did enter at some point
    assert signal.iloc[-1] == 0.0  # and exited by the end of the strong rally


def test_flat_positions_leave_equity_curve_at_one(random_walk_prices):
    flat = pd.Series(0.0, index=random_walk_prices.index)
    result = backtesting.run_backtest(random_walk_prices, flat)
    assert np.allclose(result["equity_curve"].values, 1.0)
    assert result["num_trades"] == 0
    assert result["total_costs_pct"] == 0.0


def test_always_long_matches_buy_and_hold_after_entry_cost(random_walk_prices):
    always_long = pd.Series(1.0, index=random_walk_prices.index)
    zero_cost = backtesting.run_backtest(always_long, always_long, transaction_cost_bps=0, slippage_bps=0)
    # With zero costs, holding a position of 1.0 the entire time (after the
    # one-day entry lag from the shift) should reproduce buy-and-hold
    # almost exactly, aside from that first-day lag.
    assert np.isclose(zero_cost["equity_curve"].iloc[-1], zero_cost["buy_hold_curve"].iloc[-1], rtol=0.02)


def test_zero_cost_backtest_has_no_costs(random_walk_prices):
    signal = backtesting.sma_crossover_signal(random_walk_prices, fast=10, slow=30)
    result = backtesting.run_backtest(random_walk_prices, signal, transaction_cost_bps=0, slippage_bps=0)
    assert result["total_costs_pct"] == 0.0


def test_higher_costs_never_produce_higher_ending_equity(random_walk_prices):
    signal = backtesting.sma_crossover_signal(random_walk_prices, fast=10, slow=30)
    cheap = backtesting.run_backtest(random_walk_prices, signal, transaction_cost_bps=1, slippage_bps=1)
    expensive = backtesting.run_backtest(random_walk_prices, signal, transaction_cost_bps=100, slippage_bps=100)
    assert expensive["equity_curve"].iloc[-1] <= cheap["equity_curve"].iloc[-1]
    assert expensive["total_costs_pct"] >= cheap["total_costs_pct"]


def test_signal_computed_today_cannot_affect_todays_own_return():
    """No-lookahead at the backtest level: a signal that flips to long on
    day t must not capture day t's return — only day t+1 onward, since you
    can't act on a same-day-close signal before that same close."""
    dates = pd.bdate_range("2024-01-01", periods=5)
    # A sharp, known jump on day index 2 (from 100 to 200).
    prices = pd.Series([100, 100, 200, 200, 200], index=dates, dtype=float)
    # Signal flips to long exactly on the jump day.
    signal = pd.Series([0, 0, 1, 1, 1], index=dates, dtype=float)

    result = backtesting.run_backtest(prices, signal, transaction_cost_bps=0, slippage_bps=0)
    strategy_returns = result["strategy_returns"]
    # The 100% jump happens going INTO day index 2 (pct_change at index 2).
    # Since held_position at index 2 is positions.shift(1) = signal at
    # index 1 = 0, the strategy must NOT capture that jump.
    assert np.isclose(strategy_returns.iloc[2], 0.0)
    # It should capture the (zero, in this case) return on day 3 instead,
    # once the position from day 2's signal is actually held.
    assert np.isclose(strategy_returns.iloc[3], 0.0)  # price is flat 200->200 anyway


def test_num_trades_counts_position_changes():
    dates = pd.bdate_range("2024-01-01", periods=7)
    prices = pd.Series([100, 101, 102, 103, 104, 105, 106], index=dates, dtype=float)
    # Signal: 0 -> 1 -> 1 -> 0 -> 0 -> 1 -> 1
    # Held position is this lagged by one day (you act on yesterday's
    # signal), so its transitions land one day later: 0->1 (enter),
    # 1->0 (exit), 0->1 (enter again) = 3 trades, visible once the last
    # signal transition has had a day to show up in the held position.
    signal = pd.Series([0, 1, 1, 0, 0, 1, 1], index=dates, dtype=float)
    result = backtesting.run_backtest(prices, signal)
    assert result["num_trades"] == 3
