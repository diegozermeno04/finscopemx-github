from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.schemas import HealthResponse
from app.api import auth
from app.api import prices
from app.api import rankings
from app.api import predictions
from app.api import simulation
from app.api import game
from app.api import admin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="FinScopeMX API",
    version="1.0.0",
    description="Financial Instrument Analysis and Simulation Platform - Mexican Market Data",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(auth.router)
app.include_router(prices.router)
app.include_router(rankings.router)
app.include_router(predictions.router)
app.include_router(simulation.router)
app.include_router(game.router)
app.include_router(admin.router)


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.ENVIRONMENT,
    )
