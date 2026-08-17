from __future__ import annotations

from pydantic import BaseModel


class ScreenerResult(BaseModel):
    ticker: str
    company_name: str
    sector: str | None
    price: float | None
    change_percent: float | None
    market_cap: float | None
    pe_ratio: float | None
    dividend_yield: float | None
    is_synthetic: bool


class ScreenerResponse(BaseModel):
    results: list[ScreenerResult]
    candidates_scanned: int
    candidates_available: int
    is_synthetic: bool
    note: str
