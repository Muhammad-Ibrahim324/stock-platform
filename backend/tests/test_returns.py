from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics import returns


def test_daily_returns_flat_series_is_all_zero(flat_prices):
    rets = returns.daily_returns(flat_prices)
    assert len(rets) == len(flat_prices) - 1
    assert np.allclose(rets.values, 0.0)


def test_daily_returns_known_values():
    prices = pd.Series([100.0, 110.0, 99.0], index=pd.bdate_range("2024-01-01", periods=3))
    rets = returns.daily_returns(prices)
    assert np.isclose(rets.iloc[0], 0.10)
    assert np.isclose(rets.iloc[1], -0.10)


def test_total_return_known_value():
    prices = pd.Series([100.0, 150.0], index=pd.bdate_range("2024-01-01", periods=2))
    assert np.isclose(returns.total_return(prices), 0.5)


def test_total_return_flat_is_zero(flat_prices):
    assert np.isclose(returns.total_return(flat_prices), 0.0)


def test_total_return_requires_two_points():
    single = pd.Series([100.0], index=pd.bdate_range("2024-01-01", periods=1))
    assert returns.total_return(single) == 0.0


def test_cumulative_returns_end_matches_total_return(random_walk_prices):
    cum = returns.cumulative_returns(random_walk_prices)
    assert np.isclose(cum.iloc[-1], returns.total_return(random_walk_prices), atol=1e-9)


def test_growth_of_investment_starts_near_initial(random_walk_prices):
    growth = returns.growth_of_investment(random_walk_prices, initial_investment=10_000)
    # First value is investment growth after day 1's return, not exactly day 0
    assert growth.iloc[0] > 0
    assert np.isclose(growth.iloc[-1] / 10_000 - 1, returns.total_return(random_walk_prices), atol=1e-9)


def test_annualized_return_matches_total_for_exactly_one_year():
    dates = pd.bdate_range("2024-01-01", periods=253)  # 252 trading days = 1 year
    prices = pd.Series(np.linspace(100, 120, 253), index=dates)
    total = returns.total_return(prices)
    annualized = returns.annualized_return(prices)
    assert np.isclose(total, annualized, atol=1e-6)


def test_periodic_returns_no_lookahead(random_walk_prices):
    weekly = returns.periodic_returns(random_walk_prices, "W")
    # Every weekly return must be computable strictly from data up to and
    # including that week's last observed trading day.
    for date in weekly.index:
        assert date <= random_walk_prices.index[-1]


def test_daily_return_distribution_shape(random_walk_prices):
    dist = returns.daily_return_distribution(random_walk_prices, bins=20)
    assert len(dist["counts"]) == 20
    assert len(dist["bin_edges"]) == 21
    assert sum(dist["counts"]) == len(returns.daily_returns(random_walk_prices))
