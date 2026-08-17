"""Core data contracts for market data.

Every provider (real or synthetic) must return data in these shapes.
Downstream analytics code depends on this contract, not on any single
provider's implementation details.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DataSource(str, Enum):
    """Where a given payload actually came from.

    The frontend uses this to decide whether to show a "demo data" banner.
    A response is never allowed to claim SYNTHETIC data is a real source.
    """

    YFINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    FINANCIAL_MODELING_PREP = "financial_modeling_prep"
    SYNTHETIC_DEMO = "synthetic_demo"


class OHLCVBar(BaseModel):
    """A single trading-day bar. Prices are split/dividend adjusted close."""

    trade_date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int = Field(ge=0)


class PriceHistory(BaseModel):
    """A ticker's historical bars plus provenance metadata."""

    ticker: str
    source: DataSource
    is_synthetic: bool
    bars: list[OHLCVBar]

    @property
    def is_empty(self) -> bool:
        return len(self.bars) == 0


class CompanyProfile(BaseModel):
    """Static-ish company reference data shown in the dashboard header."""

    ticker: str
    company_name: str
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None
    currency: str = "USD"
    source: DataSource
    is_synthetic: bool


class QuoteSnapshot(BaseModel):
    """Current/most-recent price snapshot."""

    ticker: str
    price: float
    previous_close: float
    change: float
    change_percent: float
    market_cap: float | None = None
    week52_high: float | None = None
    week52_low: float | None = None
    dividend_yield: float | None = None
    source: DataSource
    is_synthetic: bool


class FundamentalsSnapshot(BaseModel):
    """Best-effort fundamentals. Any field the provider lacks is None —
    the API and UI must render "N/A", never a fabricated number."""

    ticker: str
    pe_ratio: float | None = None
    forward_pe: float | None = None
    price_to_sales: float | None = None
    price_to_book: float | None = None
    peg_ratio: float | None = None
    ev_to_ebitda: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    return_on_equity: float | None = None
    return_on_assets: float | None = None
    total_cash: float | None = None
    total_debt: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    free_cash_flow: float | None = None
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    source: DataSource
    is_synthetic: bool


StatementType = Literal["income_statement", "balance_sheet", "cash_flow"]
StatementFrequency = Literal["annual", "quarterly"]


class StatementLineItem(BaseModel):
    """One row of a financial statement.

    `values` maps ISO period-end date -> the reported figure for that period.
    Line-item labels are NOT normalized across companies/providers — yfinance
    (and most free data sources) don't report perfectly consistent line-item
    names across every ticker and sector, and silently force-mapping
    differently-labeled rows into a rigid schema risks mislabeling data.
    Passing the provider's own labels through is the honest choice; a
    consuming UI groups/sorts them for display instead.
    """

    label: str
    values: dict[str, float | None]


class FinancialStatement(BaseModel):
    ticker: str
    statement_type: StatementType
    frequency: StatementFrequency
    periods: list[str]  # ISO period-end dates, most recent first
    line_items: list[StatementLineItem]
    source: DataSource
    is_synthetic: bool

    @property
    def is_empty(self) -> bool:
        return len(self.periods) == 0 or len(self.line_items) == 0


class DividendPayment(BaseModel):
    ex_date: date
    amount: float


class DividendHistory(BaseModel):
    ticker: str
    payments: list[DividendPayment]
    trailing_annual_dividend_rate: float | None = None
    dividend_yield: float | None = None
    source: DataSource
    is_synthetic: bool
