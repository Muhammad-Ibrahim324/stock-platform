"""Screener endpoint (PRD §Phase 3).

There's no bulk "screen the whole market" API behind this — yfinance has
no screener endpoint, and per-ticker requests don't batch. So this scans
a bounded slice of the bundled ticker directory (see
`app/data/ticker_directory.py`), fetching a quote for each candidate
concurrently (bounded by a semaphore) and filtering client-side.
`candidate_limit` caps how many tickers get scanned per request — it's the
honest trade-off for not having a real market-wide data feed, and it's
surfaced in the response (`candidates_scanned` vs `candidates_available`)
rather than silently truncated.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_service, rate_limiter
from app.api.schemas_screener import ScreenerResponse, ScreenerResult
from app.data import ticker_directory
from app.data.service import DataService

router = APIRouter(prefix="/api/screener", tags=["screener"], dependencies=[Depends(rate_limiter)])

MAX_CANDIDATE_LIMIT = 150
DEFAULT_CANDIDATE_LIMIT = 60
MAX_CONCURRENT_FETCHES = 15


@router.get("", response_model=ScreenerResponse)
async def screen_stocks(
    sector: str | None = Query(None, description=f"One of: {', '.join(ticker_directory.SECTORS)}"),
    min_market_cap: float | None = Query(None, ge=0),
    max_market_cap: float | None = Query(None, ge=0),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_pe: float | None = Query(None),
    max_pe: float | None = Query(None),
    min_dividend_yield: float | None = Query(None, ge=0, description="As a percent, e.g. 2.0 for 2%"),
    candidate_limit: int = Query(DEFAULT_CANDIDATE_LIMIT, ge=1, le=MAX_CANDIDATE_LIMIT),
    result_limit: int = Query(50, ge=1, le=200),
    service: DataService = Depends(get_service),
):
    all_candidates = ticker_directory.candidates(sector=sector)
    scanned = all_candidates[:candidate_limit]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)

    async def fetch_one(entry: dict) -> ScreenerResult | None:
        ticker = entry["ticker"]
        async with semaphore:
            try:
                quote, fundamentals = await asyncio.gather(
                    service.get_quote(ticker), service.get_fundamentals(ticker)
                )
            except Exception:  # noqa: BLE001 - one bad candidate shouldn't fail the whole scan
                return None

        return ScreenerResult(
            ticker=ticker,
            company_name=entry["name"],
            sector=entry["sector"],
            price=quote.price,
            change_percent=quote.change_percent,
            market_cap=quote.market_cap,
            pe_ratio=fundamentals.pe_ratio,
            dividend_yield=quote.dividend_yield,
            is_synthetic=quote.is_synthetic or fundamentals.is_synthetic,
        )

    fetched = await asyncio.gather(*[fetch_one(c) for c in scanned])
    results = [r for r in fetched if r is not None]

    min_div_fraction = (min_dividend_yield / 100) if min_dividend_yield is not None else None

    def passes(r: ScreenerResult) -> bool:
        if min_market_cap is not None and (r.market_cap is None or r.market_cap < min_market_cap):
            return False
        if max_market_cap is not None and (r.market_cap is None or r.market_cap > max_market_cap):
            return False
        if min_price is not None and (r.price is None or r.price < min_price):
            return False
        if max_price is not None and (r.price is None or r.price > max_price):
            return False
        if min_pe is not None and (r.pe_ratio is None or r.pe_ratio < min_pe):
            return False
        if max_pe is not None and (r.pe_ratio is None or r.pe_ratio > max_pe):
            return False
        if min_div_fraction is not None and (r.dividend_yield is None or r.dividend_yield < min_div_fraction):
            return False
        return True

    filtered = [r for r in results if passes(r)][:result_limit]
    any_synthetic = any(r.is_synthetic for r in results)

    scope = f"the {sector} sector" if sector else "the full bundled universe"
    note = (
        f"Scanned {len(scanned)} of {len(all_candidates)} candidates in {scope}. "
        "Increase candidate_limit to scan more, or narrow by sector — there's no "
        "live market-wide screening API behind this, so results are bounded to "
        "the tickers actually scanned, not the whole market."
    )

    return ScreenerResponse(
        results=filtered,
        candidates_scanned=len(scanned),
        candidates_available=len(all_candidates),
        is_synthetic=any_synthetic,
        note=note,
    )
