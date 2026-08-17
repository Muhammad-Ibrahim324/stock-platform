"""Small conversion helpers shared by the analytics modules and API routes."""

from __future__ import annotations

import pandas as pd

from app.data.schemas import PriceHistory


def history_to_dataframe(history: PriceHistory) -> pd.DataFrame:
    """Convert a PriceHistory into a DatetimeIndex-ed DataFrame with
    lowercase open/high/low/close/adj_close/volume columns, ascending by date."""
    records = [
        {
            "trade_date": bar.trade_date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "adj_close": bar.adj_close,
            "volume": bar.volume,
        }
        for bar in history.bars
    ]
    df = pd.DataFrame.from_records(records)
    if df.empty:
        return df
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date").sort_index()
    return df
