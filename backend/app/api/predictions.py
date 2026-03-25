import numpy as np
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.core.models import HistoricalPrice, PredictionRun, User
from app.core.schemas import PredictionRequest, PredictionResponse

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


async def _get_price_history(db: AsyncSession, ticker: str, days: int = 90) -> List[float]:
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(HistoricalPrice)
        .where(HistoricalPrice.ticker == ticker)
        .where(HistoricalPrice.date >= start_date)
        .where(HistoricalPrice.date <= end_date)
        .order_by(HistoricalPrice.date)
    )
    prices = result.scalars().all()

    return [p.close for p in prices if p.close is not None]


def _run_monte_carlo(
    prices: List[float],
    horizon_days: int,
    simulations: int = 1000,
) -> tuple:
    if len(prices) < 30:
        raise HTTPException(status_code=400, detail="Insufficient historical data")

    daily_returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] and prices[i]:
            daily_returns.append((prices[i] - prices[i - 1]) / prices[i - 1])

    if len(daily_returns) < 30:
        raise HTTPException(status_code=400, detail="Insufficient valid price data")

    returns_arr = np.array(daily_returns)
    mu = np.mean(returns_arr)
    sigma = np.std(returns_arr)

    last_price = prices[-1]

    price_paths = np.zeros((simulations, horizon_days))
    for sim in range(simulations):
        price_paths[sim, 0] = last_price
        for day in range(1, horizon_days):
            random_return = np.random.normal(mu, sigma)
            price_paths[sim, day] = price_paths[sim, day - 1] * (1 + random_return)

    percentile_25 = np.percentile(price_paths, 25, axis=0)
    percentile_50 = np.percentile(price_paths, 50, axis=0)
    percentile_75 = np.percentile(price_paths, 75, axis=0)

    return (
        percentile_25.tolist(),
        percentile_50.tolist(),
        percentile_75.tolist(),
    )


@router.post("/run", response_model=PredictionResponse)
async def run_prediction(
    payload: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    prices = await _get_price_history(db, payload.ticker, days=90)

    if not prices:
        raise HTTPException(status_code=404, detail="No historical data found for ticker")

    last_close = prices[-1]
    last_date = date.today()

    percentile_25, percentile_50, percentile_75 = _run_monte_carlo(
        prices,
        payload.horizon_days,
        simulations=payload.simulation_count if hasattr(payload, 'simulation_count') else 1000,
    )

    if current_user:
        prediction = PredictionRun(
            user_id=current_user.id,
            ticker=payload.ticker,
            horizon_days=payload.horizon_days,
            simulation_count=1000,
            percentile_25=percentile_25,
            percentile_50=percentile_50,
            percentile_75=percentile_75,
        )
        db.add(prediction)
        await db.commit()
        await db.refresh(prediction)

        if not current_user.first_prediction_seen:
            current_user.first_prediction_seen = True
            await db.commit()

    disclaimer = (
        "This prediction is based on Monte Carlo simulations using historical data. "
        "Past performance does not guarantee future results. "
        "This is for educational purposes only and should not be considered investment advice."
    )

    return PredictionResponse(
        ticker=payload.ticker,
        horizon_days=payload.horizon_days,
        last_close=last_close,
        last_date=last_date,
        percentile_25=percentile_25,
        percentile_50=percentile_50,
        percentile_75=percentile_75,
        simulation_count=1000,
        disclaimer=disclaimer,
    )


@router.get("/history", response_model=List[dict])
async def get_prediction_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if not current_user:
        return []
    
    result = await db.execute(
        select(PredictionRun)
        .where(PredictionRun.user_id == current_user.id)
        .order_by(PredictionRun.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()

    return [
        {
            "id": r.id,
            "ticker": r.ticker,
            "horizon_days": r.horizon_days,
            "simulation_count": r.simulation_count,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]
