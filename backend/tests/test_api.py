"""API-level integration tests.

Forces PRIMARY_PROVIDER=synthetic so these run offline and deterministically
in CI / this sandbox, without depending on Yahoo Finance being reachable.
"""

from __future__ import annotations

import os

os.environ["PRIMARY_PROVIDER"] = "synthetic"
os.environ["ENABLE_SYNTHETIC_FALLBACK"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.data.service import get_data_service

get_settings.cache_clear()

from app.main import app  # noqa: E402  (import after env vars are set)


@pytest.fixture(autouse=True)
def _fresh_service():
    """Reset the module-level DataService/settings singletons between tests
    so env var changes in this file always take effect."""
    import app.data.service as service_module

    get_settings.cache_clear()
    service_module._service_instance = None
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_overview_returns_synthetic_flagged_data(client):
    resp = client.get("/api/stocks/AAPL/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert body["is_synthetic"] is True
    assert body["source"] == "synthetic_demo"
    assert isinstance(body["price"], float)


def test_invalid_ticker_returns_400(client):
    resp = client.get("/api/stocks/not-a-real-ticker-123/overview")
    assert resp.status_code == 400


def test_prices_endpoint_shape(client):
    resp = client.get("/api/stocks/MSFT/prices", params={"period": "3mo"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "MSFT"
    assert len(body["bars"]) > 0
    bar = body["bars"][0]
    assert set(bar.keys()) == {"trade_date", "open", "high", "low", "close", "adj_close", "volume"}


def test_invalid_period_returns_400(client):
    resp = client.get("/api/stocks/AAPL/prices", params={"period": "3weeks"})
    assert resp.status_code == 400


def test_technicals_endpoint_shape(client):
    resp = client.get("/api/stocks/NVDA/technicals", params={"period": "1y"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["points"]) > 0
    # Early points won't have enough history for SMA-200; later ones should.
    assert body["points"][-1]["sma_20"] is not None


def test_returns_endpoint_math_is_internally_consistent(client):
    resp = client.get("/api/stocks/GOOGL/returns", params={"period": "1y", "initial_investment": 5000})
    assert resp.status_code == 200
    body = resp.json()
    expected_ending = 5000 * (1 + body["total_return_pct"] / 100)
    assert abs(body["ending_value"] - expected_ending) < 1.0


def test_risk_endpoint_with_benchmark(client):
    resp = client.get("/api/stocks/AMD/risk", params={"period": "1y", "benchmark": "SPY"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["beta"] is not None
    # Drawdown is always <= 0 by definition; no fixed lower bound since the
    # synthetic random walk's realized volatility varies run to run.
    assert body["max_drawdown_pct"] <= 0


def test_fundamentals_endpoint_is_all_none_in_synthetic_mode(client):
    # Synthetic mode must never fabricate plausible-looking fundamentals.
    resp = client.get("/api/stocks/TSLA/fundamentals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pe_ratio"] is None
    assert body["is_synthetic"] is True


def test_search_endpoint(client):
    resp = client.get("/api/stocks/search", params={"q": "apple"})
    assert resp.status_code == 200
    results = resp.json()
    assert any(r["ticker"] == "AAPL" for r in results)


def test_financial_statement_endpoint_is_empty_but_valid_in_synthetic_mode(client):
    # Fabricating income-statement figures is worse than an honest gap.
    resp = client.get("/api/stocks/AAPL/financials/income_statement", params={"frequency": "annual"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_synthetic"] is True
    assert body["periods"] == []
    assert body["line_items"] == []


def test_financial_statement_rejects_invalid_statement_type(client):
    resp = client.get("/api/stocks/AAPL/financials/not_a_real_statement")
    assert resp.status_code == 400


def test_financial_statement_rejects_invalid_frequency(client):
    resp = client.get("/api/stocks/AAPL/financials/income_statement", params={"frequency": "monthly"})
    assert resp.status_code == 400


def test_dividends_endpoint_is_empty_in_synthetic_mode(client):
    resp = client.get("/api/stocks/AAPL/dividends")
    assert resp.status_code == 200
    body = resp.json()
    assert body["payments"] == []
    assert body["is_synthetic"] is True


def test_overview_includes_dividend_yield_field(client):
    resp = client.get("/api/stocks/AAPL/overview")
    assert resp.status_code == 200
    assert "dividend_yield" in resp.json()


def test_compare_endpoint_basic(client):
    resp = client.get("/api/compare", params={"tickers": "AAPL,MSFT,GOOGL", "period": "1y"})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["tickers"]) == {"AAPL", "MSFT", "GOOGL"}
    assert len(body["series"]) == 3
    for s in body["series"]:
        assert len(s["normalized_return_pct"]) > 0
        # Normalized series should start at (or extremely near) 0% change.
        assert abs(s["normalized_return_pct"][0]["value"]) < 5.0
    # Correlation matrix diagonal is always 1.
    for t in body["tickers"]:
        assert abs(body["correlation_matrix"][t][t] - 1.0) < 1e-6


def test_compare_endpoint_rejects_too_many_tickers(client):
    resp = client.get("/api/compare", params={"tickers": "AAPL,MSFT,GOOGL,AMD,NVDA,META,TSLA"})
    assert resp.status_code == 400


def test_compare_endpoint_excludes_invalid_tickers_without_failing(client):
    resp = client.get("/api/compare", params={"tickers": "AAPL,not-valid-123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["tickers"] == ["AAPL"]
    assert len(body["excluded"]) == 1
    assert body["excluded"][0]["ticker"] == "NOT-VALID-123"


def test_compare_endpoint_requires_at_least_one_ticker(client):
    resp = client.get("/api/compare", params={"tickers": ""})
    assert resp.status_code == 400
