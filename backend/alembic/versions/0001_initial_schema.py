"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(10), nullable=False, server_default="user"),
        sa.Column("preferred_language", sa.String(2), nullable=False, server_default="es"),
        sa.Column("theme", sa.String(5), nullable=False, server_default="dark"),
        sa.Column("first_prediction_seen", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),
        sa.CheckConstraint("preferred_language IN ('es', 'en')", name="ck_users_language"),
        sa.CheckConstraint("theme IN ('dark', 'light')", name="ck_users_theme"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    op.create_table(
        "historical_prices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("open", sa.Double, nullable=True),
        sa.Column("high", sa.Double, nullable=True),
        sa.Column("low", sa.Double, nullable=True),
        sa.Column("close", sa.Double, nullable=True),
        sa.Column("adj_close", sa.Double, nullable=True),
        sa.Column("volume", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("date", "ticker", name="uq_date_ticker"),
    )
    op.create_index("ix_historical_prices_ticker_date", "historical_prices", ["ticker", "date"])

    op.create_table(
        "approved_tickers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False, unique=True),
        sa.Column("display_name_es", sa.String(100), nullable=False),
        sa.Column("display_name_en", sa.String(100), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("is_default_visible", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("description_es", sa.Text, nullable=True),
        sa.Column("description_en", sa.Text, nullable=True),
        sa.Column("last_fetched", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetch_status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("requested_by_count", sa.Integer, nullable=False, server_default="0"),
        sa.CheckConstraint(
            "category IN ('global_commodity', 'us_equity', 'mx_equity')",
            name="ck_approved_tickers_category",
        ),
        sa.CheckConstraint(
            "fetch_status IN ('pending', 'fetching', 'ready', 'failed')",
            name="ck_approved_tickers_status",
        ),
    )

    op.create_table(
        "on_demand_prices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("symbol", sa.String(20), sa.ForeignKey("approved_tickers.symbol", ondelete="CASCADE"), nullable=False),
        sa.Column("open", sa.Double, nullable=True),
        sa.Column("high", sa.Double, nullable=True),
        sa.Column("low", sa.Double, nullable=True),
        sa.Column("close", sa.Double, nullable=True),
        sa.Column("adj_close", sa.Double, nullable=True),
        sa.Column("volume", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("date", "symbol", name="uq_on_demand_date_symbol"),
    )
    op.create_index("ix_on_demand_prices_symbol_date", "on_demand_prices", ["symbol", "date"])

    op.create_table(
        "download_queue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("symbol", sa.String(20), sa.ForeignKey("approved_tickers.symbol", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_years", sa.Integer, nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("requested_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.CheckConstraint("requested_years IN (1, 5, 20)", name="ck_download_queue_years"),
        sa.CheckConstraint(
            "status IN ('pending', 'fetching', 'ready', 'failed')",
            name="ck_download_queue_status",
        ),
    )

    op.create_table(
        "etl_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("run_type", sa.String(15), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="running"),
        sa.Column("tickers_processed", sa.Integer, nullable=True),
        sa.Column("rows_inserted", sa.Integer, nullable=True),
        sa.Column("rows_failed", sa.Integer, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_log", sa.Text, nullable=True),
        sa.CheckConstraint(
            "run_type IN ('scheduled', 'manual', 'ondemand')",
            name="ck_etl_runs_type",
        ),
        sa.CheckConstraint(
            "status IN ('running', 'complete', 'failed')",
            name="ck_etl_runs_status",
        ),
    )

    op.create_table(
        "etl_errors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("etl_run_id", sa.Integer, sa.ForeignKey("etl_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("date", sa.Date, nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("raw_data", JSONB, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_etl_errors_etl_run_id", "etl_errors", ["etl_run_id"])

    op.create_table(
        "simulation_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_token", sa.String(64), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("action", sa.String(4), nullable=False),
        sa.Column("hypothetical_amount_mxn", sa.Double, nullable=False),
        sa.Column("entry_price", sa.Double, nullable=False),
        sa.Column("exit_price", sa.Double, nullable=True),
        sa.Column("hypothetical_shares", sa.Double, nullable=True),
        sa.Column("hypothetical_pnl", sa.Double, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("score_at_time", sa.Double, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("action IN ('BUY', 'SELL')", name="ck_simulation_logs_action"),
    )
    op.create_index("ix_simulation_logs_user_id", "simulation_logs", ["user_id"])

    op.create_table(
        "prediction_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("horizon_days", sa.Integer, nullable=False),
        sa.Column("simulation_count", sa.Integer, nullable=False, server_default="1000"),
        sa.Column("percentile_25", JSONB, nullable=False),
        sa.Column("percentile_50", JSONB, nullable=False),
        sa.Column("percentile_75", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("horizon_days IN (7, 30, 90)", name="ck_prediction_runs_horizon"),
    )
    op.create_index("ix_prediction_runs_user_id", "prediction_runs", ["user_id"])

    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.String(36), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("window_start", sa.Date, nullable=False),
        sa.Column("window_end", sa.Date, nullable=False),
        sa.Column("partial_data", JSONB, nullable=False),
        sa.Column("answer_data", JSONB, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_game_sessions_session_id", "game_sessions", ["session_id"])
    op.create_index("ix_game_sessions_expires_at", "game_sessions", ["expires_at"])

    op.create_table(
        "game_scores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("game_sessions.session_id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("directional_score", sa.Float, nullable=False),
        sa.Column("magnitude_score", sa.Float, nullable=False),
        sa.Column("total_score", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_game_scores_user_id", "game_scores", ["user_id"])
    op.create_index("ix_game_scores_total_score", "game_scores", ["total_score"])

    op.create_table(
        "game_educational_notes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("date_window_label", sa.String(100), nullable=True),
        sa.Column("note_es", sa.Text, nullable=True),
        sa.Column("note_en", sa.Text, nullable=True),
        sa.Column("what_happened_es", sa.Text, nullable=True),
        sa.Column("what_happened_en", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_game_educational_notes_ticker", "game_educational_notes", ["ticker"])


def downgrade():
    op.drop_table("game_educational_notes")
    op.drop_table("game_scores")
    op.drop_table("game_sessions")
    op.drop_table("prediction_runs")
    op.drop_table("simulation_logs")
    op.drop_table("etl_errors")
    op.drop_table("etl_runs")
    op.drop_table("download_queue")
    op.drop_table("on_demand_prices")
    op.drop_table("approved_tickers")
    op.drop_table("historical_prices")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
