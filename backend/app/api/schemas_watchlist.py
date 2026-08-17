from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.data.schemas import DataSource


class WatchlistAddRequest(BaseModel):
    ticker: str


class WatchlistItemOut(BaseModel):
    ticker: str
    added_at: datetime
    price: float | None
    change: float | None
    change_percent: float | None
    source: DataSource | None
    is_synthetic: bool
