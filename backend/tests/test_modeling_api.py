from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_forecast_endpoint_shape(client):
    resp = client.get("/api/stocks/AAPL/forecast", params={"period": "2y"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert body["n_predictions"] > 0
    assert body["next_predicted_return_pct"] is not None
    assert "disclaimer" in body and len(body["disclaimer"]) > 50
    assert "random" in body["disclaimer"].lower() or "not investment advice" in body["disclaimer"].lower()


def test_forecast_endpoint_reports_naive_comparison(client):
    resp = client.get("/api/stocks/MSFT/forecast", params={"period": "2y"})
    body = resp.json()
    assert body["beats_naive_mae"] in (True, False)
    assert body["beats_naive_directional"] in (True, False)
    # MAE values must be non-negative percentages.
    assert body["model_mae_pct"] >= 0
    assert body["naive_zero_mae_pct"] >= 0


def test_forecast_endpoint_insufficient_history_returns_400(client):
    resp = client.get("/api/stocks/AAPL/forecast", params={"period": "5d"})
    assert resp.status_code == 400


def test_forecast_endpoint_invalid_period_returns_400(client):
    resp = client.get("/api/stocks/AAPL/forecast", params={"period": "3fortnights"})
    assert resp.status_code == 400


def test_backtest_sma_crossover_default(client):
    resp = client.get("/api/stocks/AAPL/backtest", params={"strategy": "sma_crossover", "period": "2y"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["strategy"] == "sma_crossover"
    assert len(body["equity_curve"]) > 0
    assert body["equity_curve"][0]["strategy_value"] > 0
    assert "disclaimer" in body


def test_backtest_rejects_fast_greater_than_slow(client):
    resp = client.get("/api/stocks/AAPL/backtest", params={"strategy": "sma_crossover", "fast": 50, "slow": 20})
    assert resp.status_code == 400


def test_backtest_rsi_mean_reversion(client):
    resp = client.get(
        "/api/stocks/AAPL/backtest",
        params={"strategy": "rsi_mean_reversion", "period": "2y", "oversold": 30, "overbought": 70},
    )
    assert resp.status_code == 200
    assert resp.json()["strategy"] == "rsi_mean_reversion"


def test_backtest_buy_and_hold_has_zero_or_one_trades(client):
    resp = client.get("/api/stocks/AAPL/backtest", params={"strategy": "buy_and_hold", "period": "1y"})
    assert resp.status_code == 200
    assert resp.json()["num_trades"] <= 1


def test_backtest_higher_costs_reduce_ending_value(client):
    cheap = client.get(
        "/api/stocks/AAPL/backtest",
        params={"strategy": "sma_crossover", "period": "2y", "transaction_cost_bps": 1, "slippage_bps": 1},
    ).json()
    expensive = client.get(
        "/api/stocks/AAPL/backtest",
        params={"strategy": "sma_crossover", "period": "2y", "transaction_cost_bps": 200, "slippage_bps": 200},
    ).json()
    if cheap["num_trades"] > 0:
        assert expensive["equity_curve"][-1]["strategy_value"] <= cheap["equity_curve"][-1]["strategy_value"]


def test_backtest_reports_outperformance_consistently(client):
    resp = client.get("/api/stocks/AAPL/backtest", params={"strategy": "sma_crossover", "period": "2y"})
    body = resp.json()
    expected = body["strategy_metrics"]["total_return_pct"] - body["buy_hold_metrics"]["total_return_pct"]
    assert abs(body["outperformance_pct"] - expected) < 1e-6


def test_backtest_invalid_strategy_returns_422(client):
    resp = client.get("/api/stocks/AAPL/backtest", params={"strategy": "not_a_real_strategy"})
    assert resp.status_code == 422
