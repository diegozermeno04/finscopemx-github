# backend/Dockerfile
# Multi-stage build for the FastAPI backend.
# Stage 1 installs dependencies.
# Stage 2 copies only what is needed for runtime,
# keeping the final image lean and free of build tools.

# ── Stage 1: dependency builder ────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system deps required to compile some Python packages
# (psycopg2-binary does not need libpq-dev but cryptography does)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime image ─────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY ./app ./app
COPY alembic.ini .
COPY alembic ./alembic

# Create non-root user for security
RUN addgroup --system appgroup \
 && adduser --system --ingroup appgroup appuser \
 && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Default CMD runs Alembic migrations first, then starts Uvicorn.
# The Celery worker overrides this CMD in docker-compose.yml.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]

