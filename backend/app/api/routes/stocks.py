"""Stock research endpoints (PRD §35, Phase 1 core).

Each route composes: DataService (fetch + cache + failover) -> analytics
module (pure calculations) -> API schema (what the frontend consumes).
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.analytics import returns as returns_analytics
from app.analytics import risk as risk_analytics
from app.analytics import technicals as technicals_analytics
from app.analytics.utils import history_to_dataframe
from app.api.deps import get_service, rate_limiter
from app.api.schemas import (
    DividendPaymentOut,
    DividendsResponse,
    FinancialStatementResponse,
    FundamentalsResponse,
    IndicatorPoint,
    OverviewResponse,
    PriceHistoryResponse,
    ReturnsResponse,
    RiskResponse,
    SearchResult,
    TechnicalsResponse,
)
from app.data.service import DataService, DataUnavailableError, InvalidTickerError

router = APIRouter(prefix="/api/stocks", tags=["stocks"], dependencies=[Depends(rate_limiter)])

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "ytd", "1y", "2y", "5y", "10y", "max"}


def _period_query(period: str = Query("1y", description="1d,5d,1mo,3mo,6mo,ytd,1y,2y,5y,10y,max")) -> str:
    if period not in VALID_PERIODS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid period '{period}'")
    return period


async def _safe_call(coro):
    try:
        return await coro
    except InvalidTickerError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except DataUnavailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


@router.get("/search", response_model=list[SearchResult])
async def search_tickers(q: str = Query(..., min_length=1), service: DataService = Depends(get_service)):
    results = await service.search(q)
    return [SearchResult(**r) for r in results]


@router.get("/{ticker}/overview", response_model=OverviewResponse)
async def get_overview(ticker: str, service: DataService = Depends(get_service)):
    profile = await _safe_call(service.get_company_profile(ticker))
    quote = await _safe_call(service.get_quote(ticker))
    return OverviewResponse(
        ticker=profile.ticker,
        company_name=profile.company_name,
        exchange=profile.exchange,
        sector=profile.sector,
        industry=profile.industry,
        currency=profile.currency,
        price=quote.price,
        previous_close=quote.previous_close,
        change=quote.change,
        change_percent=quote.change_percent,
        market_cap=quote.market_cap,
        week52_high=quote.week52_high,
        week52_low=quote.week52_low,
        dividend_yield=quote.dividend_yield,
        source=quote.source,
        is_synthetic=quote.is_synthetic,
    )


@router.get("/{ticker}/prices", response_model=PriceHistoryResponse)
async def get_prices(ticker: str, period: str = Depends(_period_query), service: DataService = Depends(get_service)):
    history = await _safe_call(service.get_price_history(ticker, period=period))
    if history.is_empty:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No historical data could be found for this ticker.")
    return PriceHistoryResponse(
        ticker=history.ticker,
        period=period,
        bars=history.bars,
        source=history.source,
        is_synthetic=history.is_synthetic,
    )


@router.get("/{ticker}/technicals", response_model=TechnicalsResponse)
async def get_technicals(ticker: str, period: str = Depends(_period_query), service: DataService = Depends(get_service)):
    history = await _safe_call(service.get_price_history(ticker, period=period))
    if history.is_empty:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No historical data could be found for this ticker.")

    df = history_to_dataframe(history)
    indicators = technicals_analytics.all_indicators(df)

    points = [
        IndicatorPoint(
            trade_date=idx.date().isoformat(),
            **{col: (None if pd.isna(val) else float(val)) for col, val in row.items()},
        )
        for idx, row in indicators.iterrows()
    ]
    return TechnicalsResponse(
        ticker=history.ticker,
        period=period,
        points=points,
        source=history.source,
        is_synthetic=history.is_synthetic,
    )


@router.get("/{ticker}/returns", response_model=ReturnsResponse)
async def get_returns(
    ticker: str,
    period: str = Depends(_period_query),
    initial_investment: float = Query(10_000.0, gt=0),
    service: DataService = Depends(get_service),
):
    history = await _safe_call(service.get_price_history(ticker, period=period))
    if history.is_empty or len(history.bars) < 2:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Insufficient historical data to compute returns for this ticker/period.",
        )
    df = history_to_dataframe(history)
    close = df["adj_close"]

    growth = returns_analytics.growth_of_investment(close, initial_investment)
    growth_series = [{"trade_date": idx.date().isoformat(), "value": round(float(v), 2)} for idx, v in growth.items()]

    return ReturnsResponse(
        ticker=history.ticker,
        period=period,
        total_return_pct=returns_analytics.total_return(close) * 100,
        annualized_return_pct=returns_analytics.annualized_return(close) * 100,
        initial_investment=initial_investment,
        ending_value=float(growth.iloc[-1]) if len(growth) else initial_investment,
        growth_series=growth_series,
        distribution=returns_analytics.daily_return_distribution(close),
        source=history.source,
        is_synthetic=history.is_synthetic,
    )


@router.get("/{ticker}/risk", response_model=RiskResponse)
async def get_risk(
    ticker: str,
    period: str = Depends(_period_query),
    benchmark: str | None = Query(None, description="Ticker to compute beta/correlation against, e.g. SPY"),
    risk_free_rate: float = Query(0.04, ge=0, le=0.2),
    service: DataService = Depends(get_service),
):
    history = await _safe_call(service.get_price_history(ticker, period=period))
    if history.is_empty or len(history.bars) < 2:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Insufficient historical data to compute risk metrics for this ticker/period.",
        )
    df = history_to_dataframe(history)
    close = df["adj_close"]

    benchmark_close = None
    if benchmark:
        bench_history = await _safe_call(service.get_price_history(benchmark, period=period))
        if not bench_history.is_empty:
            benchmark_close = history_to_dataframe(bench_history)["adj_close"]

    summary = risk_analytics.risk_summary(close, benchmark_close, risk_free_rate)
    dd_series = risk_analytics.drawdown_series(close)
    drawdown_series = [{"trade_date": idx.date().isoformat(), "drawdown_pct": round(float(v) * 100, 3)} for idx, v in dd_series.items()]

    return RiskResponse(
        ticker=history.ticker,
        period=period,
        benchmark=benchmark,
        annualized_volatility=summary["annualized_volatility"] * 100,
        sharpe_ratio=summary["sharpe_ratio"],
        sortino_ratio=summary["sortino_ratio"],
        max_drawdown_pct=summary["max_drawdown_pct"] * 100,
        max_drawdown_peak_date=summary["max_drawdown_peak_date"],
        max_drawdown_trough_date=summary["max_drawdown_trough_date"],
        max_drawdown_recovery_date=summary["max_drawdown_recovery_date"],
        max_drawdown_recovery_days=summary["max_drawdown_recovery_days"],
        current_drawdown_pct=summary["current_drawdown_pct"] * 100,
        value_at_risk_95=summary["value_at_risk_95"] * 100,
        conditional_value_at_risk_95=summary["conditional_value_at_risk_95"] * 100,
        risk_free_rate_assumed=summary["risk_free_rate_assumed"],
        beta=summary["beta"],
        correlation_to_benchmark=summary["correlation_to_benchmark"],
        drawdown_series=drawdown_series,
        source=history.source,
        is_synthetic=history.is_synthetic,
    )


@router.get("/{ticker}/fundamentals", response_model=FundamentalsResponse)
async def get_fundamentals(ticker: str, service: DataService = Depends(get_service)):
    fundamentals = await _safe_call(service.get_fundamentals(ticker))
    return FundamentalsResponse(**fundamentals.model_dump())


VALID_STATEMENT_TYPES = {"income_statement", "balance_sheet", "cash_flow"}
VALID_FREQUENCIES = {"annual", "quarterly"}


@router.get("/{ticker}/financials/{statement_type}", response_model=FinancialStatementResponse)
async def get_financials(
    ticker: str,
    statement_type: str,
    frequency: str = Query("annual", description="annual or quarterly"),
    service: DataService = Depends(get_service),
):
    if statement_type not in VALID_STATEMENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid statement_type '{statement_type}'")
    if frequency not in VALID_FREQUENCIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid frequency '{frequency}'")

    statement = await _safe_call(
        service.get_financial_statement(ticker, statement_type=statement_type, frequency=frequency)  # type: ignore[arg-type]
    )
    return FinancialStatementResponse(
        ticker=statement.ticker,
        statement_type=statement.statement_type,
        frequency=statement.frequency,
        periods=statement.periods,
        line_items=[item.model_dump() for item in statement.line_items],
        source=statement.source,
        is_synthetic=statement.is_synthetic,
    )


@router.get("/{ticker}/dividends", response_model=DividendsResponse)
async def get_dividends(ticker: str, service: DataService = Depends(get_service)):
    dividends = await _safe_call(service.get_dividends(ticker))
    return DividendsResponse(
        ticker=dividends.ticker,
        payments=[DividendPaymentOut(ex_date=p.ex_date.isoformat(), amount=p.amount) for p in dividends.payments],
        trailing_annual_dividend_rate=dividends.trailing_annual_dividend_rate,
        dividend_yield=dividends.dividend_yield,
        source=dividends.source,
        is_synthetic=dividends.is_synthetic,
    )
