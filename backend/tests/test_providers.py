"""Unit tests against providers directly, bypassing DataService.

These catch bugs in how a provider reports failure — e.g. a provider that
returns an empty result without raising can get silently mislabeled by
DataService as "this provider successfully returned nothing," when what
actually happened is the underlying request failed. See
YFinanceProvider.get_financial_statement for the case this guards.
"""

from __future__ import annotations

import pandas as pd
import pytest

from app.data.providers.base import TickerNotFoundError
from app.data.providers.synthetic_provider import SyntheticProvider
from app.data.providers.yfinance_provider import YFinanceProvider


@pytest.mark.asyncio
async def test_yfinance_statement_raises_on_empty_dataframe(monkeypatch):
    provider = YFinanceProvider()
    monkeypatch.setattr(provider, "_fetch_statement_sync", lambda *a, **k: pd.DataFrame())

    with pytest.raises(TickerNotFoundError):
        await provider.get_financial_statement("AAPL", statement_type="income_statement", frequency="annual")


@pytest.mark.asyncio
async def test_yfinance_statement_raises_on_none(monkeypatch):
    provider = YFinanceProvider()
    monkeypatch.setattr(provider, "_fetch_statement_sync", lambda *a, **k: None)

    with pytest.raises(TickerNotFoundError):
        await provider.get_financial_statement("AAPL", statement_type="balance_sheet", frequency="quarterly")


@pytest.mark.asyncio
async def test_synthetic_statement_is_always_empty_and_labeled_synthetic():
    provider = SyntheticProvider()
    statement = await provider.get_financial_statement("AAPL", statement_type="cash_flow", frequency="annual")
    assert statement.is_empty
    assert statement.is_synthetic is True


@pytest.mark.asyncio
async def test_synthetic_dividends_are_always_empty_and_labeled_synthetic():
    provider = SyntheticProvider()
    dividends = await provider.get_dividends("AAPL")
    assert dividends.payments == []
    assert dividends.is_synthetic is True
