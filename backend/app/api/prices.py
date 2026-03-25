from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.core.models import ApprovedTicker, HistoricalPrice, User
from app.core.schemas import (
    OHLCVPoint,
    TickerHistoryResponse,
    ExtendedTickerRequest,
    ExtendedTickerStatusResponse,
)
from app.core.rbac import require_permission
from app.core.security import hash_password
from app.config import get_settings
from datetime import datetime, timezone

router = APIRouter(prefix="/api/prices", tags=["prices"])
settings = get_settings()


@router.get("/tickers", response_model=List[str])
async def list_tickers(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HistoricalPrice.ticker)
        .distinct()
        .order_by(HistoricalPrice.ticker)
    )
    return [row[0] for row in result.fetchall()]


@router.get("/{ticker}", response_model=TickerHistoryResponse)
async def get_ticker_history(
    ticker: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(HistoricalPrice).where(HistoricalPrice.ticker == ticker)

    if start_date:
        query = query.where(HistoricalPrice.date >= start_date)
    if end_date:
        query = query.where(HistoricalPrice.date <= end_date)

    query = query.order_by(HistoricalPrice.date)

    result = await db.execute(query)
    prices = result.scalars().all()

    if not prices:
        raise HTTPException(status_code=404, detail="Ticker not found or no data available")

    data = [
        OHLCVPoint(
            date=p.date,
            open=p.open,
            high=p.high,
            low=p.low,
            close=p.close,
            adj_close=p.adj_close,
            volume=p.volume,
        )
        for p in prices
    ]

    return TickerHistoryResponse(ticker=ticker, data=data)


@router.get("/extended/tickers", response_model=List[ExtendedTickerStatusResponse])
async def list_extended_tickers(
    category: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ApprovedTicker)
    if category:
        query = query.where(ApprovedTicker.category == category)
    query = query.order_by(ApprovedTicker.display_name_es)

    result = await db.execute(query)
    tickers = result.scalars().all()

    return [
        ExtendedTickerStatusResponse(
            symbol=t.symbol,
            display_name=t.display_name_es,
            fetch_status=t.fetch_status,
            last_fetched=t.last_fetched,
            requested_by_count=t.requested_by_count,
        )
        for t in tickers
    ]


@router.get("/extended/{symbol}", response_model=TickerHistoryResponse)
async def get_extended_ticker_history(
    symbol: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    from app.core.models import OnDemandPrice

    query = select(OnDemandPrice).where(OnDemandPrice.symbol == symbol)

    if start_date:
        query = query.where(OnDemandPrice.date >= start_date)
    if end_date:
        query = query.where(OnDemandPrice.date <= end_date)

    query = query.order_by(OnDemandPrice.date)

    result = await db.execute(query)
    prices = result.scalars().all()

    if not prices:
        raise HTTPException(status_code=404, detail="Extended ticker not found or no data available")

    data = [
        OHLCVPoint(
            date=p.date,
            open=p.open,
            high=p.high,
            low=p.low,
            close=p.close,
            adj_close=p.adj_close,
            volume=p.volume,
        )
        for p in prices
    ]

    return TickerHistoryResponse(ticker=symbol, data=data)


@router.post("/extended/request", status_code=201)
async def request_extended_ticker(
    payload: ExtendedTickerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    result = await db.execute(
        select(ApprovedTicker).where(ApprovedTicker.symbol == payload.symbol)
    )
    ticker = result.scalar_one_or_none()

    if ticker is None:
        raise HTTPException(status_code=404, detail="Ticker not found in approved list")

    from app.core.models import DownloadQueue

    existing_job = await db.execute(
        select(DownloadQueue)
        .where(DownloadQueue.symbol == payload.symbol)
        .where(DownloadQueue.status.in_(["pending", "fetching"]))
    )
    if existing_job.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Download already in progress for this ticker")

    job = DownloadQueue(
        symbol=payload.symbol,
        requested_years=payload.requested_years,
        status="pending",
        requested_by_user_id=current_user.id if current_user else None,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    ticker.requested_by_count += 1
    await db.commit()

    return {"message": "Download queued", "job_id": job.id}
