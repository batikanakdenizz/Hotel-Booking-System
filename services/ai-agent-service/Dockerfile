# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# No DB → no compilers needed at the bottom of Phase 0.
# Phase 9 may add `fastmcp` and other deps; revisit then.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/shared /shared

COPY services/ai-agent-service/requirements.txt /app/requirements.txt
RUN sed -i 's|-e ../shared|-e /shared|' /app/requirements.txt \
    && pip install --upgrade pip \
    && pip install -r /app/requirements.txt

COPY services/ai-agent-service/app /app/app
COPY services/ai-agent-service/mcp_server /app/mcp_server

EXPOSE 8006

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8006/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
