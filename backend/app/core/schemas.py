from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_lowercase(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, hyphens, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_lowercase(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    preferred_language: str
    theme: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    preferred_language: str
    theme: str
    first_prediction_seen: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateMeRequest(BaseModel):
    preferred_language: Optional[str] = None
    theme: Optional[str] = None

    @field_validator("preferred_language")
    @classmethod
    def valid_language(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("es", "en"):
            raise ValueError("preferred_language must be 'es' or 'en'")
        return v

    @field_validator("theme")
    @classmethod
    def valid_theme(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("dark", "light"):
            raise ValueError("theme must be 'dark' or 'light'")
        return v


# ------------------------------------------------------------------
# Prices
# ------------------------------------------------------------------
class OHLCVPoint(BaseModel):
    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    adj_close: Optional[float]
    volume: Optional[int]

    class Config:
        from_attributes = True


class TickerHistoryResponse(BaseModel):
    ticker: str
    data: List[OHLCVPoint]


# ------------------------------------------------------------------
# Rankings
# ------------------------------------------------------------------
class TickerScoreResponse(BaseModel):
    ticker: str
    display_name: str
    rank: int
    return_30d: Optional[float]
    return_90d: Optional[float]
    annualized_volatility: Optional[float]
    rsi: Optional[float]
    score: float
    score_return: float
    score_volatility: float
    score_maxdd: float
    score_rsi: float
    score_sma: float


# ------------------------------------------------------------------
# Predictions
# ------------------------------------------------------------------
class PredictionRequest(BaseModel):
    ticker: str
    horizon_days: int

    @field_validator("horizon_days")
    @classmethod
    def valid_horizon(cls, v: int) -> int:
        if v not in (7, 30, 90):
            raise ValueError("horizon_days must be 7, 30, or 90")
        return v


class PredictionResponse(BaseModel):
    ticker: str
    horizon_days: int
    last_close: float
    last_date: date
    percentile_25: List[float]
    percentile_50: List[float]
    percentile_75: List[float]
    simulation_count: int
    disclaimer: str


# ------------------------------------------------------------------
# Game
# ------------------------------------------------------------------
class GameRoundResponse(BaseModel):
    session_id: str
    ticker_hidden: bool = True
    partial_data: List[OHLCVPoint]
    expires_at: datetime


class PredictionPoint(BaseModel):
    day: int
    price: float


class GameSubmitRequest(BaseModel):
    session_id: str
    prediction_points: List[PredictionPoint]

    @field_validator("prediction_points")
    @classmethod
    def validate_points(cls, v: list) -> list:
        if len(v) < 1 or len(v) > 5:
            raise ValueError("Must submit between 1 and 5 prediction points")
        return v


class GameScoreResponse(BaseModel):
    session_id: str
    directional_score: float
    magnitude_score: float
    total_score: float
    reveal_data: List[OHLCVPoint]
    ticker: str
    window_start: date
    window_end: date


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    total_score: float
    ticker: str
    created_at: datetime


# ------------------------------------------------------------------
# Simulation
# ------------------------------------------------------------------
class SimulationCreateRequest(BaseModel):
    ticker: str
    action: str
    hypothetical_amount_mxn: float
    entry_price: float
    rationale: Optional[str] = None

    @field_validator("action")
    @classmethod
    def valid_action(cls, v: str) -> str:
        if v not in ("BUY", "SELL"):
            raise ValueError("action must be BUY or SELL")
        return v

    @field_validator("hypothetical_amount_mxn")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("hypothetical_amount_mxn must be greater than zero")
        return v


class SimulationResponse(BaseModel):
    id: int
    ticker: str
    action: str
    hypothetical_amount_mxn: float
    entry_price: float
    exit_price: Optional[float]
    hypothetical_shares: Optional[float]
    hypothetical_pnl: Optional[float]
    rationale: Optional[str]
    score_at_time: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------
# Extended tickers
# ------------------------------------------------------------------
class ExtendedTickerRequest(BaseModel):
    symbol: str
    requested_years: int

    @field_validator("requested_years")
    @classmethod
    def valid_years(cls, v: int) -> int:
        if v not in (1, 5, 20):
            raise ValueError("requested_years must be 1, 5, or 20")
        return v


class ExtendedTickerStatusResponse(BaseModel):
    symbol: str
    display_name: str
    fetch_status: str
    last_fetched: Optional[datetime]
    requested_by_count: int


# ------------------------------------------------------------------
# Admin
# ------------------------------------------------------------------
class AdminUserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class AdminRoleUpdateRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("admin", "user"):
            raise ValueError("role must be admin or user")
        return v


class ETLStatusResponse(BaseModel):
    id: int
    run_type: str
    status: str
    tickers_processed: Optional[int]
    rows_inserted: Optional[int]
    rows_failed: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    error_log: Optional[str]

    class Config:
        from_attributes = True


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
