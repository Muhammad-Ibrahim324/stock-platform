from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics import risk


def test_max_drawdown_exact_known_value(known_drawdown_prices):
    result = risk.max_drawdown(known_drawdown_prices)
    assert np.isclose(result["max_drawdown_pct"], -0.25, atol=1e-9)
    # Peak is the 120 print (index 2), trough is the 90 print (index 5).
    assert result["peak_date"] == known_drawdown_prices.index[2].date().isoformat()
    assert result["trough_date"] == known_drawdown_prices.index[5].date().isoformat()
    # Series never climbs back to 120 after the trough in this fixture.
    assert result["recovery_date"] is None
    assert result["recovery_days"] is None


def test_current_drawdown_exact_known_value(known_drawdown_prices):
    # Last close 108 vs running peak 120 => exactly -10%.
    assert np.isclose(risk.current_drawdown(known_drawdown_prices), -0.10, atol=1e-9)


def test_monotonic_increase_has_zero_drawdown(monotonic_up_prices):
    result = risk.max_drawdown(monotonic_up_prices)
    assert np.isclose(result["max_drawdown_pct"], 0.0, atol=1e-9)
    assert np.isclose(risk.current_drawdown(monotonic_up_prices), 0.0, atol=1e-9)


def test_flat_series_has_zero_volatility_and_sharpe(flat_prices):
    assert np.isclose(risk.annualized_volatility(flat_prices), 0.0, atol=1e-9)
    # No division-by-zero explosions on a zero-variance series.
    assert risk.sharpe_ratio(flat_prices) == 0.0
    # With a 0% risk-free hurdle, a flat (0% return) series has no shortfall
    # below the hurdle, so downside deviation is exactly zero too.
    assert risk.sortino_ratio(flat_prices, risk_free_rate=0.0) == 0.0


def test_sortino_is_negative_when_flat_series_trails_a_positive_hurdle(flat_prices):
    # A 0%-return stock measured against a positive risk-free rate is
    # genuinely underperforming every single day, so Sortino (unlike
    # Sharpe, which measures variance rather than shortfall) should
    # reflect that as a real negative number, not zero.
    assert risk.sortino_ratio(flat_prices, risk_free_rate=0.04) < 0


def test_value_at_risk_is_negative_for_a_volatile_series(random_walk_prices):
    var95 = risk.value_at_risk(random_walk_prices, confidence=0.95)
    assert var95 < 0


def test_cvar_is_at_least_as_severe_as_var(random_walk_prices):
    var95 = risk.value_at_risk(random_walk_prices, confidence=0.95)
    cvar95 = risk.conditional_value_at_risk(random_walk_prices, confidence=0.95)
    # Expected shortfall in the tail must be <= the cutoff itself (more negative or equal).
    assert cvar95 <= var95


def test_beta_of_asset_against_itself_is_one(random_walk_prices):
    assert np.isclose(risk.beta(random_walk_prices, random_walk_prices), 1.0, atol=1e-9)


def test_beta_matches_known_linear_relationship():
    # risk.beta() is computed on simple (pct_change) returns, so the
    # fixture must be built with cumprod(1+r) rather than exp(cumsum(r))
    # (log returns) — the two only coincide in the small-return limit,
    # and daily vol of 1% is large enough that the difference would
    # otherwise show up as ~0.1% noise in the recovered beta.
    rng = np.random.default_rng(3)
    bench_returns = rng.normal(0.0005, 0.01, 300)
    asset_returns = 2.0 * bench_returns  # exact 2x relationship => beta should be 2

    dates = pd.bdate_range("2023-01-01", periods=301)
    bench_prices = pd.Series(4000 * np.insert(1 + bench_returns, 0, 1.0).cumprod(), index=dates)
    asset_prices = pd.Series(100 * np.insert(1 + asset_returns, 0, 1.0).cumprod(), index=dates)

    computed_beta = risk.beta(asset_prices, bench_prices)
    assert np.isclose(computed_beta, 2.0, atol=1e-6)


def test_correlation_is_bounded(random_walk_prices, benchmark_prices):
    corr = risk.correlation(random_walk_prices, benchmark_prices)
    assert -1.0 <= corr <= 1.0


def test_risk_summary_without_benchmark_leaves_beta_none(random_walk_prices):
    summary = risk.risk_summary(random_walk_prices, None)
    assert summary["beta"] is None
    assert summary["correlation_to_benchmark"] is None


def test_risk_summary_with_benchmark_populates_beta(random_walk_prices, benchmark_prices):
    summary = risk.risk_summary(random_walk_prices, benchmark_prices)
    assert summary["beta"] is not None
    assert summary["correlation_to_benchmark"] is not None


def test_correlation_matrix_diagonal_is_one(random_walk_prices, benchmark_prices):
    matrix = risk.correlation_matrix({"A": random_walk_prices, "B": benchmark_prices})
    assert np.isclose(matrix["A"]["A"], 1.0, atol=1e-9)
    assert np.isclose(matrix["B"]["B"], 1.0, atol=1e-9)


def test_correlation_matrix_is_symmetric(random_walk_prices, benchmark_prices):
    matrix = risk.correlation_matrix({"A": random_walk_prices, "B": benchmark_prices})
    assert np.isclose(matrix["A"]["B"], matrix["B"]["A"], atol=1e-9)


def test_correlation_matrix_matches_pairwise_correlation(random_walk_prices, benchmark_prices):
    matrix = risk.correlation_matrix({"A": random_walk_prices, "B": benchmark_prices})
    pairwise = risk.correlation(random_walk_prices, benchmark_prices)
    assert np.isclose(matrix["A"]["B"], pairwise, atol=1e-9)
