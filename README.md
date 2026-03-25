# FinScopeMX: Quantitative Market Intelligence Platform

FinScopeMX is a full-stack, open-access intelligence platform designed to analyze the Mexican Stock Market (BMV) alongside key global assets. It bridges the gap between raw financial data and actionable academic theory, providing 20-year historical data visualization, predictive algorithmic ranking, and an interactive paper-trading simulator.

This repository is strictly containerized and production-ready, optimized for seamless deployment via Coolify or standard Docker environments.

## Key Features

* **Data-Driven Dashboard:** Real-time Min-Max normalization ranking of 14 highly liquid Mexican equities (e.g., WALMEX, FEMSA, AMX) and 5 global macro assets (Gold, Silver, S&P 500, NASDAQ, Bitcoin).
* **High-Performance Visualization:** Renders up to 20 years of historical market data using optimized Lightweight Charts. Features dynamic memory handling and three analytical modes: Beginner (Line), Intermediate (Candlesticks), and Expert (Candlesticks + SMA-200).
* **Live Academic Hub (KaTeX):** A dedicated `/formulas` engine that renders complex quantitative finance mathematics (SDEs, Log Returns, Volatility) and injects live market data to calculate real-time educational examples.
* **Paper Trading Simulator:** A local-first, interactive game loop where users predict short-term price action (Bullish/Bearish) on blinded charts.
* **Persistent Leaderboard:** Asynchronous PostgreSQL integration that ranks top traders while maintaining strict ACID compliance.
* **Graceful Auth System:** JWT-based authentication with seamless fallback degradation, allowing guest users to explore the platform without crashing.

## Quantitative Foundation

The platform's logic is built on standard mathematical finance models, rendered natively in the browser:

* **Geometric Brownian Motion (SDEs):** dS_t = mu S_t dt + sigma S_t dW_t
* **Logarithmic Returns:** r_t = ln(P_t) - ln(P_{t-1})

## Technology Stack

* **Frontend:** React, Tailwind CSS, Lightweight Charts, React-KaTeX.
* **Backend:** Python, FastAPI, Pandas, Yahoo Finance API (yfinance).
* **Infrastructure:** Docker, Docker Compose, Nginx.
* **Database and Cache:** PostgreSQL, Redis.

## Deployment (Coolify / Docker)

This repository is configured for immediate deployment. There are no heavy `node_modules` or local `venv` folders included.

### 1. Environment Configuration

Duplicate the example environment file and populate it with your secure credentials:

```bash
cp .env.example .env
```

### 2. Standard Docker Deployment

Run the multi-container architecture in detached mode:

```bash
docker compose up --build -d
```

### 3. Coolify Deployment

If deploying via Coolify, simply connect this Git repository and select the Docker Compose deployment option. Coolify will automatically parse the docker-compose.yml file and provision the services. Ensure you map the environment variables directly in the Coolify dashboard.

## Architecture Overview

The application utilizes a microservices approach:

* **frontend:** Served via Nginx on port 80.
* **backend:** Uvicorn/FastAPI server handling data ingestion and statistical modeling.
* **db:** PostgreSQL instance securing user data and simulation logs.
* **redis:** Caching layer to prevent rate-limiting from upstream financial data providers.
