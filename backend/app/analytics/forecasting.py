"""Return forecasting, evaluated honestly.

The point of this module is not to predict stock prices well — a simple
linear model on daily technical features generally can't, and pretending
otherwise would be exactly the kind of misleading claim this whole app is
built to avoid making (see the disclaimer that ships with every response
this produces). The point is to demonstrate the *right way* to evaluate a
forecast: walk-forward (never trained on data from after the day it's
predicting), compared against a naive baseline, with the comparison
reported honestly even when the model doesn't beat the baseline — which,
for daily equity returns, is the normal and expected outcome.

Everything here operates on features built purely from the no-lookahead
indicator functions in `app/analytics/technicals.py`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from app.analytics import technicals

FEATURE_COLUMNS = [
    "lag_return_1",
    "lag_return_2",
    "lag_return_3",
    "lag_return_5",
    "rsi_14",
    "macd_histogram",
    "historical_volatility_21d",
    "dist_from_sma_50",
]


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Build a feature matrix + next-day-return target from an OHLC frame.

    `df` needs lowercase open/high/low/close columns, ascending by date.
    The target column ('target') is the ONE forward-looking value here —
    it's `close.pct_change().shift(-1)`, i.e. tomorrow's return, and it's
    the only column a caller should ever treat as "looks into the future."
    Every feature column is computed strictly from data at or before the
    row's own date.
    """
    close = df["close"]
    daily_return = close.pct_change()
    indicators = technicals.all_indicators(df)

    features = pd.DataFrame(index=df.index)
    features["lag_return_1"] = daily_return.shift(1)
    features["lag_return_2"] = daily_return.shift(2)
    features["lag_return_3"] = daily_return.shift(3)
    features["lag_return_5"] = daily_return.shift(5)
    features["rsi_14"] = indicators["rsi_14"]
    features["macd_histogram"] = indicators["macd_histogram"]
    features["historical_volatility_21d"] = indicators["historical_volatility_21d"]
    features["dist_from_sma_50"] = (close - indicators["sma_50"]) / indicators["sma_50"]
    features["target"] = daily_return.shift(-1)  # the only forward-looking column

    return features.dropna()


def walk_forward_forecast(
    feature_df: pd.DataFrame,
    *,
    min_train_days: int = 126,
    refit_interval_days: int = 21,
    alpha: float = 1.0,
) -> pd.DataFrame:
    """Rolling walk-forward evaluation.

    At each prediction point, the model is trained only on rows strictly
    before it — refit every `refit_interval_days` (a fixed model is used
    to predict the days between refits, mirroring how a model would
    actually be operated, rather than refitting on every single day,
    which is both unrealistic and unnecessarily slow).

    Returns a DataFrame indexed by date with columns: actual (the real
    next-day return), predicted (the model's prediction), naive_zero
    (always predicts 0% — the "nothing changes" baseline), and
    naive_persistence (predicts the same sign as the most recent actual
    realized return — the "trend continues" baseline).
    """
    if len(feature_df) <= min_train_days:
        return pd.DataFrame(columns=["actual", "predicted", "naive_zero", "naive_persistence"])

    rows = []
    model = None
    last_actual_sign = 0.0

    for i in range(min_train_days, len(feature_df)):
        if model is None or (i - min_train_days) % refit_interval_days == 0:
            train = feature_df.iloc[:i]
            model = Ridge(alpha=alpha)
            model.fit(train[FEATURE_COLUMNS], train["target"])

        row = feature_df.iloc[[i]]
        predicted = float(model.predict(row[FEATURE_COLUMNS])[0])
        actual = float(row["target"].iloc[0])
        naive_persistence = last_actual_sign

        rows.append(
            {
                "date": feature_df.index[i],
                "actual": actual,
                "predicted": predicted,
                "naive_zero": 0.0,
                "naive_persistence": naive_persistence,
            }
        )
        last_actual_sign = np.sign(actual) * 0.001 if actual != 0 else 0.0  # small nonzero for sign comparison

    return pd.DataFrame(rows).set_index("date")


def evaluate_forecast(results: pd.DataFrame) -> dict:
    """Honest scoring: MAE/RMSE for the model vs. the zero baseline,
    directional accuracy for the model vs. both baselines. Nothing here
    picks a favorable framing — it reports what happened."""
    if results.empty:
        return {
            "n_predictions": 0,
            "model_mae": None,
            "model_rmse": None,
            "naive_zero_mae": None,
            "naive_zero_rmse": None,
            "model_directional_accuracy": None,
            "naive_persistence_directional_accuracy": None,
            "beats_naive_mae": None,
            "beats_naive_directional": None,
        }

    actual = results["actual"]
    predicted = results["predicted"]
    naive_zero = results["naive_zero"]
    naive_persistence = results["naive_persistence"]

    model_mae = float((predicted - actual).abs().mean())
    model_rmse = float(np.sqrt(((predicted - actual) ** 2).mean()))
    naive_zero_mae = float((naive_zero - actual).abs().mean())
    naive_zero_rmse = float(np.sqrt(((naive_zero - actual) ** 2).mean()))

    model_correct_direction = (np.sign(predicted) == np.sign(actual)) & (actual != 0)
    model_directional_accuracy = float(model_correct_direction.mean())

    persistence_correct = (np.sign(naive_persistence) == np.sign(actual)) & (actual != 0) & (naive_persistence != 0)
    naive_persistence_directional_accuracy = float(persistence_correct.mean())

    return {
        "n_predictions": int(len(results)),
        "model_mae": model_mae,
        "model_rmse": model_rmse,
        "naive_zero_mae": naive_zero_mae,
        "naive_zero_rmse": naive_zero_rmse,
        "model_directional_accuracy": model_directional_accuracy,
        "naive_persistence_directional_accuracy": naive_persistence_directional_accuracy,
        "beats_naive_mae": model_mae < naive_zero_mae,
        "beats_naive_directional": model_directional_accuracy > 0.5,
    }


def fit_latest_model(feature_df: pd.DataFrame, *, alpha: float = 1.0) -> tuple[Ridge, float]:
    """Fit on ALL available data and predict one step past the end of it.

    This is explicitly NOT part of the walk-forward evaluation — it's the
    "what does the model say about tomorrow" figure, fit on everything
    including the most recent day, which is the normal way to operate a
    model in production (evaluate walk-forward, then deploy on all data).
    The evaluation metrics from `evaluate_forecast` are what tell you
    whether to trust this number at all.
    """
    model = Ridge(alpha=alpha)
    model.fit(feature_df[FEATURE_COLUMNS], feature_df["target"])
    latest_features = feature_df[FEATURE_COLUMNS].iloc[[-1]]
    next_return = float(model.predict(latest_features)[0])
    return model, next_return
