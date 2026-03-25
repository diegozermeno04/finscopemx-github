import asyncio
import time
import random
from datetime import date, timedelta
from typing import List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

from app.etl.etl_core import CORE_TICKERS, _download_chunk

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _get_weekdays(start: date, end: date) -> List[date]:
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


async def find_gaps(ticker: str, start: date, end: date) -> List[date]:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT date FROM historical_prices "
                "WHERE ticker = :ticker AND date BETWEEN :start AND :end "
                "ORDER BY date"
            ),
            {"ticker": ticker, "start": start, "end": end},
        )
        existing_dates = {row[0] for row in result.fetchall()}

    await engine.dispose()

    all_weekdays = set(_get_weekdays(start, end))
    gaps = sorted(all_weekdays - existing_dates)
    return gaps


async def reconcile_ticker(ticker: str, start: date, end: date) -> dict:
    gaps = await find_gaps(ticker, start, end)

    if not gaps:
        print(f"[{ticker}] No gaps found")
        return {"ticker": ticker, "gaps_found": 0, "gaps_filled": 0}

    print(f"[{ticker}] Found {len(gaps)} gap dates")

    gap_groups = []
    group_start = gaps[0]
    group_end = gaps[0]

    for gap_date in gaps[1:]:
        if (gap_date - group_end).days <= 5:
            group_end = gap_date
        else:
            gap_groups.append((
                group_start - timedelta(days=5),
                group_end + timedelta(days=5),
            ))
            group_start = gap_date
            group_end = gap_date

    gap_groups.append((
        group_start - timedelta(days=5),
        group_end + timedelta(days=5),
    ))

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    gaps_filled = 0

    for group_start_buf, group_end_buf in gap_groups:
        try:
            df = await asyncio.get_event_loop().run_in_executor(
                None,
                _download_chunk,
                ticker,
                max(group_start_buf, start),
                min(group_end_buf, end),
            )
            if df is None:
                continue

            adj_col = "Adj Close" if "Adj Close" in df.columns else "Close"

            async with async_session() as session:
                for idx, row in df.iterrows():
                    row_date = idx.date() if hasattr(idx, "date") else idx
                    if row_date in set(gaps):
                        await session.execute(
                            text("""
                                INSERT INTO historical_prices
                                    (date, ticker, open, high, low, close, adj_close, volume)
                                VALUES
                                    (:date, :ticker, :open, :high, :low, :close, :adj_close, :volume)
                                ON CONFLICT (date, ticker) DO NOTHING
                            """),
                            {
                                "date": row_date,
                                "ticker": ticker,
                                "open": float(row.get("Open") or 0) or None,
                                "high": float(row.get("High") or 0) or None,
                                "low": float(row.get("Low") or 0) or None,
                                "close": float(row.get("Close") or 0) or None,
                                "adj_close": float(row.get(adj_col) or 0) or None,
                                "volume": int(row.get("Volume") or 0) or None,
                            },
                        )
                        gaps_filled += 1
                await session.commit()

            time.sleep(random.uniform(5, 12))

        except Exception as exc:
            print(f"[{ticker}] reconcile group failed: {exc}")

    await engine.dispose()
    print(f"[{ticker}] Reconcile complete: {gaps_filled}/{len(gaps)} gaps filled")
    return {"ticker": ticker, "gaps_found": len(gaps), "gaps_filled": gaps_filled}


async def run_full_reconcile(years: int = 20) -> dict:
    from datetime import date
    end_date = date.today()
    start_date = end_date.replace(year=end_date.year - years)

    total_gaps = 0
    total_filled = 0

    for ticker in CORE_TICKERS:
        result = await reconcile_ticker(ticker, start_date, end_date)
        total_gaps += result["gaps_found"]
        total_filled += result["gaps_filled"]
        time.sleep(random.uniform(10, 20))

    return {
        "tickers_checked": len(CORE_TICKERS),
        "total_gaps_found": total_gaps,
        "total_gaps_filled": total_filled,
    }
