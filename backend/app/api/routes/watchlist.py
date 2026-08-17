"""Watchlist endpoints. All routes require a logged-in user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_service, rate_limiter
from app.api.schemas_watchlist import WatchlistAddRequest, WatchlistItemOut
from app.data.service import DataService, InvalidTickerError, sanitize_ticker
from app.db.models import User, WatchlistItem

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"], dependencies=[Depends(rate_limiter)])


@router.get("", response_model=list[WatchlistItemOut])
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: DataService = Depends(get_service),
):
    result = await db.scalars(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id).order_by(WatchlistItem.added_at)
    )
    items = result.all()

    out: list[WatchlistItemOut] = []
    for item in items:
        try:
            quote = await service.get_quote(item.ticker)
            out.append(
                WatchlistItemOut(
                    ticker=item.ticker,
                    added_at=item.added_at,
                    price=quote.price,
                    change=quote.change,
                    change_percent=quote.change_percent,
                    source=quote.source,
                    is_synthetic=quote.is_synthetic,
                )
            )
        except Exception:  # noqa: BLE001 - one bad quote shouldn't break the whole list
            out.append(
                WatchlistItemOut(
                    ticker=item.ticker,
                    added_at=item.added_at,
                    price=None,
                    change=None,
                    change_percent=None,
                    source=None,
                    is_synthetic=False,
                )
            )
    return out


@router.post("", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    payload: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: DataService = Depends(get_service),
):
    try:
        ticker = sanitize_ticker(payload.ticker)
    except InvalidTickerError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    existing = await db.scalar(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.ticker == ticker)
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{ticker} is already on your watchlist.")

    item = WatchlistItem(user_id=current_user.id, ticker=ticker)
    db.add(item)
    await db.commit()

    quote = await service.get_quote(ticker)
    return WatchlistItemOut(
        ticker=ticker,
        added_at=item.added_at,
        price=quote.price,
        change=quote.change,
        change_percent=quote.change_percent,
        source=quote.source,
        is_synthetic=quote.is_synthetic,
    )


@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticker = ticker.upper()
    item = await db.scalar(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.ticker == ticker)
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{ticker} is not on your watchlist.")
    await db.delete(item)
    await db.commit()
