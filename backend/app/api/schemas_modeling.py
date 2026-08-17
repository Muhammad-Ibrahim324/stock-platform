from __future__ import annotations

from pydantic import BaseModel

from app.data.schemas import DataSource

FORECAST_DISCLAIMER = (
    "This forecast is a simple statistical baseline (ridge regression on lagged returns and "
    "technical indicators), evaluated walk-forward so it was never trained on data from after "
    "the day it predicted. It is shown for educational purposes to illustrate how forecasts "
    "should be evaluated, not because it reliably predicts price movements — daily stock "
    "returns are notoriously close to random, and the metrics below report honestly whether "
    "this model actually beats a naive baseline. Nothing here is investment advice."
)

BACKTEST_DISCLAIMER = (
    "This is a backtest of a simple rules-based strategy against historical prices, including "
    "estimated transaction costs and slippage. Backtested performance on historical data does "
    "not predict future results, and a strategy that performed well here may not going forward "
    "(especially if it was implicitly curve-fit by trying several parameter values). Nothing "
    "here is investment advice."
)


class ForecastPoint(BaseModel):
    trade_date: str
    actual_pct: float
    predicted_pct: float


class ForecastResponse(BaseModel):
    ticker: str
    period: str
    n_predictions: int
    min_train_days: int
    refit_interval_days: int
    model_mae_pct: float | None
    model_rmse_pct: float | None
    naive_zero_mae_pct: float | None
    naive_zero_rmse_pct: float | None
    model_directional_accuracy_pct: float | None
    naive_persistence_directional_accuracy_pct: float | None
    beats_naive_mae: bool | None
    beats_naive_directional: bool | None
    next_predicted_return_pct: float | None
    chart_series: list[ForecastPoint]
    source: DataSource
    is_synthetic: bool
    disclaimer: str = FORECAST_DISCLAIMER


class EquityPoint(BaseModel):
    trade_date: str
    strategy_value: float
    buy_hold_value: float


class BacktestMetrics(BaseModel):
    total_return_pct: float
    annualized_return_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float


class BacktestResponse(BaseModel):
    ticker: str
    period: str
    strategy: str
    params: dict
    transaction_cost_bps: float
    slippage_bps: float
    num_trades: int
    total_costs_pct: float
    strategy_metrics: BacktestMetrics
    buy_hold_metrics: BacktestMetrics
    outperformance_pct: float
    equity_curve: list[EquityPoint]
    source: DataSource
    is_synthetic: bool
    disclaimer: str = BACKTEST_DISCLAIMER
