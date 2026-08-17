from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics import technicals


def test_sma_known_value():
    prices = pd.Series([1, 2, 3, 4, 5], index=pd.bdate_range("2024-01-01", periods=5))
    result = technicals.sma(prices, window=3)
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert np.isclose(result.iloc[2], 2.0)  # mean(1,2,3)
    assert np.isclose(result.iloc[3], 3.0)  # mean(2,3,4)
    assert np.isclose(result.iloc[4], 4.0)  # mean(3,4,5)


def test_sma_of_flat_series_equals_the_constant(flat_prices):
    result = technicals.sma(flat_prices, window=20)
    assert np.allclose(result.dropna().values, 100.0)


def test_ema_reacts_faster_than_sma_to_a_shock():
    # A flat series with one upward jump: EMA should move toward the jump
    # faster than an equal-window SMA, since it weights recent data more.
    prices = pd.Series([100.0] * 30 + [150.0] * 10, index=pd.bdate_range("2024-01-01", periods=40))
    sma_20 = technicals.sma(prices, 20)
    ema_20 = technicals.ema(prices, 20)
    assert ema_20.iloc[-1] > sma_20.iloc[-1]


def test_rsi_stays_within_bounds(random_walk_prices):
    result = technicals.rsi(random_walk_prices).dropna()
    assert (result >= 0).all()
    assert (result <= 100).all()


def test_rsi_is_high_for_a_strictly_rising_series(monotonic_up_prices):
    result = technicals.rsi(monotonic_up_prices).dropna()
    # An unbroken uptrend has no losses, so RSI should sit at the top of its range.
    assert (result > 95).all()


def test_macd_histogram_equals_macd_minus_signal(random_walk_prices):
    result = technicals.macd(random_walk_prices)
    diff = (result["macd"] - result["signal"] - result["histogram"]).dropna()
    assert np.allclose(diff.values, 0.0, atol=1e-9)


def test_bollinger_bands_are_correctly_ordered(random_walk_prices):
    bands = technicals.bollinger_bands(random_walk_prices).dropna()
    assert (bands["upper"] >= bands["middle"]).all()
    assert (bands["middle"] >= bands["lower"]).all()


def test_bollinger_bands_collapse_to_price_on_flat_series(flat_prices):
    bands = technicals.bollinger_bands(flat_prices).dropna()
    assert np.allclose(bands["upper"].values, 100.0)
    assert np.allclose(bands["lower"].values, 100.0)


def test_atr_is_never_negative(random_walk_ohlc):
    result = technicals.atr(
        random_walk_ohlc["high"], random_walk_ohlc["low"], random_walk_ohlc["close"]
    ).dropna()
    assert (result >= 0).all()


def test_indicators_have_no_lookahead_bias(random_walk_prices):
    """The value of an indicator at time t must not change when data after
    t is added or removed — otherwise the backtester/forecaster built on
    top of this module would leak future information into past features."""
    full = technicals.sma(random_walk_prices, window=20)
    truncated_input = random_walk_prices.iloc[:300]
    truncated = technicals.sma(truncated_input, window=20)

    overlap_index = truncated.dropna().index
    pd.testing.assert_series_equal(
        full.loc[overlap_index], truncated.loc[overlap_index], check_names=False
    )


def test_all_indicators_runs_end_to_end(random_walk_ohlc):
    result = technicals.all_indicators(random_walk_ohlc)
    expected_columns = {
        "sma_20", "sma_50", "sma_100", "sma_200", "ema_12", "ema_26",
        "rsi_14", "macd", "macd_signal", "macd_histogram",
        "bb_upper", "bb_middle", "bb_lower", "atr_14",
        "historical_volatility_21d", "adx_14",
    }
    assert expected_columns.issubset(set(result.columns))
    assert len(result) == len(random_walk_ohlc)
