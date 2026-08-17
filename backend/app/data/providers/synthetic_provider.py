"""Synthetic fallback provider.

Generates deterministic, seeded geometric-Brownian-motion price paths.
This is NOT real market data and must never be presented as such.

Every object this provider returns has `is_synthetic=True` and
`source=DataSource.SYNTHETIC_DEMO`. The API layer forwards those flags
unchanged, and the frontend is required to render a visible "demo data"
banner whenever they're set (see `frontend/components/dashboard/DataSourceBanner`).

Use cases:
  - Automated tests, so `pytest` never depends on network access.
  - A local demo mode for developers/reviewers who don't want to wait
    on a real API and are fine looking at illustrative data.

It is deliberately NOT used as a silent, invisible substitute for a real
provider in production — see `DataService` for the failover policy.
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

import numpy as np

from app.data import ticker_directory
from app.data.providers.base import MarketDataProvider
from app.data.schemas import (
    CompanyProfile,
    DataSource,
    DividendHistory,
    FinancialStatement,
    FundamentalsSnapshot,
    OHLCVBar,
    PriceHistory,
    QuoteSnapshot,
    StatementFrequency,
    StatementType,
)

_PERIOD_TO_DAYS = {
    "1d": 1,
    "5d": 5,
    "1mo": 22,
    "3mo": 63,
    "6mo": 126,
    "ytd": 180,
    "1y": 252,
    "2y": 504,
    "5y": 1260,
    "10y": 2520,
    "max": 2520,
}


def _seed_for(ticker: str) -> int:
    """Deterministic seed so the same ticker always renders the same synthetic path."""
    digest = hashlib.sha256(ticker.upper().encode()).hexdigest()
    return int(digest[:8], 16)


def _synthetic_walk(ticker: str, n_days: int) -> tuple[np.ndarray, np.ndarray]:
    """Seeded GBM close-price path plus a plausible synthetic volume series."""
    rng = np.random.default_rng(_seed_for(ticker))
    start_price = 20 + (_seed_for(ticker) % 400)  # deterministic $20-$420 start
    mu, sigma = 0.0004, 0.02  # ~10%/yr drift, ~32%/yr vol, illustrative only
    daily_returns = rng.normal(mu, sigma, n_days)
    prices = start_price * np.exp(np.cumsum(daily_returns))
    base_volume = 5_000_000 + (_seed_for(ticker) % 20_000_000)
    volume = np.maximum(
        1_000, (base_volume * (1 + rng.normal(0, 0.3, n_days))).astype(int)
    )
    return prices, volume


class SyntheticProvider(MarketDataProvider):
    name = "synthetic_demo"

    async def get_price_history(self, ticker: str, *, period: str = "1y") -> PriceHistory:
        n_days = _PERIOD_TO_DAYS.get(period, 252)
        closes, volumes = _synthetic_walk(ticker, n_days)

        bars: list[OHLCVBar] = []
        cursor = date.today()
        dates: list[date] = []
        while len(dates) < n_days:
            cursor -= timedelta(days=1)
            if cursor.weekday() < 5:  # skip weekends
                dates.append(cursor)
        dates.reverse()

        rng = np.random.default_rng(_seed_for(ticker) + 1)
        for i, d in enumerate(dates):
            close = float(closes[i])
            intraday_spread = close * float(abs(rng.normal(0, 0.008)))
            open_px = close * (1 + float(rng.normal(0, 0.004)))
            bars.append(
                OHLCVBar(
                    trade_date=d,
                    open=round(open_px, 2),
                    high=round(max(open_px, close) + intraday_spread, 2),
                    low=round(min(open_px, close) - intraday_spread, 2),
                    close=round(close, 2),
                    adj_close=round(close, 2),
                    volume=int(volumes[i]),
                )
            )
        return PriceHistory(
            ticker=ticker.upper(),
            source=DataSource.SYNTHETIC_DEMO,
            is_synthetic=True,
            bars=bars,
        )

    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        entry = ticker_directory.lookup(ticker)
        return CompanyProfile(
            ticker=ticker.upper(),
            company_name=(entry["name"] if entry else f"{ticker.upper()} (Demo)"),
            exchange=(entry["exchange"] if entry else None),
            sector="Demo Sector",
            industry="Demo Industry",
            currency="USD",
            source=DataSource.SYNTHETIC_DEMO,
            is_synthetic=True,
        )

    async def get_quote(self, ticker: str) -> QuoteSnapshot:
        history = await self.get_price_history(ticker, period="5d")
        last, prev = history.bars[-1], history.bars[-2]
        change = last.close - prev.close
        change_pct = (change / prev.close) * 100 if prev.close else 0.0
        year_history = await self.get_price_history(ticker, period="1y")
        closes = [b.close for b in year_history.bars]
        return QuoteSnapshot(
            ticker=ticker.upper(),
            price=last.close,
            previous_close=prev.close,
            change=round(change, 2),
            change_percent=round(change_pct, 2),
            market_cap=None,
            week52_high=round(max(closes), 2),
            week52_low=round(min(closes), 2),
            source=DataSource.SYNTHETIC_DEMO,
            is_synthetic=True,
        )

    async def get_fundamentals(self, ticker: str) -> FundamentalsSnapshot:
        # Deliberately all-None: fabricating plausible-looking fundamentals
        # is exactly what the PRD forbids. Demo mode shows "N/A" here.
        return FundamentalsSnapshot(
            ticker=ticker.upper(),
            source=DataSource.SYNTHETIC_DEMO,
            is_synthetic=True,
        )

    async def search(self, query: str, *, limit: int = 8) -> list[dict]:
        return ticker_directory.search(query, limit=limit)

    async def get_financial_statement(
        self, ticker: str, *, statement_type: StatementType, frequency: StatementFrequency
    ) -> FinancialStatement:
        # Deliberately empty, same reasoning as get_fundamentals: a
        # fabricated income statement is far more misleading than an
        # honestly empty one, and nothing else in the app depends on
        # statement data to function.
        return FinancialStatement(
            ticker=ticker.upper(),
            statement_type=statement_type,
            frequency=frequency,
            periods=[],
            line_items=[],
            source=DataSource.SYNTHETIC_DEMO,
            is_synthetic=True,
        )

    async def get_dividends(self, ticker: str) -> DividendHistory:
        return DividendHistory(
            ticker=ticker.upper(),
            payments=[],
            trailing_annual_dividend_rate=None,
            dividend_yield=None,
            source=DataSource.SYNTHETIC_DEMO,
            is_synthetic=True,
        )
