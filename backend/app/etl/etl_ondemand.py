import asyncio
import random
import time
from datetime import date, datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

from app.core.models import ApprovedTicker, DownloadQueue
from app.etl.etl_core import _download_chunk

DATABASE_URL = os.getenv("DATABASE_URL", "")


async def process_download_queue_job(job_id: int) -> dict:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            select(DownloadQueue).where(DownloadQueue.id == job_id)
        )
        job = result.scalar_one_or_none()

        if job is None:
            await engine.dispose()
            return {"error": f"Job {job_id} not found"}

        job.status = "fetching"
        await session.commit()

        symbol = job.symbol
        years = job.requested_years

    end_date = date.today()
    start_date = end_date.replace(year=end_date.year - years)

    rows_inserted = 0
    error_message = None

    try:
        chunk_size_years = 2
        current = start_date
        while current < end_date:
            next_date = min(
                end_date,
                current.replace(year=current.year + chunk_size_years)
                if current.year + chunk_size_years <= 9999
                else end_date,
            )

            df = await asyncio.get_event_loop().run_in_executor(
                None, _download_chunk, symbol, current, next_date
            )

            if df is not None:
                adj_col = "Adj Close" if "Adj Close" in df.columns else "Close"
                async with async_session() as session:
                    for idx, row in df.iterrows():
                        row_date = idx.date() if hasattr(idx, "date") else idx
                        await session.execute(
                            text("""
                                INSERT INTO on_demand_prices
                                    (date, symbol, open, high, low, close, adj_close, volume)
                                VALUES
                                    (:date, :symbol, :open, :high, :low, :close, :adj_close, :volume)
                                ON CONFLICT (date, symbol) DO UPDATE SET
                                    open      = EXCLUDED.open,
                                    high      = EXCLUDED.high,
                                    low       = EXCLUDED.low,
                                    close     = EXCLUDED.close,
                                    adj_close = EXCLUDED.adj_close,
                                    volume    = EXCLUDED.volume
                            """),
                            {
                                "date": row_date,
                                "symbol": symbol,
                                "open": float(row.get("Open") or 0) or None,
                                "high": float(row.get("High") or 0) or None,
                                "low": float(row.get("Low") or 0) or None,
                                "close": float(row.get("Close") or 0) or None,
                                "adj_close": float(row.get(adj_col) or 0) or None,
                                "volume": int(row.get("Volume") or 0) or None,
                            },
                        )
                        rows_inserted += 1
                    await session.commit()

            time.sleep(random.uniform(8, 15))
            current = next_date

    except Exception as exc:
        error_message = str(exc)

    async with async_session() as session:
        result = await session.execute(
            select(DownloadQueue).where(DownloadQueue.id == job_id)
        )
        job = result.scalar_one()
        job.status = "failed" if error_message else "ready"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = error_message
        await session.commit()

        if not error_message:
            result = await session.execute(
                select(ApprovedTicker).where(ApprovedTicker.symbol == symbol)
            )
            ticker_ref = result.scalar_one_or_none()
            if ticker_ref:
                ticker_ref.fetch_status = "ready"
                ticker_ref.last_fetched = datetime.now(timezone.utc)
                await session.commit()

    await engine.dispose()
    return {
        "job_id": job_id,
        "symbol": symbol,
        "rows_inserted": rows_inserted,
        "status": "failed" if error_message else "ready",
        "error": error_message,
    }
