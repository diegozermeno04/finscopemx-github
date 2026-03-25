import asyncio
import random
import socket as _socket
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

_orig_getaddrinfo = _socket.getaddrinfo


def _force_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, _socket.AF_INET, type, proto, flags)


_socket.getaddrinfo = _force_ipv4

import yfinance as yf
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

from app.core.models import ETLError, ETLRun, HistoricalPrice

DATABASE_URL = os.getenv("DATABASE_URL", "")

CORE_TICKERS = [
    "AC.MX", "AMX", "ASURB.MX", "CEMEXCPO.MX", "FEMSAUBD.MX",
    "GAPB.MX", "GFNORTEO.MX", "GMEXICOB.MX", "PENOLES.MX", "WALMEX.MX",
]

CHUNK_YEARS = 2
MIN_SLEEP_CHUNK = 8
MAX_SLEEP_CHUNK = 15
MIN_SLEEP_TICKER = 45
MAX_SLEEP_TICKER = 90

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def _warm_up_yahoo():
    try:
        from curl_cffi import requests as curl_requests
        s = curl_requests.Session(impersonate="chrome120")
        s.get("https://fc.yahoo.com", timeout=10)
        s.get("https://finance.yahoo.com", timeout=10)
    except Exception:
        pass


def _download_chunk(ticker: str, start: date, end: date) -> Optional[object]:
    try:
        _warm_up_yahoo()
        time.sleep(random.uniform(1, 3))

        t = yf.Ticker(ticker)
        df = t.history(
            start=start.isoformat(),
            end=end.isoformat(),
            auto_adjust=False,
            actions=False,
        )
        return df if not df.empty else None
    except Exception as exc:
        raise RuntimeError(
            f"yfinance download failed for {ticker}: {exc}"
        ) from exc


def _validate_row(row) -> Optional[str]:
    try:
        h = float(row.get("High") or 0)
        l = float(row.get("Low") or 0)
        c = float(row.get("Close") or 0)
        v = int(row.get("Volume") or 0)
    except (TypeError, ValueError) as exc:
        return f"Type conversion error: {exc}"

    if c <= 0:
        return f"Close price is zero or negative: {c}"
    if h > 0 and l > 0 and h < l:
        return f"High ({h}) is less than Low ({l})"
    if v < 0:
        return f"Volume is negative: {v}"
    return None


async def fetch_ticker_chunked(
    ticker: str,
    years: int = 20,
    etl_run_id: Optional[int] = None,
) -> dict:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    end_date = date.today()
    start_date = end_date.replace(year=end_date.year - years)

    chunk_starts = []
    current = start_date
    while current < end_date:
        chunk_starts.append(current)
        new_year = current.year + CHUNK_YEARS
        if new_year > end_date.year:
            break
        try:
            current = current.replace(year=new_year)
        except ValueError:
            current = current.replace(year=new_year, day=28)

    rows_inserted = 0
    rows_failed = 0

    async with async_session() as session:
        for i, chunk_start in enumerate(chunk_starts):
            try:
                next_year = chunk_start.year + CHUNK_YEARS
                chunk_end = min(
                    end_date,
                    chunk_start.replace(year=next_year)
                    if next_year <= 9999
                    else end_date,
                )
            except ValueError:
                chunk_end = end_date

            try:
                df = await asyncio.get_event_loop().run_in_executor(
                    None, _download_chunk, ticker, chunk_start, chunk_end
                )
            except RuntimeError as exc:
                rows_failed += 1
                if etl_run_id:
                    session.add(
                        ETLError(
                            etl_run_id=etl_run_id,
                            ticker=ticker,
                            date=chunk_start,
                            reason=str(exc),
                            retry_count=0,
                        )
                    )
                    await session.commit()
                time.sleep(random.uniform(MIN_SLEEP_CHUNK, MAX_SLEEP_CHUNK))
                continue

            if df is None:
                time.sleep(random.uniform(MIN_SLEEP_CHUNK, MAX_SLEEP_CHUNK))
                continue

            adj_col = "Adj Close" if "Adj Close" in df.columns else "Close"

            for idx, row in df.iterrows():
                row_date = idx.date() if hasattr(idx, "date") else idx

                validation_error = _validate_row(row)
                if validation_error:
                    rows_failed += 1
                    if etl_run_id:
                        session.add(
                            ETLError(
                                etl_run_id=etl_run_id,
                                ticker=ticker,
                                date=row_date,
                                reason=validation_error,
                                raw_data={
                                    "close": str(row.get("Close")),
                                    "volume": str(row.get("Volume")),
                                },
                            )
                        )
                    continue

                await session.execute(
                    text("""
                        INSERT INTO historical_prices
                            (date, ticker, open, high, low,
                             close, adj_close, volume)
                        VALUES
                            (:date, :ticker, :open, :high, :low,
                             :close, :adj_close, :volume)
                        ON CONFLICT (date, ticker) DO UPDATE SET
                            open      = EXCLUDED.open,
                            high      = EXCLUDED.high,
                            low       = EXCLUDED.low,
                            close     = EXCLUDED.close,
                            adj_close = EXCLUDED.adj_close,
                            volume    = EXCLUDED.volume
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
                rows_inserted += 1

            await session.commit()

            if i < len(chunk_starts) - 1:
                sleep_time = random.uniform(MIN_SLEEP_CHUNK, MAX_SLEEP_CHUNK)
                print(
                    f"  [{ticker}] chunk {i+1}/{len(chunk_starts)} done "
                    f"({rows_inserted} rows so far). "
                    f"Sleeping {sleep_time:.1f}s"
                )
                time.sleep(sleep_time)

    await engine.dispose()
    print(
        f"[{ticker}] complete: {rows_inserted} inserted, "
        f"{rows_failed} failed"
    )
    return {
        "ticker": ticker,
        "rows_inserted": rows_inserted,
        "rows_failed": rows_failed,
    }


async def run_full_etl(years: int = 20) -> dict:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        etl_run = ETLRun(
            run_type="manual",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(etl_run)
        await session.commit()
        await session.refresh(etl_run)
        etl_run_id = etl_run.id

    total_inserted = 0
    total_failed = 0

    for i, ticker in enumerate(CORE_TICKERS):
        print(f"\nProcessing {ticker} ({i+1}/{len(CORE_TICKERS)})")
        result = await fetch_ticker_chunked(
            ticker, years=years, etl_run_id=etl_run_id
        )
        total_inserted += result["rows_inserted"]
        total_failed += result["rows_failed"]

        if i < len(CORE_TICKERS) - 1:
            sleep_time = random.uniform(MIN_SLEEP_TICKER, MAX_SLEEP_TICKER)
            print(f"Sleeping {sleep_time:.1f}s before next ticker")
            time.sleep(sleep_time)

    async with async_session() as session:
        result = await session.execute(
            select(ETLRun).where(ETLRun.id == etl_run_id)
        )
        etl_run = result.scalar_one()
        etl_run.status = "complete"
        etl_run.tickers_processed = len(CORE_TICKERS)
        etl_run.rows_inserted = total_inserted
        etl_run.rows_failed = total_failed
        etl_run.completed_at = datetime.now(timezone.utc)
        await session.commit()

    await engine.dispose()
    return {
        "etl_run_id": etl_run_id,
        "tickers_processed": len(CORE_TICKERS),
        "total_inserted": total_inserted,
        "total_failed": total_failed,
    }


async def run_incremental_etl() -> dict:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        etl_run = ETLRun(
            run_type="scheduled",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(etl_run)
        await session.commit()
        await session.refresh(etl_run)
        etl_run_id = etl_run.id

    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    total_inserted = 0
    total_failed = 0

    for ticker in CORE_TICKERS:
        try:
            df = await asyncio.get_event_loop().run_in_executor(
                None, _download_chunk, ticker, start_date, end_date
            )
            if df is None:
                continue

            adj_col = "Adj Close" if "Adj Close" in df.columns else "Close"

            async with async_session() as session:
                for idx, row in df.iterrows():
                    row_date = idx.date() if hasattr(idx, "date") else idx
                    await session.execute(
                        text("""
                            INSERT INTO historical_prices
                                (date, ticker, open, high, low,
                                 close, adj_close, volume)
                            VALUES
                                (:date, :ticker, :open, :high, :low,
                                 :close, :adj_close, :volume)
                            ON CONFLICT (date, ticker) DO UPDATE SET
                                open      = EXCLUDED.open,
                                high      = EXCLUDED.high,
                                low       = EXCLUDED.low,
                                close     = EXCLUDED.close,
                                adj_close = EXCLUDED.adj_close,
                                volume    = EXCLUDED.volume
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
                    total_inserted += 1
                await session.commit()

            time.sleep(random.uniform(3, 8))

        except Exception as exc:
            total_failed += 1
            print(f"[incremental] {ticker} failed: {exc}")

    async with async_session() as session:
        result = await session.execute(
            select(ETLRun).where(ETLRun.id == etl_run_id)
        )
        etl_run = result.scalar_one()
        etl_run.status = "complete"
        etl_run.tickers_processed = len(CORE_TICKERS)
        etl_run.rows_inserted = total_inserted
        etl_run.rows_failed = total_failed
        etl_run.completed_at = datetime.now(timezone.utc)
        await session.commit()

    await engine.dispose()
    return {
        "etl_run_id": etl_run_id,
        "total_inserted": total_inserted,
        "total_failed": total_failed,
    }
