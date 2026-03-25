#!/usr/bin/env python3
"""
Database Seed Script for FinScopeMX
Downloads 1 year of historical data for 15 BMV tickers and inserts into PostgreSQL.
"""

import os
import sys
import time
from datetime import date, datetime

try:
    import yfinance as yf
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    print(f"ERROR: Missing dependency - {e}")
    print("Run: pip install yfinance sqlalchemy")
    sys.exit(1)

TICKERS = [
    "WALMEX.MX",
    "GMEXICOB.MX",
    "CEMEXCPO.MX",
    "AMXB.MX",
    "GFNORTEO.MX",
    "FEMSAUBD.MX",
    "KOFUBL.MX",
    "GAPB.MX",
    "ASURB.MX",
    "OMAB.MX",
    "BIMBOA.MX",
    "AC.MX",
    "GRUMAB.MX",
    "TLEVISACPO.MX",
    "KIMBER.MX",
    "GC=F",
    "SI=F",
    "^IXIC",
    "^GSPC",
    "BTC-USD",
]

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set")
    sys.exit(1)

DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def download_ticker_data(ticker: str, period: str = "1y") -> list:
    """Download historical data for a single ticker."""
    print(f"  Downloading {ticker}...", end=" ", flush=True)

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, auto_adjust=False)

        if hist.empty:
            print(f"WARNING: No data returned for {ticker}")
            return []

        records = []
        for idx, row in hist.iterrows():
            records.append({
                "date": idx.date() if isinstance(idx, datetime) else idx,
                "ticker": ticker,
                "open": float(row["Open"]) if not pd.isna(row["Open"]) else None,
                "high": float(row["High"]) if not pd.isna(row["High"]) else None,
                "low": float(row["Low"]) if not pd.isna(row["Low"]) else None,
                "close": float(row["Close"]) if not pd.isna(row["Close"]) else None,
                "adj_close": float(row["Adj Close"]) if not pd.isna(row.get("Adj Close", None)) else None,
                "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else None,
            })

        print(f"OK ({len(records)} rows)")
        return records

    except Exception as e:
        print(f"ERROR: {e}")
        return []


def create_table_if_not_exists():
    """Create the historical_prices table if it doesn't exist."""
    from sqlalchemy import text

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS historical_prices (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        ticker VARCHAR(20) NOT NULL,
        open DOUBLE PRECISION,
        high DOUBLE PRECISION,
        low DOUBLE PRECISION,
        close DOUBLE PRECISION,
        adj_close DOUBLE PRECISION,
        volume BIGINT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE (date, ticker)
    );
    CREATE INDEX IF NOT EXISTS ix_historical_prices_ticker_date ON historical_prices (ticker, date);
    CREATE INDEX IF NOT EXISTS ix_historical_prices_ticker ON historical_prices (ticker);
    CREATE INDEX IF NOT EXISTS ix_historical_prices_date ON historical_prices (date);
    """

    with engine.connect() as conn:
        for statement in create_table_sql.split(";"):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    print(f"  Note: {e}")
        conn.commit()
    print("  Table created/verified.")


def insert_records(records: list, ticker: str) -> int:
    """Insert or update records using ON CONFLICT."""
    from sqlalchemy import text

    if not records:
        return 0

    inserted = 0

    with engine.connect() as conn:
        for rec in records:
            sql = text("""
                INSERT INTO historical_prices (date, ticker, open, high, low, close, adj_close, volume)
                VALUES (:date, :ticker, :open, :high, :low, :close, :adj_close, :volume)
                ON CONFLICT (date, ticker) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    adj_close = EXCLUDED.adj_close,
                    volume = EXCLUDED.volume,
                    created_at = NOW()
            """)

            try:
                conn.execute(sql, rec)
                inserted += 1
            except Exception as e:
                print(f"    Error inserting {rec['date']}: {e}")

        conn.commit()

    return inserted


def seed_database():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("FinScopeMX Database Seeding")
    print("=" * 60)
    print(f"Database: {DATABASE_URL[:30]}...")
    print(f"Tickers: {len(TICKERS)}")
    print("=" * 60 + "\n")

    print("Step 1: Creating table if not exists...")
    create_table_if_not_exists()

    print("\nStep 2: Downloading ticker data...")
    print("-" * 40)

    total_records = 0
    failed_tickers = []

    for i, ticker in enumerate(TICKERS, 1):
        print(f"\n[{i}/{len(TICKERS)}] Processing: {ticker}")

        records = download_ticker_data(ticker, period="1y")

        if records:
            inserted = insert_records(records, ticker)
            total_records += inserted
            print(f"  Inserted/Updated: {inserted} records")
        else:
            failed_tickers.append(ticker)

        if i < len(TICKERS):
            wait_time = 2
            print(f"  Waiting {wait_time}s to avoid rate limits...")
            time.sleep(wait_time)

    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"Total records: {total_records}")
    print(f"Tickers processed: {len(TICKERS) - len(failed_tickers)}/{len(TICKERS)}")

    if failed_tickers:
        print(f"Failed tickers: {', '.join(failed_tickers)}")
    else:
        print("All tickers seeded successfully!")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        print("Installing pandas...")
        os.system(f"{sys.executable} -m pip install pandas")
        import pandas as pd

    seed_database()
