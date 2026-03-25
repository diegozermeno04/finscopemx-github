#!/usr/bin/env python3
"""
Quick score calculation for seeded tickers.
Computes RSI, volatility, returns for rankings.
"""

import os
import sys
from datetime import datetime, timedelta

try:
    import yfinance as yf
    from sqlalchemy import create_engine, text
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fintech:fintech_pass@localhost:5432/fintech_bmv")

TICKERS = [
    "WALMEX.MX", "GMEXICOB.MX", "CEMEXCPO.MX", "AMXB.MX", "GFNORTEO.MX",
    "FEMSAUBD.MX", "KOFUBL.MX", "GAPB.MX", "ASURB.MX", "OMAB.MX",
    "BIMBOA.MX", "AC.MX", "GRUMAB.MX", "TLEVISACPO.MX", "MFRISCOA.MX"
]

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_volatility(prices):
    if len(prices) < 2:
        return 0.0
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    return (variance ** 0.5) * (252 ** 0.5)

def calculate_return(prices, days):
    if len(prices) < days + 1:
        return 0.0
    return (prices[-1] - prices[-days-1]) / prices[-days-1]

def main():
    engine = create_engine(DATABASE_URL)
    
    print("Calculating scores for seeded tickers...")
    
    results = []
    
    for ticker in TICKERS:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT date, close 
                FROM historical_prices 
                WHERE ticker = :ticker 
                ORDER BY date DESC 
                LIMIT 252
            """), {"ticker": ticker})
            rows = list(result.fetchall())
        
        if not rows:
            print(f"  {ticker}: No data")
            continue
        
        prices = [r[1] for r in reversed(rows)]
        
        rsi = calculate_rsi(prices)
        volatility = calculate_volatility(prices)
        ret_30d = calculate_return(prices, 30) if len(prices) > 30 else 0
        ret_90d = calculate_return(prices, 90) if len(prices) > 90 else 0
        
        rsi_score = max(0, 100 - abs(rsi - 50) * 2)
        vol_score = max(0, 100 - volatility * 100)
        ret_score = min(100, max(0, 50 + ret_30d * 500))
        sma_score = 70 if len(prices) > 200 else 50
        
        score = (rsi_score * 0.25) + (vol_score * 0.20) + (ret_score * 0.30) + (sma_score * 0.25)
        
        results.append({
            "ticker": ticker,
            "score": round(score, 1),
            "rsi": round(rsi, 1),
            "volatility": round(volatility, 4),
            "return_30d": round(ret_30d, 4),
            "return_90d": round(ret_90d, 4),
        })
        
        print(f"  {ticker}: score={score:.1f}, rsi={rsi:.1f}, 30d={ret_30d*100:.1f}%")
    
    print(f"\nComputed {len(results)} rankings")
    return results

if __name__ == "__main__":
    main()
