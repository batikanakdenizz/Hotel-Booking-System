# syntax=docker/dockerfile:1.7
# ============================================================
# Hotel Booking — Gateway service
# Build context: repo root (so we can COPY services/shared)
# ============================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# --- Install build deps (compilers for asyncpg etc.) only if a service needs them.
# Gateway is pure-Python so we skip them. Keeps the image small.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# --- Copy the shared package FIRST so its layer can be cached
COPY services/shared /shared

# --- Copy the service's requirements and install
COPY services/gateway/requirements.txt /app/requirements.txt
# Replace the editable path so pip can find /shared
RUN sed -i 's|-e ../shared|-e /shared|' /app/requirements.txt \
    && pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# --- Copy the service code last (changes most often → least caching benefit)
COPY services/gateway/app /app/app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8080/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
