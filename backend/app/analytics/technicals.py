"""Technical indicators.

Every function is a pure transform over a pandas DataFrame with columns
open/high/low/close (lowercase) indexed by trade date, ascending. Each
value at row t is computed only from rows <= t — this matters a lot once
these functions get reused as ML features in the forecasting lab (PRD §23),
where using information from t+1 would be data leakage.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return close.rolling(window=window, min_periods=window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    """Exponential moving average."""
    return close.ewm(span=span, adjust=False, min_periods=span).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing (the standard
    definition — a plain rolling-mean RSI is a common but incorrect
    shortcut that diverges from what every charting platform shows)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result = 100 - (100 / (1 + rs))
    return result.fillna(100).where(avg_loss != 0, 100).mask(avg_gain == 0, 0)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD line, signal line, and histogram."""
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "histogram": histogram})


def bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Middle band (SMA), upper/lower bands at +/- num_std standard deviations."""
    middle = sma(close, window)
    std = close.rolling(window=window, min_periods=window).std(ddof=0)
    return pd.DataFrame(
        {
            "middle": middle,
            "upper": middle + num_std * std,
            "lower": middle - num_std * std,
        }
    )


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    ranges = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    )
    return ranges.max(axis=1)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Average True Range via Wilder's smoothing."""
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def historical_volatility(close: pd.Series, window: int = 21) -> pd.Series:
    """Rolling annualized volatility of log returns (21 trading days ~ 1 month)."""
    log_rets = np.log(close / close.shift(1))
    return log_rets.rolling(window=window, min_periods=window).std(ddof=1) * np.sqrt(252)


def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Average Directional Index — trend strength (not direction), 0-100."""
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index)

    tr = true_range(high, low, close)
    atr_smoothed = tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    plus_di = 100 * (plus_dm.ewm(alpha=1 / window, min_periods=window, adjust=False).mean() / atr_smoothed)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / window, min_periods=window, adjust=False).mean() / atr_smoothed)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience: compute the full standard indicator set (PRD §9) at once.

    `df` must have lowercase open/high/low/close columns indexed by date.
    """
    close, high, low = df["close"], df["high"], df["low"]
    macd_df = macd(close)
    bb_df = bollinger_bands(close)

    out = pd.DataFrame(index=df.index)
    out["sma_20"] = sma(close, 20)
    out["sma_50"] = sma(close, 50)
    out["sma_100"] = sma(close, 100)
    out["sma_200"] = sma(close, 200)
    out["ema_12"] = ema(close, 12)
    out["ema_26"] = ema(close, 26)
    out["rsi_14"] = rsi(close, 14)
    out["macd"] = macd_df["macd"]
    out["macd_signal"] = macd_df["signal"]
    out["macd_histogram"] = macd_df["histogram"]
    out["bb_upper"] = bb_df["upper"]
    out["bb_middle"] = bb_df["middle"]
    out["bb_lower"] = bb_df["lower"]
    out["atr_14"] = atr(high, low, close, 14)
    out["historical_volatility_21d"] = historical_volatility(close, 21)
    out["adx_14"] = adx(high, low, close, 14)
    return out
