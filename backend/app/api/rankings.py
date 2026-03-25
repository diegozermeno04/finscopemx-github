from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.core.schemas import TickerScoreResponse

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


async def _calculate_technical_metrics(db: AsyncSession, ticker: str, days: int = 90) -> dict:
    end_date = date.today()
    start_date = end_date - timedelta(days=days + 30)

    result = await db.execute(
        text("""
            SELECT date, close, volume
            FROM historical_prices
            WHERE ticker = :ticker AND date BETWEEN :start AND :end
            ORDER BY date DESC
            LIMIT :limit
        """),
        {"ticker": ticker, "start": start_date, "end": end_date, "limit": days + 30}
    )
    rows = result.fetchall()
    if not rows or len(rows) < 30:
        return None

    prices = [r[1] for r in rows if r[1] is not None]
    if len(prices) < 30:
        return None

    prices = list(reversed(prices))
    current_price = prices[-1]
    price_30d_ago = prices[-31] if len(prices) > 30 else prices[0]
    price_90d_ago = prices[0]

    return_30d = ((current_price / price_30d_ago) - 1) if price_30d_ago else None
    return_90d = ((current_price / price_90d_ago) - 1) if price_90d_ago else None

    daily_returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] and prices[i]:
            daily_returns.append((prices[i] - prices[i - 1]) / prices[i - 1])

    if not daily_returns:
        return None

    import numpy as np
    returns_arr = np.array(daily_returns)
    volatility = np.std(returns_arr) * (252 ** 0.5)

    cumulative = np.cumsum(returns_arr)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = cumulative - running_max
    max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

    gains = [r for r in daily_returns if r > 0]
    losses = [-r for r in daily_returns if r < 0]
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    rs = avg_gain / avg_loss if avg_loss > 0 else 0
    rsi = 100 - (100 / (1 + rs)) if rs > 0 else 50

    sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else None
    sma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else None

    score_return = max(0, return_90d * 100) if return_90d else 0
    score_volatility = max(0, (0.3 - volatility) / 0.3 * 100) if volatility else 0
    score_maxdd = max(0, (0.2 + max_drawdown) / 0.2 * 100) if max_drawdown else 100
    score_rsi = 100 - abs(50 - rsi) if rsi else 50
    score_sma = 100 if (sma_20 and sma_50 and sma_20 > sma_50) else 50

    total_score = (
        score_return * 0.30 +
        score_volatility * 0.25 +
        score_maxdd * 0.15 +
        score_rsi * 0.15 +
        score_sma * 0.15
    )

    return {
        "return_30d": return_30d,
        "return_90d": return_90d,
        "annualized_volatility": volatility,
        "rsi": rsi,
        "score": total_score,
        "score_return": score_return,
        "score_volatility": score_volatility,
        "score_maxdd": score_maxdd,
        "score_rsi": score_rsi,
        "score_sma": score_sma,
    }


@router.get("", response_model=List[TickerScoreResponse])
async def get_rankings(
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=90, ge=30, le=365),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT DISTINCT ticker FROM historical_prices ORDER BY ticker")
    )
    tickers = [row[0] for row in result.fetchall()]

    scored = []
    for ticker in tickers:
        metrics = await _calculate_technical_metrics(db, ticker, days)
        if metrics:
            result = await db.execute(
                text("SELECT display_name_es FROM approved_tickers WHERE symbol = :ticker"),
                {"ticker": ticker}
            )
            name_row = result.fetchone()
            display_name = name_row[0] if name_row else ticker

            scored.append(TickerScoreResponse(
                ticker=ticker,
                display_name=display_name,
                rank=0,
                return_30d=metrics["return_30d"],
                return_90d=metrics["return_90d"],
                annualized_volatility=metrics["annualized_volatility"],
                rsi=metrics["rsi"],
                score=metrics["score"],
                score_return=metrics["score_return"],
                score_volatility=metrics["score_volatility"],
                score_maxdd=metrics["score_maxdd"],
                score_rsi=metrics["score_rsi"],
                score_sma=metrics["score_sma"],
            ))

    scored.sort(key=lambda x: x.score, reverse=True)

    for i, item in enumerate(scored[:limit]):
        item.rank = i + 1

    return scored[:limit]
