"""Orchestration layer between the API routes and the raw data providers.

Responsibilities:
  1. Validate/sanitize ticker input (PRD §39).
  2. Serve from cache when possible (PRD §40).
  3. Try the configured primary provider; on failure, fail over to the
     synthetic provider ONLY if `enable_synthetic_fallback` is set, and
     always with the response's `is_synthetic` flag telling the truth.
  4. Never let a provider-specific exception leak past this layer —
     callers see either data or a `DataUnavailableError`.
"""

from __future__ import annotations

import re

from app.core.cache import get_cache
from app.core.config import get_settings
from app.data.providers.base import MarketDataProvider, ProviderError
from app.data.providers.synthetic_provider import SyntheticProvider
from app.data.providers.yfinance_provider import YFinanceProvider
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

_TICKER_PATTERN = re.compile(r"^[A-Z]{1,6}([.\-][A-Z]{1,3})?$")


class InvalidTickerError(ValueError):
    pass


class DataUnavailableError(RuntimeError):
    pass


def sanitize_ticker(raw: str) -> str:
    """Normalize and validate a user-supplied ticker.

    Rejects anything that isn't a plausible ticker symbol before it ever
    reaches a provider or a cache key, closing off injection via the
    ticker path/query parameter.
    """
    ticker = raw.strip().upper()
    if not ticker or len(ticker) > 10 or not _TICKER_PATTERN.match(ticker):
        raise InvalidTickerError(f"'{raw}' is not a valid ticker symbol")
    return ticker


class DataService:
    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self._cache = get_cache()
        self._primary: MarketDataProvider = (
            SyntheticProvider() if settings.primary_provider == "synthetic" else YFinanceProvider()
        )
        self._fallback = SyntheticProvider()

    async def get_price_history(self, raw_ticker: str, *, period: str = "1y") -> PriceHistory:
        ticker = sanitize_ticker(raw_ticker)
        ttl = (
            self._settings.cache_ttl_intraday_seconds
            if period in {"1d", "5d"}
            else self._settings.cache_ttl_daily_seconds
        )
        cache_key = f"history:{ticker}:{period}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return PriceHistory.model_validate(cached)

        try:
            result = await self._primary.get_price_history(ticker, period=period)
        except ProviderError as exc:
            if not self._settings.enable_synthetic_fallback:
                raise DataUnavailableError(str(exc)) from exc
            result = await self._fallback.get_price_history(ticker, period=period)

        await self._cache.set(cache_key, result.model_dump(mode="json"), ttl)
        return result

    async def get_company_profile(self, raw_ticker: str) -> CompanyProfile:
        ticker = sanitize_ticker(raw_ticker)
        cache_key = f"profile:{ticker}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return CompanyProfile.model_validate(cached)

        try:
            result = await self._primary.get_company_profile(ticker)
        except ProviderError as exc:
            if not self._settings.enable_synthetic_fallback:
                raise DataUnavailableError(str(exc)) from exc
            result = await self._fallback.get_company_profile(ticker)

        await self._cache.set(cache_key, result.model_dump(mode="json"), self._settings.cache_ttl_fundamentals_seconds)
        return result

    async def get_quote(self, raw_ticker: str) -> QuoteSnapshot:
        ticker = sanitize_ticker(raw_ticker)
        cache_key = f"quote:{ticker}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return QuoteSnapshot.model_validate(cached)

        try:
            result = await self._primary.get_quote(ticker)
        except ProviderError as exc:
            if not self._settings.enable_synthetic_fallback:
                raise DataUnavailableError(str(exc)) from exc
            result = await self._fallback.get_quote(ticker)

        await self._cache.set(cache_key, result.model_dump(mode="json"), self._settings.cache_ttl_intraday_seconds)
        return result

    async def get_fundamentals(self, raw_ticker: str) -> FundamentalsSnapshot:
        ticker = sanitize_ticker(raw_ticker)
        cache_key = f"fundamentals:{ticker}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return FundamentalsSnapshot.model_validate(cached)

        try:
            result = await self._primary.get_fundamentals(ticker)
        except ProviderError as exc:
            if not self._settings.enable_synthetic_fallback:
                raise DataUnavailableError(str(exc)) from exc
            result = await self._fallback.get_fundamentals(ticker)

        await self._cache.set(cache_key, result.model_dump(mode="json"), self._settings.cache_ttl_fundamentals_seconds)
        return result

    async def search(self, query: str, *, limit: int = 8) -> list[dict]:
        return await self._primary.search(query, limit=limit)

    async def get_financial_statement(
        self, raw_ticker: str, *, statement_type: StatementType, frequency: StatementFrequency
    ) -> FinancialStatement:
        ticker = sanitize_ticker(raw_ticker)
        cache_key = f"statement:{ticker}:{statement_type}:{frequency}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return FinancialStatement.model_validate(cached)

        try:
            result = await self._primary.get_financial_statement(
                ticker, statement_type=statement_type, frequency=frequency
            )
        except ProviderError as exc:
            if not self._settings.enable_synthetic_fallback:
                raise DataUnavailableError(str(exc)) from exc
            result = await self._fallback.get_financial_statement(
                ticker, statement_type=statement_type, frequency=frequency
            )

        await self._cache.set(cache_key, result.model_dump(mode="json"), self._settings.cache_ttl_fundamentals_seconds)
        return result

    async def get_dividends(self, raw_ticker: str) -> DividendHistory:
        ticker = sanitize_ticker(raw_ticker)
        cache_key = f"dividends:{ticker}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return DividendHistory.model_validate(cached)

        try:
            result = await self._primary.get_dividends(ticker)
        except ProviderError as exc:
            if not self._settings.enable_synthetic_fallback:
                raise DataUnavailableError(str(exc)) from exc
            result = await self._fallback.get_dividends(ticker)

        await self._cache.set(cache_key, result.model_dump(mode="json"), self._settings.cache_ttl_fundamentals_seconds)
        return result


_service_instance: DataService | None = None


def get_data_service() -> DataService:
    global _service_instance
    if _service_instance is None:
        _service_instance = DataService()
    return _service_instance
