"""yfinance-backed provider.

This is the default, no-API-key data source: it scrapes Yahoo Finance's
public endpoints via the `yfinance` package. It needs outbound internet
access to `query1.finance.yahoo.com` / `query2.finance.yahoo.com`, which
sandboxed or firewalled environments (including the one this project was
originally built in) may not have. When it can't reach Yahoo, it raises
`ProviderError` and `DataService` fails over per its configured policy —
see `app/data/service.py`.
"""

from __future__ import annotations

import asyncio
import math
from datetime import date

import pandas as pd
import yfinance as yf

from app.data import ticker_directory
from app.data.providers.base import (
    MarketDataProvider,
    ProviderError,
    RateLimitedError,
    TickerNotFoundError,
)
from app.data.schemas import (
    CompanyProfile,
    DataSource,
    DividendHistory,
    DividendPayment,
    FinancialStatement,
    FundamentalsSnapshot,
    OHLCVBar,
    PriceHistory,
    QuoteSnapshot,
    StatementFrequency,
    StatementLineItem,
    StatementType,
)

_VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "ytd", "1y", "2y", "5y", "10y", "max"}


def _clean(value: object) -> float | None:
    """yfinance returns NaN / None inconsistently across fields; normalize both to None."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


class YFinanceProvider(MarketDataProvider):
    name = "yfinance"

    async def get_price_history(self, ticker: str, *, period: str = "1y") -> PriceHistory:
        if period not in _VALID_PERIODS:
            raise ProviderError(f"Unsupported period '{period}'")
        df = await asyncio.to_thread(self._fetch_history_sync, ticker, period)
        if df is None or df.empty:
            raise TickerNotFoundError(f"No historical data found for '{ticker}'")

        bars = [
            OHLCVBar(
                trade_date=idx.date() if hasattr(idx, "date") else idx,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                adj_close=float(row.get("Adj Close", row["Close"])),
                volume=int(row["Volume"]) if not math.isnan(row["Volume"]) else 0,
            )
            for idx, row in df.iterrows()
        ]
        return PriceHistory(
            ticker=ticker.upper(),
            source=DataSource.YFINANCE,
            is_synthetic=False,
            bars=bars,
        )

    def _fetch_history_sync(self, ticker: str, period: str) -> pd.DataFrame:
        try:
            t = yf.Ticker(ticker)
            return t.history(period=period, auto_adjust=False)
        except Exception as exc:  # yfinance raises assorted requests/HTTP errors
            if "rate" in str(exc).lower():
                raise RateLimitedError() from exc
            raise ProviderError(f"yfinance request failed for '{ticker}': {exc}") from exc

    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        info = await asyncio.to_thread(self._fetch_info_sync, ticker)
        name = info.get("longName") or info.get("shortName")
        if not name:
            raise TickerNotFoundError(f"'{ticker}' is not a recognized ticker")
        return CompanyProfile(
            ticker=ticker.upper(),
            company_name=name,
            exchange=info.get("exchange"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            currency=info.get("currency") or "USD",
            source=DataSource.YFINANCE,
            is_synthetic=False,
        )

    def _fetch_info_sync(self, ticker: str) -> dict:
        try:
            return yf.Ticker(ticker).info or {}
        except Exception as exc:
            raise ProviderError(f"yfinance info request failed for '{ticker}': {exc}") from exc

    async def get_quote(self, ticker: str) -> QuoteSnapshot:
        info = await asyncio.to_thread(self._fetch_info_sync, ticker)
        price = _clean(info.get("currentPrice") or info.get("regularMarketPrice"))
        prev_close = _clean(info.get("previousClose") or info.get("regularMarketPreviousClose"))
        if price is None or prev_close is None:
            raise TickerNotFoundError(f"No quote available for '{ticker}'")
        change = price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0.0
        return QuoteSnapshot(
            ticker=ticker.upper(),
            price=price,
            previous_close=prev_close,
            change=change,
            change_percent=change_pct,
            market_cap=_clean(info.get("marketCap")),
            week52_high=_clean(info.get("fiftyTwoWeekHigh")),
            week52_low=_clean(info.get("fiftyTwoWeekLow")),
            dividend_yield=_clean(info.get("dividendYield")),
            source=DataSource.YFINANCE,
            is_synthetic=False,
        )

    async def get_fundamentals(self, ticker: str) -> FundamentalsSnapshot:
        info = await asyncio.to_thread(self._fetch_info_sync, ticker)
        return FundamentalsSnapshot(
            ticker=ticker.upper(),
            pe_ratio=_clean(info.get("trailingPE")),
            forward_pe=_clean(info.get("forwardPE")),
            price_to_sales=_clean(info.get("priceToSalesTrailing12Months")),
            price_to_book=_clean(info.get("priceToBook")),
            peg_ratio=_clean(info.get("pegRatio") or info.get("trailingPegRatio")),
            ev_to_ebitda=_clean(info.get("enterpriseToEbitda")),
            gross_margin=_clean(info.get("grossMargins")),
            operating_margin=_clean(info.get("operatingMargins")),
            net_margin=_clean(info.get("profitMargins")),
            return_on_equity=_clean(info.get("returnOnEquity")),
            return_on_assets=_clean(info.get("returnOnAssets")),
            total_cash=_clean(info.get("totalCash")),
            total_debt=_clean(info.get("totalDebt")),
            debt_to_equity=_clean(info.get("debtToEquity")),
            current_ratio=_clean(info.get("currentRatio")),
            free_cash_flow=_clean(info.get("freeCashflow")),
            revenue_growth=_clean(info.get("revenueGrowth")),
            earnings_growth=_clean(info.get("earningsGrowth")),
            source=DataSource.YFINANCE,
            is_synthetic=False,
        )

    async def search(self, query: str, *, limit: int = 8) -> list[dict]:
        # Yahoo has no stable public search endpoint; see ticker_directory
        # module docstring for the production replacement path.
        return ticker_directory.search(query, limit=limit)

    async def get_financial_statement(
        self, ticker: str, *, statement_type: StatementType, frequency: StatementFrequency
    ) -> FinancialStatement:
        df = await asyncio.to_thread(self._fetch_statement_sync, ticker, statement_type, frequency)
        if df is None or df.empty:
            # Every real, tracked equity reports *some* line items for its
            # statements, so an empty result here is a much stronger "this
            # didn't actually work" signal than an empty dividend history
            # (see get_dividends) — raise so DataService fails over to the
            # honestly-labeled synthetic provider instead of this method
            # unilaterally returning an empty result mislabeled as yfinance.
            raise TickerNotFoundError(
                f"No {statement_type} data available for '{ticker}' ({frequency})"
            )

        # yfinance returns line items as rows, period-end dates as columns,
        # most-recent period first.
        periods = [col.date().isoformat() if hasattr(col, "date") else str(col) for col in df.columns]
        line_items = [
            StatementLineItem(
                label=str(label),
                values={
                    periods[i]: _clean(df.loc[label].iloc[i]) for i in range(len(periods))
                },
            )
            for label in df.index
        ]
        return FinancialStatement(
            ticker=ticker.upper(),
            statement_type=statement_type,
            frequency=frequency,
            periods=periods,
            line_items=line_items,
            source=DataSource.YFINANCE,
            is_synthetic=False,
        )

    def _fetch_statement_sync(self, ticker: str, statement_type: StatementType, frequency: StatementFrequency):
        attr = {
            ("income_statement", "annual"): "income_stmt",
            ("income_statement", "quarterly"): "quarterly_income_stmt",
            ("balance_sheet", "annual"): "balance_sheet",
            ("balance_sheet", "quarterly"): "quarterly_balance_sheet",
            ("cash_flow", "annual"): "cashflow",
            ("cash_flow", "quarterly"): "quarterly_cashflow",
        }[(statement_type, frequency)]
        try:
            return getattr(yf.Ticker(ticker), attr)
        except Exception as exc:
            raise ProviderError(f"yfinance statement request failed for '{ticker}': {exc}") from exc

    async def get_dividends(self, ticker: str) -> DividendHistory:
        # Note: yfinance returns an empty Series both when a company
        # genuinely has never paid a dividend (a real, common, valid
        # answer) and, in some failure modes, when the underlying request
        # fails silently — the two aren't reliably distinguishable from
        # this signal alone. We treat empty as "no dividends" rather than
        # erroring, since that's the far more common real-world case.
        series, info = await asyncio.to_thread(self._fetch_dividends_sync, ticker)
        payments = [
            DividendPayment(ex_date=idx.date() if hasattr(idx, "date") else idx, amount=float(amount))
            for idx, amount in series.items()
        ]
        return DividendHistory(
            ticker=ticker.upper(),
            payments=payments,
            trailing_annual_dividend_rate=_clean(info.get("trailingAnnualDividendRate")),
            dividend_yield=_clean(info.get("dividendYield")),
            source=DataSource.YFINANCE,
            is_synthetic=False,
        )

    def _fetch_dividends_sync(self, ticker: str):
        try:
            t = yf.Ticker(ticker)
            return t.dividends, (t.info or {})
        except Exception as exc:
            raise ProviderError(f"yfinance dividends request failed for '{ticker}': {exc}") from exc
