"""Multi-stock comparison (PRD §10 / Phase 2).

Kept as its own router with a distinct path prefix rather than nested
under /api/stocks/{ticker}/... — a comparison isn't a property of one
ticker, and mixing "/compare" into the {ticker} path space risks it being
shadowed by or shadowing the single-ticker routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.analytics import returns as returns_analytics
from app.analytics import risk as risk_analytics
from app.analytics.utils import history_to_dataframe
from app.api.deps import get_service, rate_limiter
from app.api.schemas import CompareResponse, CompareSeries
from app.api.routes.stocks import VALID_PERIODS
from app.data.service import DataService, InvalidTickerError

router = APIRouter(prefix="/api/compare", tags=["compare"], dependencies=[Depends(rate_limiter)])

MAX_COMPARE_TICKERS = 6


@router.get("", response_model=CompareResponse)
async def compare_tickers(
    tickers: str = Query(..., description="Comma-separated tickers, e.g. AAPL,MSFT,GOOGL"),
    period: str = Query("1y"),
    service: DataService = Depends(get_service),
):
    if period not in VALID_PERIODS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid period '{period}'")

    requested = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if len(requested) < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provide at least one ticker.")
    if len(requested) > MAX_COMPARE_TICKERS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Compare up to {MAX_COMPARE_TICKERS} tickers at a time.")

    closes: dict[str, object] = {}
    series_out: list[CompareSeries] = []
    excluded: list[dict] = []

    for ticker in requested:
        try:
            history = await service.get_price_history(ticker, period=period)
        except InvalidTickerError:
            excluded.append({"ticker": ticker, "reason": "Not a valid ticker symbol."})
            continue
        except Exception:  # noqa: BLE001 - a single bad ticker shouldn't fail the whole comparison
            excluded.append({"ticker": ticker, "reason": "Data unavailable."})
            continue

        if history.is_empty or len(history.bars) < 2:
            excluded.append({"ticker": ticker, "reason": "Insufficient historical data."})
            continue

        df = history_to_dataframe(history)
        close = df["adj_close"]
        closes[ticker] = close

        cum = returns_analytics.cumulative_returns(close) * 100
        series_out.append(
            CompareSeries(
                ticker=ticker,
                normalized_return_pct=[
                    {"trade_date": idx.date().isoformat(), "value": round(float(v), 3)} for idx, v in cum.items()
                ],
                total_return_pct=returns_analytics.total_return(close) * 100,
                annualized_volatility=risk_analytics.annualized_volatility(close) * 100,
                source=history.source,
                is_synthetic=history.is_synthetic,
            )
        )

    if not closes:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No valid tickers with sufficient data to compare.")

    corr_matrix = risk_analytics.correlation_matrix(closes) if len(closes) > 1 else {t: {t: 1.0} for t in closes}

    return CompareResponse(
        period=period,
        tickers=list(closes.keys()),
        series=series_out,
        correlation_matrix=corr_matrix,
        excluded=excluded,
    )
