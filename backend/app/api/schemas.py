"""Response schemas returned by the API routes.

These wrap the internal data-layer schemas and add the analytics fields
the frontend actually renders, so the frontend never has to reach into
provider-shaped objects.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.data.schemas import DataSource, OHLCVBar


class OverviewResponse(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None
    sector: str | None
    industry: str | None
    currency: str
    price: float
    previous_close: float
    change: float
    change_percent: float
    market_cap: float | None
    week52_high: float | None
    week52_low: float | None
    dividend_yield: float | None
    source: DataSource
    is_synthetic: bool


class PriceHistoryResponse(BaseModel):
    ticker: str
    period: str
    bars: list[OHLCVBar]
    source: DataSource
    is_synthetic: bool


class IndicatorPoint(BaseModel):
    trade_date: str
    sma_20: float | None = None
    sma_50: float | None = None
    sma_100: float | None = None
    sma_200: float | None = None
    ema_12: float | None = None
    ema_26: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    atr_14: float | None = None
    historical_volatility_21d: float | None = None
    adx_14: float | None = None


class TechnicalsResponse(BaseModel):
    ticker: str
    period: str
    points: list[IndicatorPoint]
    source: DataSource
    is_synthetic: bool


class ReturnsResponse(BaseModel):
    ticker: str
    period: str
    total_return_pct: float
    annualized_return_pct: float
    initial_investment: float
    ending_value: float
    growth_series: list[dict]  # [{trade_date, value}]
    distribution: dict
    source: DataSource
    is_synthetic: bool


class RiskResponse(BaseModel):
    ticker: str
    period: str
    benchmark: str | None
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    max_drawdown_peak_date: str | None
    max_drawdown_trough_date: str | None
    max_drawdown_recovery_date: str | None
    max_drawdown_recovery_days: int | None
    current_drawdown_pct: float
    value_at_risk_95: float
    conditional_value_at_risk_95: float
    risk_free_rate_assumed: float
    beta: float | None
    correlation_to_benchmark: float | None
    drawdown_series: list[dict]  # [{trade_date, drawdown_pct}]
    source: DataSource
    is_synthetic: bool


class FundamentalsResponse(BaseModel):
    ticker: str
    pe_ratio: float | None
    forward_pe: float | None
    price_to_sales: float | None
    price_to_book: float | None
    peg_ratio: float | None
    ev_to_ebitda: float | None
    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
    return_on_equity: float | None
    return_on_assets: float | None
    total_cash: float | None
    total_debt: float | None
    debt_to_equity: float | None
    current_ratio: float | None
    free_cash_flow: float | None
    revenue_growth: float | None
    earnings_growth: float | None
    source: DataSource
    is_synthetic: bool


class SearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str | None


class FinancialStatementResponse(BaseModel):
    ticker: str
    statement_type: str
    frequency: str
    periods: list[str]
    line_items: list[dict]  # [{label, values: {period: value}}]
    source: DataSource
    is_synthetic: bool


class DividendPaymentOut(BaseModel):
    ex_date: str
    amount: float


class DividendsResponse(BaseModel):
    ticker: str
    payments: list[DividendPaymentOut]
    trailing_annual_dividend_rate: float | None
    dividend_yield: float | None
    source: DataSource
    is_synthetic: bool


class CompareSeries(BaseModel):
    ticker: str
    normalized_return_pct: list[dict]  # [{trade_date, value}] — % change from period start
    total_return_pct: float
    annualized_volatility: float
    source: DataSource
    is_synthetic: bool


class CompareResponse(BaseModel):
    period: str
    tickers: list[str]
    series: list[CompareSeries]
    correlation_matrix: dict[str, dict[str, float]]
    excluded: list[dict]  # [{ticker, reason}] for tickers that couldn't be loaded


class ErrorResponse(BaseModel):
    detail: str
