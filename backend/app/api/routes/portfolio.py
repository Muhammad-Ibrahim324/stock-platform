"""Portfolio endpoints. All routes require a logged-in user.

The analytics endpoint is the interesting one — it reuses the exact same
`app/analytics/returns.py` and `app/analytics/risk.py` functions built for
single-ticker research, by treating the portfolio's aggregate value over
time as just another price series. See `app/analytics/portfolio.py` for
what that does and doesn't mean.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import portfolio as portfolio_analytics
from app.analytics.utils import history_to_dataframe
from app.api.deps import get_current_user, get_db, get_service, rate_limiter
from app.api.schemas_portfolio import (
    HoldingAnalytics,
    HoldingCreateRequest,
    HoldingOut,
    HoldingUpdateRequest,
    PortfolioAnalyticsResponse,
    PortfolioRiskSummary,
)
from app.data.service import DataService, InvalidTickerError, sanitize_ticker
from app.db.models import PortfolioHolding, User

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"], dependencies=[Depends(rate_limiter)])


@router.get("/holdings", response_model=list[HoldingOut])
async def list_holdings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.scalars(
        select(PortfolioHolding)
        .where(PortfolioHolding.user_id == current_user.id)
        .order_by(PortfolioHolding.created_at)
    )
    return list(result.all())


@router.post("/holdings", response_model=HoldingOut, status_code=status.HTTP_201_CREATED)
async def add_holding(
    payload: HoldingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        ticker = sanitize_ticker(payload.ticker)
    except InvalidTickerError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    holding = PortfolioHolding(
        user_id=current_user.id,
        ticker=ticker,
        shares=payload.shares,
        cost_basis_per_share=payload.cost_basis_per_share,
        purchase_date=payload.purchase_date,
        notes=payload.notes,
    )
    db.add(holding)
    await db.commit()
    await db.refresh(holding)
    return holding


@router.put("/holdings/{holding_id}", response_model=HoldingOut)
async def update_holding(
    holding_id: str,
    payload: HoldingUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    holding = await db.get(PortfolioHolding, holding_id)
    if holding is None or holding.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Holding not found.")

    for field in ("shares", "cost_basis_per_share", "purchase_date", "notes"):
        value = getattr(payload, field)
        if value is not None:
            setattr(holding, field, value)

    await db.commit()
    await db.refresh(holding)
    return holding


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    holding_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    holding = await db.get(PortfolioHolding, holding_id)
    if holding is None or holding.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Holding not found.")
    await db.delete(holding)
    await db.commit()


@router.get("/analytics", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: DataService = Depends(get_service),
):
    result = await db.scalars(select(PortfolioHolding).where(PortfolioHolding.user_id == current_user.id))
    holdings = list(result.all())

    if not holdings:
        return PortfolioAnalyticsResponse(
            holdings=[],
            total_cost_basis=0.0,
            total_current_value=0.0,
            total_gain_loss=0.0,
            total_gain_loss_pct=0.0,
            allocation_by_ticker={},
            allocation_by_sector={},
            risk=None,
            risk_note="Add a holding to see portfolio analytics.",
            excluded=[],
            is_synthetic=False,
        )

    unique_tickers = sorted({h.ticker for h in holdings})

    quotes, histories, profiles = await asyncio.gather(
        asyncio.gather(*[service.get_quote(t) for t in unique_tickers], return_exceptions=True),
        asyncio.gather(*[service.get_price_history(t, period="1y") for t in unique_tickers], return_exceptions=True),
        asyncio.gather(*[service.get_company_profile(t) for t in unique_tickers], return_exceptions=True),
    )
    quotes = dict(zip(unique_tickers, quotes))
    histories = dict(zip(unique_tickers, histories))
    profiles = dict(zip(unique_tickers, profiles))

    excluded: list[dict] = []
    current_price_by_ticker: dict[str, float] = {}
    for t in unique_tickers:
        q = quotes[t]
        if isinstance(q, Exception):
            excluded.append({"ticker": t, "reason": "Current price unavailable."})
        else:
            current_price_by_ticker[t] = q.price

    holdings_out: list[HoldingAnalytics] = []
    total_cost_basis = 0.0
    total_current_value = 0.0
    any_synthetic = False

    for h in holdings:
        cost_basis_total = h.shares * h.cost_basis_per_share
        total_cost_basis += cost_basis_total
        price = current_price_by_ticker.get(h.ticker)
        current_value = h.shares * price if price is not None else None
        gain_loss = (current_value - cost_basis_total) if current_value is not None else None
        gain_loss_pct = gain_loss / cost_basis_total * 100 if gain_loss is not None and cost_basis_total > 0 else None
        q = quotes.get(h.ticker)
        source = None if isinstance(q, Exception) else q.source
        is_synth = False if isinstance(q, Exception) else q.is_synthetic
        any_synthetic = any_synthetic or is_synth
        if current_value is not None:
            total_current_value += current_value

        holdings_out.append(
            HoldingAnalytics(
                id=h.id,
                ticker=h.ticker,
                shares=h.shares,
                cost_basis_per_share=h.cost_basis_per_share,
                cost_basis_total=cost_basis_total,
                current_price=price,
                current_value=current_value,
                gain_loss=gain_loss,
                gain_loss_pct=gain_loss_pct,
                weight_pct=None,
                source=source,
                is_synthetic=is_synth,
            )
        )

    current_values_by_ticker: dict[str, float] = {}
    for ho in holdings_out:
        if ho.current_value is not None:
            current_values_by_ticker[ho.ticker] = current_values_by_ticker.get(ho.ticker, 0.0) + ho.current_value
    for ho in holdings_out:
        if ho.current_value is not None and total_current_value > 0:
            ho.weight_pct = ho.current_value / total_current_value * 100

    total_gain_loss = total_current_value - total_cost_basis
    total_gain_loss_pct = (total_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0.0

    allocation_by_ticker = (
        {t: v / total_current_value for t, v in current_values_by_ticker.items()} if total_current_value > 0 else {}
    )

    sector_by_ticker = {
        t: profiles[t].sector for t in unique_tickers if not isinstance(profiles[t], Exception) and profiles[t].sector
    }
    allocation_by_sector = portfolio_analytics.allocation_by_key(current_values_by_ticker, sector_by_ticker)

    total_shares_by_ticker: dict[str, float] = {}
    for h in holdings:
        total_shares_by_ticker[h.ticker] = total_shares_by_ticker.get(h.ticker, 0.0) + h.shares

    prices_by_ticker = {}
    for t in unique_tickers:
        hist = histories[t]
        if not isinstance(hist, Exception) and not hist.is_empty:
            prices_by_ticker[t] = history_to_dataframe(hist)["adj_close"]

    risk = None
    if not prices_by_ticker:
        risk_note = "No price history available to compute portfolio risk metrics."
    else:
        value_series = portfolio_analytics.portfolio_value_series(total_shares_by_ticker, prices_by_ticker)
        if len(value_series) < 2:
            risk_note = "Not enough overlapping price history across your holdings to compute risk metrics."
        else:
            bench_close = None
            try:
                bench_hist = await service.get_price_history("SPY", period="1y")
                if not bench_hist.is_empty:
                    bench_close = history_to_dataframe(bench_hist)["adj_close"]
            except Exception:  # noqa: BLE001 - benchmark is a nice-to-have, not required
                bench_close = None

            summary = portfolio_analytics.portfolio_risk_summary(value_series, bench_close)
            risk = PortfolioRiskSummary(
                annualized_volatility=summary["annualized_volatility"] * 100,
                sharpe_ratio=summary["sharpe_ratio"],
                sortino_ratio=summary["sortino_ratio"],
                max_drawdown_pct=summary["max_drawdown_pct"] * 100,
                beta=summary["beta"],
                correlation_to_benchmark=summary["correlation_to_benchmark"],
            )
            covered = set(prices_by_ticker.keys())
            if covered == set(unique_tickers):
                risk_note = (
                    "Based on today's holdings mix applied across the trailing 1-year daily prices — "
                    "a hypothetical of how the current portfolio would have behaved, not your realized "
                    "history (since positions were presumably bought at different times)."
                )
            else:
                missing = ", ".join(sorted(set(unique_tickers) - covered))
                risk_note = (
                    f"Computed using only {', '.join(sorted(covered))} ({missing} lacked sufficient price "
                    "history) — a hypothetical of how this partial mix would have behaved, not realized history."
                )

    return PortfolioAnalyticsResponse(
        holdings=holdings_out,
        total_cost_basis=total_cost_basis,
        total_current_value=total_current_value,
        total_gain_loss=total_gain_loss,
        total_gain_loss_pct=total_gain_loss_pct,
        allocation_by_ticker=allocation_by_ticker,
        allocation_by_sector=allocation_by_sector,
        risk=risk,
        risk_note=risk_note,
        excluded=excluded,
        is_synthetic=any_synthetic,
    )
