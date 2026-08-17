from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics import forecasting


def test_build_feature_matrix_has_expected_columns(random_walk_ohlc):
    features = forecasting.build_feature_matrix(random_walk_ohlc)
    for col in forecasting.FEATURE_COLUMNS:
        assert col in features.columns
    assert "target" in features.columns
    assert not features.isna().any().any()


def test_target_is_next_day_return_not_same_day(random_walk_ohlc):
    features = forecasting.build_feature_matrix(random_walk_ohlc)
    close = random_walk_ohlc["close"]
    actual_next_return = close.pct_change().shift(-1)
    # Every target value must match the actual forward return on that date.
    aligned = actual_next_return.reindex(features.index)
    assert np.allclose(features["target"].values, aligned.values, equal_nan=False)


def test_features_do_not_change_when_future_rows_are_removed(random_walk_ohlc):
    """The defining no-lookahead property: a feature value at row i must be
    identical whether or not rows after i exist in the input."""
    full = forecasting.build_feature_matrix(random_walk_ohlc)
    truncated_input = random_walk_ohlc.iloc[:300]
    truncated = forecasting.build_feature_matrix(truncated_input)

    overlap = truncated.index.intersection(full.index)
    assert len(overlap) > 50
    for col in forecasting.FEATURE_COLUMNS:
        pd.testing.assert_series_equal(
            full.loc[overlap, col], truncated.loc[overlap, col], check_names=False
        )


def test_walk_forward_forecast_returns_empty_when_insufficient_data():
    tiny = pd.DataFrame(
        {c: [0.0] * 10 for c in forecasting.FEATURE_COLUMNS} | {"target": [0.0] * 10},
        index=pd.bdate_range("2024-01-01", periods=10),
    )
    result = forecasting.walk_forward_forecast(tiny, min_train_days=126)
    assert result.empty


def test_walk_forward_forecast_length_matches_available_predictions(random_walk_ohlc):
    features = forecasting.build_feature_matrix(random_walk_ohlc)
    result = forecasting.walk_forward_forecast(features, min_train_days=126, refit_interval_days=21)
    assert len(result) == len(features) - 126


def test_walk_forward_naive_zero_is_always_zero(random_walk_ohlc):
    features = forecasting.build_feature_matrix(random_walk_ohlc)
    result = forecasting.walk_forward_forecast(features, min_train_days=126)
    assert (result["naive_zero"] == 0.0).all()


def test_walk_forward_only_trains_on_strictly_prior_data(random_walk_ohlc):
    """Mutating a feature value AFTER a given prediction's cutoff must not
    change that prediction — proves the model never trains on the future."""
    features = forecasting.build_feature_matrix(random_walk_ohlc)
    baseline = forecasting.walk_forward_forecast(features, min_train_days=126, refit_interval_days=21)

    mutated = features.copy()
    # Corrupt every feature value in the back third of the series.
    cutoff = int(len(mutated) * 0.7)
    mutated.iloc[cutoff:, :-1] = 999.0

    mutated_result = forecasting.walk_forward_forecast(mutated, min_train_days=126, refit_interval_days=21)

    # Predictions made using only data before the corrupted region must be identical.
    pre_corruption_dates = baseline.index[baseline.index < features.index[cutoff]]
    pd.testing.assert_series_equal(
        baseline.loc[pre_corruption_dates, "predicted"],
        mutated_result.loc[pre_corruption_dates, "predicted"],
        check_names=False,
    )


def test_evaluate_forecast_on_empty_input():
    result = forecasting.evaluate_forecast(pd.DataFrame(columns=["actual", "predicted", "naive_zero", "naive_persistence"]))
    assert result["n_predictions"] == 0
    assert result["model_mae"] is None


def test_evaluate_forecast_perfect_model_scores_zero_error():
    dates = pd.bdate_range("2024-01-01", periods=20)
    actual = pd.Series(np.linspace(-0.01, 0.01, 20), index=dates)
    results = pd.DataFrame(
        {
            "actual": actual,
            "predicted": actual,  # perfect predictions
            "naive_zero": 0.0,
            "naive_persistence": 0.0,
        },
        index=dates,
    )
    scored = forecasting.evaluate_forecast(results)
    assert np.isclose(scored["model_mae"], 0.0, atol=1e-12)
    assert np.isclose(scored["model_rmse"], 0.0, atol=1e-12)
    assert scored["model_directional_accuracy"] == 1.0
    assert scored["beats_naive_mae"] is True
    assert scored["beats_naive_directional"] is True


def test_evaluate_forecast_always_wrong_direction_scores_zero_accuracy():
    dates = pd.bdate_range("2024-01-01", periods=10)
    actual = pd.Series([0.01] * 10, index=dates)  # always goes up
    predicted = pd.Series([-0.01] * 10, index=dates)  # always predicts down
    results = pd.DataFrame(
        {"actual": actual, "predicted": predicted, "naive_zero": 0.0, "naive_persistence": 0.0}, index=dates
    )
    scored = forecasting.evaluate_forecast(results)
    assert scored["model_directional_accuracy"] == 0.0
    assert scored["beats_naive_directional"] is False


def test_fit_latest_model_predicts_a_single_finite_number(random_walk_ohlc):
    features = forecasting.build_feature_matrix(random_walk_ohlc)
    _, next_return = forecasting.fit_latest_model(features)
    assert np.isfinite(next_return)
