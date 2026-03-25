import secrets
import random
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.models import (
    GameEducationalNote,
    GameScore,
    GameSession,
    HistoricalPrice,
    PaperTradingSimulation,
    User,
)
from app.core.schemas import (
    GameRoundResponse,
    GameScoreResponse,
    GameSubmitRequest,
    LeaderboardEntry,
    OHLCVPoint,
)

router = APIRouter(prefix="/api/game", tags=["game"])


def _generate_session_id() -> str:
    return secrets.token_hex(16)


async def _get_random_ticker_with_data(db: AsyncSession) -> Optional[str]:
    result = await db.execute(
        text("""
            SELECT DISTINCT h.ticker
            FROM historical_prices h
            WHERE h.close IS NOT NULL
            AND (SELECT COUNT(*) FROM historical_prices WHERE ticker = h.ticker) > 200
            ORDER BY RANDOM()
            LIMIT 1
        """)
    )
    row = result.fetchone()
    return row[0] if row else None


async def _create_game_round(db: AsyncSession, user: Optional[User] = None) -> GameSession:
    ticker = await _get_random_ticker_with_data(db)
    if ticker is None:
        raise HTTPException(status_code=503, detail="No tickers available for game")

    end_date = date.today()
    window_days = random.choice([30, 60, 90])
    window_start = end_date - timedelta(days=window_days)

    partial_result = await db.execute(
        select(HistoricalPrice)
        .where(HistoricalPrice.ticker == ticker)
        .where(HistoricalPrice.date >= window_start)
        .where(HistoricalPrice.date <= end_date - timedelta(days=7))
        .order_by(HistoricalPrice.date)
    )
    partial_prices = partial_result.scalars().all()

    full_result = await db.execute(
        select(HistoricalPrice)
        .where(HistoricalPrice.ticker == ticker)
        .where(HistoricalPrice.date >= window_start)
        .where(HistoricalPrice.date <= end_date)
        .order_by(HistoricalPrice.date)
    )
    full_prices = full_result.scalars().all()

    partial_data = [
        {
            "date": p.date.isoformat(),
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "adj_close": p.adj_close,
            "volume": p.volume,
        }
        for p in partial_prices
    ]

    answer_data = [
        {
            "date": p.date.isoformat(),
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "adj_close": p.adj_close,
            "volume": p.volume,
        }
        for p in full_prices
    ]

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    session = GameSession(
        session_id=_generate_session_id(),
        user_id=user.id if user else None,
        ticker=ticker,
        window_start=window_start,
        window_end=end_date,
        partial_data=partial_data,
        answer_data=answer_data,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


@router.post("/start", response_model=GameRoundResponse)
async def start_game(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    session = await _create_game_round(db, current_user)

    return GameRoundResponse(
        session_id=session.session_id,
        ticker_hidden=True,
        partial_data=[
            OHLCVPoint(
                date=datetime.fromisoformat(d["date"]).date(),
                open=d["open"],
                high=d["high"],
                low=d["low"],
                close=d["close"],
                adj_close=d["adj_close"],
                volume=d["volume"],
            )
            for d in session.partial_data
        ],
        expires_at=session.expires_at,
    )


@router.post("/submit", response_model=GameScoreResponse)
async def submit_prediction(
    payload: GameSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    result = await db.execute(
        select(GameSession).where(GameSession.session_id == payload.session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="Game session not found")

    if session.submitted_at is not None:
        raise HTTPException(status_code=400, detail="Already submitted")

    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Game session expired")

    prediction_prices = {p.day: p.price for p in payload.prediction_points}
    answer_prices = {i + 1: point["close"] for i, point in enumerate(session.answer_data) if point.get("close")}

    if not answer_prices:
        raise HTTPException(status_code=400, detail="No answer data available")

    directional_correct = 0
    magnitude_total = 0

    for day, pred_price in prediction_prices.items():
        if day in answer_prices:
            actual_price = answer_prices[day]
            first_actual = session.answer_data[0]["close"] if session.answer_data and session.answer_data[0].get("close") else actual_price
            pred_direction = "up" if pred_price > first_actual else "down"
            actual_direction = "up" if actual_price > first_actual else "down"

            if pred_direction == actual_direction:
                directional_correct += 1

            pred_pct_change = ((pred_price - first_actual) / first_actual) * 100 if first_actual else 0
            actual_pct_change = ((actual_price - first_actual) / first_actual) * 100 if first_actual else 0
            magnitude_total += max(0, 100 - abs(pred_pct_change - actual_pct_change))

    directional_score = (directional_correct / len(prediction_prices)) * 100 if prediction_prices else 0
    magnitude_score = (magnitude_total / len(prediction_prices)) * 100 if prediction_prices else 0
    total_score = (directional_score * 0.6) + (magnitude_score * 0.4)

    session.submitted_at = datetime.now(timezone.utc)

    score = GameScore(
        session_id=session.session_id,
        user_id=current_user.id if current_user else None,
        directional_score=directional_score,
        magnitude_score=magnitude_score,
        total_score=total_score,
    )
    db.add(score)
    await db.commit()

    reveal_data = [
        OHLCVPoint(
            date=datetime.fromisoformat(d["date"]).date(),
            open=d["open"],
            high=d["high"],
            low=d["low"],
            close=d["close"],
            adj_close=d["adj_close"],
            volume=d["volume"],
        )
        for d in session.answer_data
    ]

    return GameScoreResponse(
        session_id=session.session_id,
        directional_score=directional_score,
        magnitude_score=magnitude_score,
        total_score=total_score,
        reveal_data=reveal_data,
        ticker=session.ticker,
        window_start=session.window_start,
        window_end=session.window_end,
    )


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT 
                gs.ticker,
                u.username,
                gs.total_score,
                gs.created_at,
                ROW_NUMBER() OVER (ORDER BY gs.total_score DESC) as rank
            FROM game_scores gs
            LEFT JOIN users u ON gs.user_id = u.id
            ORDER BY gs.total_score DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )
    rows = result.fetchall()

    return [
        LeaderboardEntry(
            rank=row[4],
            username=row[1] or "Anonymous",
            total_score=float(row[2]),
            ticker=row[0],
            created_at=row[3],
        )
        for row in rows
    ]


@router.get("/educational/{ticker}", response_model=List[dict])
async def get_educational_notes(
    ticker: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GameEducationalNote)
        .where(GameEducationalNote.ticker == ticker)
        .order_by(GameEducationalNote.created_at.desc())
        .limit(10)
    )
    notes = result.scalars().all()

    return [
        {
            "ticker": n.ticker,
            "date_window_label": n.date_window_label,
            "note": n.note_en,
            "what_happened": n.what_happened_en,
        }
        for n in notes
    ]


@router.post("/record-simulation")
async def record_simulation(
    ticker: str,
    prediction_date: date,
    start_date: date,
    end_date: date,
    user_prediction: str,
    predicted_direction: str,
    actual_direction: str,
    is_correct: bool,
    score: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    simulation = PaperTradingSimulation(
        user_id=current_user.id if current_user else None,
        username=current_user.username if current_user else "guest",
        ticker=ticker,
        prediction_date=prediction_date,
        start_date=start_date,
        end_date=end_date,
        user_prediction=user_prediction,
        predicted_direction=predicted_direction,
        actual_direction=actual_direction,
        is_correct=is_correct,
        score=score,
    )
    db.add(simulation)
    await db.commit()
    await db.refresh(simulation)
    
    return {"id": simulation.id, "status": "recorded"}
