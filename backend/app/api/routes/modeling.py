"""Forecasting and backtesting endpoints (PRD Phase 5).

Both routes lean entirely on `app/analytics/forecasting.py` and
`app/analytics/backtesting.py` for the actual math — this layer is just
data-fetch, parameter validation, and response shaping. See those modules'
docstrings for the honesty/no-lookahead guarantees behind the numbers.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.analytics import backtesting, forecasting
from app.analytics import risk as risk_analytics
from app.analytics import returns as returns_analytics
from app.analytics.utils import history_to_dataframe
from app.api.deps import get_service, rate_limiter
from app.api.routes.stocks import VALID_PERIODS
from app.api.schemas_modeling import (
    BacktestMetrics,
    BacktestResponse,
    EquityPoint,
    ForecastPoint,
    ForecastResponse,
)
from app.data.service import DataService

router = APIRouter(prefix="/api/stocks", tags=["modeling"], dependencies=[Depends(rate_limiter)])

MIN_TRAIN_DAYS = 126
REFIT_INTERVAL_DAYS = 21
MIN_ROWS_FOR_FORECAST = MIN_TRAIN_DAYS + 30  # need a meaningful out-of-sample stretch, not just a handful of days


@router.get("/{ticker}/forecast", response_model=ForecastResponse)
async def get_forecast(
    ticker: str,
    period: str = Query("2y"),
    service: DataService = Depends(get_service),
):
    if period not in VALID_PERIODS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid period '{period}'")

    history = await service.get_price_history(ticker, period=period)
    if history.is_empty:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No historical data could be found for this ticker.")

    df = history_to_dataframe(history)
    features = forecasting.build_feature_matrix(df)
    if len(features) < MIN_ROWS_FOR_FORECAST:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Not enough history to evaluate a forecast (~{MIN_ROWS_FOR_FORECAST} trading days needed "
            f"after warmup; got {len(features)}). Try a longer period.",
        )

    results = forecasting.walk_forward_forecast(
        features, min_train_days=MIN_TRAIN_DAYS, refit_interval_days=REFIT_INTERVAL_DAYS
    )
    scored = forecasting.evaluate_forecast(results)
    _, next_return = forecasting.fit_latest_model(features)

    chart_series = [
        ForecastPoint(trade_date=idx.date().isoformat(), actual_pct=round(row.actual * 100, 4), predicted_pct=round(row.predicted * 100, 4))
        for idx, row in results.iterrows()
    ]

    def as_pct(v: float | None) -> float | None:
        return None if v is None else v * 100

    return ForecastResponse(
        ticker=history.ticker,
        period=period,
        n_predictions=scored["n_predictions"],
        min_train_days=MIN_TRAIN_DAYS,
        refit_interval_days=REFIT_INTERVAL_DAYS,
        model_mae_pct=as_pct(scored["model_mae"]),
        model_rmse_pct=as_pct(scored["model_rmse"]),
        naive_zero_mae_pct=as_pct(scored["naive_zero_mae"]),
        naive_zero_rmse_pct=as_pct(scored["naive_zero_rmse"]),
        model_directional_accuracy_pct=as_pct(scored["model_directional_accuracy"]),
        naive_persistence_directional_accuracy_pct=as_pct(scored["naive_persistence_directional_accuracy"]),
        beats_naive_mae=scored["beats_naive_mae"],
        beats_naive_directional=scored["beats_naive_directional"],
        next_predicted_return_pct=round(next_return * 100, 4),
        chart_series=chart_series,
        source=history.source,
        is_synthetic=history.is_synthetic,
    )


StrategyParam = Literal["sma_crossover", "rsi_mean_reversion", "buy_and_hold"]


@router.get("/{ticker}/backtest", response_model=BacktestResponse)
async def get_backtest(
    ticker: str,
    strategy: StrategyParam = Query("sma_crossover"),
    period: str = Query("2y"),
    fast: int = Query(20, ge=2, le=100, description="sma_crossover: fast SMA window"),
    slow: int = Query(50, ge=5, le=300, description="sma_crossover: slow SMA window"),
    rsi_window: int = Query(14, ge=2, le=50, description="rsi_mean_reversion: RSI window"),
    oversold: float = Query(30, ge=1, le=49, description="rsi_mean_reversion: entry threshold"),
    overbought: float = Query(70, ge=51, le=99, description="rsi_mean_reversion: exit threshold"),
    transaction_cost_bps: float = Query(10.0, ge=0, le=500),
    slippage_bps: float = Query(5.0, ge=0, le=500),
    risk_free_rate: float = Query(0.04, ge=0, le=0.2),
    service: DataService = Depends(get_service),
):
    if period not in VALID_PERIODS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid period '{period}'")
    if strategy == "sma_crossover" and fast >= slow:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "'fast' window must be smaller than 'slow' window.")

    history = await service.get_price_history(ticker, period=period)
    if history.is_empty or len(history.bars) < 60:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not enough historical data to run a backtest.")

    df = history_to_dataframe(history)
    close = df["adj_close"]

    params: dict = {}
    if strategy == "sma_crossover":
        positions = backtesting.sma_crossover_signal(close, fast=fast, slow=slow)
        params = {"fast": fast, "slow": slow}
    elif strategy == "rsi_mean_reversion":
        positions = backtesting.rsi_mean_reversion_signal(close, window=rsi_window, oversold=oversold, overbought=overbought)
        params = {"rsi_window": rsi_window, "oversold": oversold, "overbought": overbought}
    else:  # buy_and_hold
        import pandas as pd

        positions = pd.Series(1.0, index=close.index)
        params = {}

    result = backtesting.run_backtest(close, positions, transaction_cost_bps=transaction_cost_bps, slippage_bps=slippage_bps)
    equity_curve = result["equity_curve"]
    buy_hold_curve = result["buy_hold_curve"]

    def metrics_for(series):
        summary = risk_analytics.risk_summary(series, None, risk_free_rate)
        return BacktestMetrics(
            total_return_pct=returns_analytics.total_return(series) * 100,
            annualized_return_pct=returns_analytics.annualized_return(series) * 100,
            annualized_volatility_pct=summary["annualized_volatility"] * 100,
            sharpe_ratio=summary["sharpe_ratio"],
            sortino_ratio=summary["sortino_ratio"],
            max_drawdown_pct=summary["max_drawdown_pct"] * 100,
        )

    strategy_metrics = metrics_for(equity_curve)
    buy_hold_metrics = metrics_for(buy_hold_curve)

    equity_points = [
        EquityPoint(trade_date=idx.date().isoformat(), strategy_value=round(float(s), 4), buy_hold_value=round(float(b), 4))
        for idx, s, b in zip(equity_curve.index, equity_curve.values, buy_hold_curve.values)
    ]

    return BacktestResponse(
        ticker=history.ticker,
        period=period,
        strategy=strategy,
        params=params,
        transaction_cost_bps=transaction_cost_bps,
        slippage_bps=slippage_bps,
        num_trades=result["num_trades"],
        total_costs_pct=result["total_costs_pct"],
        strategy_metrics=strategy_metrics,
        buy_hold_metrics=buy_hold_metrics,
        outperformance_pct=strategy_metrics.total_return_pct - buy_hold_metrics.total_return_pct,
        equity_curve=equity_points,
        source=history.source,
        is_synthetic=history.is_synthetic,
    )
