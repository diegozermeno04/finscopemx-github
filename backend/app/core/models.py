from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, Date,
    DateTime, Double, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# ------------------------------------------------------------------
# Users
# ------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id                     = Column(Integer, primary_key=True, index=True)
    username               = Column(String(50), nullable=False, unique=True, index=True)
    password_hash          = Column(String(255), nullable=False)
    role                   = Column(String(10), nullable=False, default="user")
    preferred_language     = Column(String(2), nullable=False, default="es")
    theme                  = Column(String(5), nullable=False, default="dark")
    first_prediction_seen  = Column(Boolean, nullable=False, default=False)
    created_at             = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_login             = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),
        CheckConstraint("preferred_language IN ('es', 'en')", name="ck_users_language"),
        CheckConstraint("theme IN ('dark', 'light')", name="ck_users_theme"),
    )

    refresh_tokens   = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    simulation_logs  = relationship("SimulationLog", back_populates="user", cascade="all, delete-orphan")
    prediction_runs  = relationship("PredictionRun", back_populates="user", cascade="all, delete-orphan")
    game_scores      = relationship("GameScore", back_populates="user")


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash  = Column(String(255), nullable=False, unique=True)
    expires_at  = Column(DateTime(timezone=True), nullable=False)
    revoked     = Column(Boolean, nullable=False, default=False)
    created_at  = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


# ------------------------------------------------------------------
# Core market data
# ------------------------------------------------------------------
class HistoricalPrice(Base):
    __tablename__ = "historical_prices"

    id         = Column(Integer, primary_key=True, index=True)
    date       = Column(Date, nullable=False, index=True)
    ticker     = Column(String(20), nullable=False, index=True)
    open       = Column(Double, nullable=True)
    high       = Column(Double, nullable=True)
    low        = Column(Double, nullable=True)
    close      = Column(Double, nullable=True)
    adj_close  = Column(Double, nullable=True)
    volume     = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "ticker", name="uq_date_ticker"),
        Index("ix_historical_prices_ticker_date", "ticker", "date"),
    )


# ------------------------------------------------------------------
# On-demand extended tickers
# ------------------------------------------------------------------
class ApprovedTicker(Base):
    __tablename__ = "approved_tickers"

    id                  = Column(Integer, primary_key=True, index=True)
    symbol              = Column(String(20), nullable=False, unique=True, index=True)
    display_name_es     = Column(String(100), nullable=False)
    display_name_en     = Column(String(100), nullable=False)
    category            = Column(String(30), nullable=False)
    is_default_visible  = Column(Boolean, nullable=False, default=False)
    description_es      = Column(Text, nullable=True)
    description_en      = Column(Text, nullable=True)
    last_fetched        = Column(DateTime(timezone=True), nullable=True)
    fetch_status        = Column(String(10), nullable=False, default="pending")
    requested_by_count  = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint(
            "category IN ('global_commodity', 'us_equity', 'mx_equity')",
            name="ck_approved_tickers_category",
        ),
        CheckConstraint(
            "fetch_status IN ('pending', 'fetching', 'ready', 'failed')",
            name="ck_approved_tickers_status",
        ),
    )

    on_demand_prices = relationship("OnDemandPrice", back_populates="ticker_ref", cascade="all, delete-orphan")
    download_queue   = relationship("DownloadQueue", back_populates="ticker_ref", cascade="all, delete-orphan")


class OnDemandPrice(Base):
    __tablename__ = "on_demand_prices"

    id         = Column(Integer, primary_key=True, index=True)
    date       = Column(Date, nullable=False, index=True)
    symbol     = Column(String(20), ForeignKey("approved_tickers.symbol", ondelete="CASCADE"), nullable=False, index=True)
    open       = Column(Double, nullable=True)
    high       = Column(Double, nullable=True)
    low        = Column(Double, nullable=True)
    close      = Column(Double, nullable=True)
    adj_close  = Column(Double, nullable=True)
    volume     = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "symbol", name="uq_on_demand_date_symbol"),
        Index("ix_on_demand_prices_symbol_date", "symbol", "date"),
    )

    ticker_ref = relationship("ApprovedTicker", back_populates="on_demand_prices")


class DownloadQueue(Base):
    __tablename__ = "download_queue"

    id                   = Column(Integer, primary_key=True, index=True)
    symbol               = Column(String(20), ForeignKey("approved_tickers.symbol", ondelete="CASCADE"), nullable=False, index=True)
    requested_years      = Column(Integer, nullable=False)
    status               = Column(String(10), nullable=False, default="pending")
    requested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    retry_count          = Column(Integer, nullable=False, default=0)
    created_at           = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at         = Column(DateTime(timezone=True), nullable=True)
    error_message        = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("requested_years IN (1, 5, 20)", name="ck_download_queue_years"),
        CheckConstraint(
            "status IN ('pending', 'fetching', 'ready', 'failed')",
            name="ck_download_queue_status",
        ),
    )

    ticker_ref = relationship("ApprovedTicker", back_populates="download_queue")


# ------------------------------------------------------------------
# ETL tracking
# ------------------------------------------------------------------
class ETLRun(Base):
    __tablename__ = "etl_runs"

    id                = Column(Integer, primary_key=True, index=True)
    run_type          = Column(String(15), nullable=False)
    status            = Column(String(10), nullable=False, default="running")
    tickers_processed = Column(Integer, nullable=True)
    rows_inserted     = Column(Integer, nullable=True)
    rows_failed       = Column(Integer, nullable=True)
    started_at        = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at      = Column(DateTime(timezone=True), nullable=True)
    error_log         = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "run_type IN ('scheduled', 'manual', 'ondemand')",
            name="ck_etl_runs_type",
        ),
        CheckConstraint(
            "status IN ('running', 'complete', 'failed')",
            name="ck_etl_runs_status",
        ),
    )

    etl_errors = relationship("ETLError", back_populates="etl_run", cascade="all, delete-orphan")


class ETLError(Base):
    __tablename__ = "etl_errors"

    id          = Column(Integer, primary_key=True, index=True)
    etl_run_id  = Column(Integer, ForeignKey("etl_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker      = Column(String(20), nullable=False)
    date        = Column(Date, nullable=True)
    reason      = Column(Text, nullable=False)
    raw_data    = Column(JSONB, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    locked      = Column(Boolean, nullable=False, default=False)
    created_at  = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    etl_run = relationship("ETLRun", back_populates="etl_errors")


# ------------------------------------------------------------------
# Simulation (paper trading)
# ------------------------------------------------------------------
class SimulationLog(Base):
    __tablename__ = "simulation_logs"

    id                       = Column(Integer, primary_key=True, index=True)
    user_id                  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token            = Column(String(64), nullable=False, index=True)
    ticker                   = Column(String(20), nullable=False)
    action                   = Column(String(4), nullable=False)
    hypothetical_amount_mxn  = Column(Double, nullable=False)
    entry_price              = Column(Double, nullable=False)
    exit_price               = Column(Double, nullable=True)
    hypothetical_shares      = Column(Double, nullable=True)
    hypothetical_pnl         = Column(Double, nullable=True)
    rationale                = Column(Text, nullable=True)
    score_at_time            = Column(Double, nullable=True)
    created_at               = Column(DateTime(timezone=True), default=utcnow, nullable=True)

    __table_args__ = (
        CheckConstraint("action IN ('BUY', 'SELL')", name="ck_simulation_logs_action"),
    )

    user = relationship("User", back_populates="simulation_logs")


# ------------------------------------------------------------------
# Predictions (Monte Carlo)
# ------------------------------------------------------------------
class PredictionRun(Base):
    __tablename__ = "prediction_runs"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker           = Column(String(20), nullable=False)
    horizon_days     = Column(Integer, nullable=False)
    simulation_count = Column(Integer, nullable=False, default=1000)
    percentile_25    = Column(JSONB, nullable=False)
    percentile_50    = Column(JSONB, nullable=False)
    percentile_75    = Column(JSONB, nullable=False)
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("horizon_days IN (7, 30, 90)", name="ck_prediction_runs_horizon"),
    )

    user = relationship("User", back_populates="prediction_runs")


# ------------------------------------------------------------------
# Game
# ------------------------------------------------------------------
class GameSession(Base):
    __tablename__ = "game_sessions"

    id            = Column(Integer, primary_key=True, index=True)
    session_id    = Column(String(36), nullable=False, unique=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ticker        = Column(String(20), nullable=False)
    window_start  = Column(Date, nullable=False)
    window_end    = Column(Date, nullable=False)
    partial_data  = Column(JSONB, nullable=False)
    answer_data   = Column(JSONB, nullable=False)
    expires_at    = Column(DateTime(timezone=True), nullable=False, index=True)
    submitted_at  = Column(DateTime(timezone=True), nullable=True)
    created_at    = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    score = relationship("GameScore", back_populates="session", uselist=False, cascade="all, delete-orphan")


class GameScore(Base):
    __tablename__ = "game_scores"

    id                 = Column(Integer, primary_key=True, index=True)
    session_id         = Column(String(36), ForeignKey("game_sessions.session_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    user_id            = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    directional_score  = Column(Float, nullable=False)
    magnitude_score    = Column(Float, nullable=False)
    total_score        = Column(Float, nullable=False)
    created_at         = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("GameSession", back_populates="score")
    user    = relationship("User", back_populates="game_scores")


class GameEducationalNote(Base):
    __tablename__ = "game_educational_notes"

    id                  = Column(Integer, primary_key=True, index=True)
    ticker              = Column(String(20), nullable=False, index=True)
    date_window_label   = Column(String(100), nullable=True)
    note_es             = Column(Text, nullable=True)
    note_en             = Column(Text, nullable=True)
    what_happened_es    = Column(Text, nullable=True)
    what_happened_en    = Column(Text, nullable=True)
    created_at          = Column(DateTime(timezone=True), default=utcnow, nullable=False)


# ------------------------------------------------------------------
# Paper Trading Simulation Records (Objective #6)
# ------------------------------------------------------------------
class PaperTradingSimulation(Base):
    __tablename__ = "paper_trading_simulations"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id            = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username           = Column(String(50), nullable=True)
    ticker             = Column(String(20), nullable=False, index=True)
    prediction_date    = Column(Date, nullable=False)
    start_date         = Column(Date, nullable=False)
    end_date           = Column(Date, nullable=False)
    user_prediction    = Column(String(10), nullable=False)
    predicted_direction = Column(String(10), nullable=True)
    actual_direction   = Column(String(10), nullable=True)
    is_correct         = Column(Boolean, nullable=True)
    score              = Column(Integer, nullable=True)
    created_at         = Column(DateTime(timezone=True), default=utcnow, nullable=False)
