"""Provider interface.

Every data source (yfinance, a paid API, the synthetic fallback) implements
this protocol. The rest of the backend only ever talks to `MarketDataProvider`,
never to a concrete provider class — that's what lets the app fail over
between sources without analytics or API code knowing the difference.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.data.schemas import (
    CompanyProfile,
    DividendHistory,
    FinancialStatement,
    FundamentalsSnapshot,
    PriceHistory,
    QuoteSnapshot,
    StatementFrequency,
    StatementType,
)


class ProviderError(Exception):
    """Raised when a provider cannot fulfill a request.

    Callers (the DataService) catch this to decide whether to fail over
    to another provider or surface a clean error to the API layer.
    """

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class TickerNotFoundError(ProviderError):
    """The ticker does not exist / has no data at this provider."""


class RateLimitedError(ProviderError):
    """Provider is rate limiting us. Always retryable."""

    def __init__(self, message: str = "Rate limited by data provider") -> None:
        super().__init__(message, retryable=True)


class MarketDataProvider(ABC):
    """Abstract base for any market-data source."""

    name: str

    @abstractmethod
    async def get_price_history(self, ticker: str, *, period: str = "1y") -> PriceHistory:
        """Fetch historical OHLCV bars.

        `period` follows the yfinance convention: 1d, 5d, 1mo, 3mo, 6mo,
        ytd, 1y, 2y, 5y, 10y, max. Providers that don't natively support a
        period should resample from a max-range pull.
        """

    @abstractmethod
    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        """Fetch static company reference data (name, sector, exchange)."""

    @abstractmethod
    async def get_quote(self, ticker: str) -> QuoteSnapshot:
        """Fetch the current/most recent price snapshot."""

    @abstractmethod
    async def get_fundamentals(self, ticker: str) -> FundamentalsSnapshot:
        """Fetch valuation/profitability/health metrics where available."""

    @abstractmethod
    async def get_financial_statement(
        self, ticker: str, *, statement_type: StatementType, frequency: StatementFrequency
    ) -> FinancialStatement:
        """Fetch a financial statement (income statement, balance sheet, or
        cash flow), annual or quarterly. Returns an empty statement
        (`is_empty` True) rather than fabricated figures when unavailable."""

    @abstractmethod
    async def get_dividends(self, ticker: str) -> DividendHistory:
        """Fetch dividend payment history and trailing yield, if any."""

    @abstractmethod
    async def search(self, query: str, *, limit: int = 8) -> list[dict]:
        """Search tickers by symbol or company name.

        Returns a list of {"ticker": str, "name": str, "exchange": str | None}.
        """
