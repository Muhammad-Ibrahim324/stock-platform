from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.data.schemas import DataSource


class HoldingCreateRequest(BaseModel):
    ticker: str
    shares: float = Field(gt=0)
    cost_basis_per_share: float = Field(ge=0)
    purchase_date: date
    notes: str | None = Field(default=None, max_length=500)


class HoldingUpdateRequest(BaseModel):
    shares: float | None = Field(default=None, gt=0)
    cost_basis_per_share: float | None = Field(default=None, ge=0)
    purchase_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)


class HoldingOut(BaseModel):
    id: str
    ticker: str
    shares: float
    cost_basis_per_share: float
    purchase_date: date
    notes: str | None
    created_at: datetime


class HoldingAnalytics(BaseModel):
    id: str
    ticker: str
    shares: float
    cost_basis_per_share: float
    cost_basis_total: float
    current_price: float | None
    current_value: float | None
    gain_loss: float | None
    gain_loss_pct: float | None
    weight_pct: float | None
    source: DataSource | None
    is_synthetic: bool


class PortfolioRiskSummary(BaseModel):
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    beta: float | None
    correlation_to_benchmark: float | None


class PortfolioAnalyticsResponse(BaseModel):
    holdings: list[HoldingAnalytics]
    total_cost_basis: float
    total_current_value: float
    total_gain_loss: float
    total_gain_loss_pct: float
    allocation_by_ticker: dict[str, float]
    allocation_by_sector: dict[str, float]
    risk: PortfolioRiskSummary | None
    risk_note: str
    excluded: list[dict]
    is_synthetic: bool
