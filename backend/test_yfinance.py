#!/usr/bin/env python3
"""
ETL Verification Script for FinScopeMX
Tests yfinance download for 'AMX.MX' with 1 year of data.
"""

import sys
from datetime import datetime, timedelta
from typing import Optional

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance")
    sys.exit(1)


def test_yfinance_download(ticker: str = "AMX", period: str = "1y") -> bool:
    """
    Attempt to download 1 year of data for the given ticker.
    Returns True on success, False on rate limit or other errors.
    """
    print(f"\n{'='*60}")
    print(f"Testing yfinance download for: {ticker}")
    print(f"Period: {period}")
    print(f"{'='*60}\n")

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            print(f"WARNING: No data returned for {ticker}")
            return False

        start_date = hist.index[0].strftime("%Y-%m-%d")
        end_date = hist.index[-1].strftime("%Y-%m-%d")
        rows = len(hist)

        print(f"SUCCESS: Downloaded {rows} data points")
        print(f"Date range: {start_date} to {end_date}")
        print(f"\nSample data (last 5 rows):")
        print(hist.tail()[['Close', 'Volume']].to_string())

        return True

    except Exception as e:
        error_msg = str(e).lower()

        if "429" in error_msg or "too many requests" in error_msg or "rate limit" in error_msg:
            print("\n" + "="*60)
            print("HTTP 429 RATE LIMIT ERROR DETECTED")
            print("="*60)
            print("Your IP has been blocked by Yahoo Finance.")
            print("Possible causes:")
            print("  - Too many requests in a short period")
            print("  - Running without a user agent")
            print("  - IP flagged as automated")
            print("\nRecommendations:")
            print("  1. Wait 15-60 minutes before retrying")
            print("  2. Use a VPN to get a new IP")
            print("  3. Add a custom user agent header")
            print("  4. Consider using async/celery with rate limiting")
            print("="*60)
            return False

        print(f"\nERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = test_yfinance_download("AMX", "1y")

    print("\n" + "="*60)
    if success:
        print("ETL VERIFICATION: PASSED")
        print("yfinance is working correctly for this ticker.")
    else:
        print("ETL VERIFICATION: FAILED")
        print("Check the error message above for details.")
    print("="*60 + "\n")

    sys.exit(0 if success else 1)
