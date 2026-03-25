import secrets
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import HistoricalPrice, SimulationLog, User
from app.core.schemas import SimulationCreateRequest, SimulationResponse

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


def _generate_session_token() -> str:
    return secrets.token_hex(32)


@router.post("", response_model=SimulationResponse, status_code=201)
async def create_simulation(
    payload: SimulationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HistoricalPrice)
        .where(HistoricalPrice.ticker == payload.ticker)
        .order_by(HistoricalPrice.date.desc())
        .limit(1)
    )
    latest_price = result.scalar_one_or_none()

    if latest_price is None or latest_price.close is None:
        raise HTTPException(status_code=404, detail="No price data found for ticker")

    entry_price = latest_price.close
    hypothetical_shares = payload.hypothetical_amount_mxn / entry_price

    session_token = _generate_session_token()

    score_query = await db.execute(
        text("""
            SELECT SUM(hypothetical_pnl) as total_pnl
            FROM simulation_logs
            WHERE user_id = :user_id
        """),
        {"user_id": current_user.id}
    )
    score_row = score_query.fetchone()
    score_at_time = score_row[0] if score_row and score_row[0] is not None else 0.0

    simulation = SimulationLog(
        user_id=current_user.id,
        session_token=session_token,
        ticker=payload.ticker,
        action=payload.action,
        hypothetical_amount_mxn=payload.hypothetical_amount_mxn,
        entry_price=entry_price,
        hypothetical_shares=hypothetical_shares,
        rationale=payload.rationale,
        score_at_time=score_at_time,
    )
    db.add(simulation)
    await db.commit()
    await db.refresh(simulation)

    return SimulationResponse(
        id=simulation.id,
        ticker=simulation.ticker,
        action=simulation.action,
        hypothetical_amount_mxn=simulation.hypothetical_amount_mxn,
        entry_price=simulation.entry_price,
        exit_price=simulation.exit_price,
        hypothetical_shares=simulation.hypothetical_shares,
        hypothetical_pnl=simulation.hypothetical_pnl,
        rationale=simulation.rationale,
        score_at_time=simulation.score_at_time,
        created_at=simulation.created_at,
    )


@router.post("/{simulation_id}/close")
async def close_simulation(
    simulation_id: int,
    exit_price: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SimulationLog)
        .where(SimulationLog.id == simulation_id)
        .where(SimulationLog.user_id == current_user.id)
    )
    simulation = result.scalar_one_or_none()

    if simulation is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if simulation.exit_price is not None:
        raise HTTPException(status_code=400, detail="Simulation already closed")

    simulation.exit_price = exit_price

    if simulation.action == "BUY" and simulation.hypothetical_shares:
        simulation.hypothetical_pnl = (exit_price - simulation.entry_price) * simulation.hypothetical_shares
    elif simulation.action == "SELL" and simulation.hypothetical_shares:
        simulation.hypothetical_pnl = (simulation.entry_price - exit_price) * simulation.hypothetical_shares
    else:
        simulation.hypothetical_pnl = 0

    await db.commit()
    await db.refresh(simulation)

    return {
        "id": simulation.id,
        "ticker": simulation.ticker,
        "action": simulation.action,
        "entry_price": simulation.entry_price,
        "exit_price": simulation.exit_price,
        "hypothetical_pnl": simulation.hypothetical_pnl,
    }


@router.get("", response_model=List[SimulationResponse])
async def list_simulations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SimulationLog)
        .where(SimulationLog.user_id == current_user.id)
        .order_by(SimulationLog.created_at.desc())
        .limit(50)
    )
    simulations = result.scalars().all()

    return [
        SimulationResponse(
            id=s.id,
            ticker=s.ticker,
            action=s.action,
            hypothetical_amount_mxn=s.hypothetical_amount_mxn,
            entry_price=s.entry_price,
            exit_price=s.exit_price,
            hypothetical_shares=s.hypothetical_shares,
            hypothetical_pnl=s.hypothetical_pnl,
            rationale=s.rationale,
            score_at_time=s.score_at_time,
            created_at=s.created_at,
        )
        for s in simulations
    ]


@router.get("/score")
async def get_simulation_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        text("""
            SELECT 
                COUNT(*) as total_trades,
                COALESCE(SUM(hypothetical_pnl), 0) as total_pnl,
                COALESCE(AVG(hypothetical_pnl), 0) as avg_pnl
            FROM simulation_logs
            WHERE user_id = :user_id AND exit_price IS NOT NULL
        """),
        {"user_id": current_user.id}
    )
    row = result.fetchone()

    return {
        "total_trades": row[0] if row else 0,
        "total_pnl": float(row[1]) if row else 0.0,
        "average_pnl": float(row[2]) if row else 0.0,
    }
