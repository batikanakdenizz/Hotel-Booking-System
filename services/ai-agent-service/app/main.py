"""AI Agent service — Phase 0 stub.

Real implementation lands in Phase 9:
  - POST /api/v1/agent/chat endpoint
  - Groq LLM client (httpx, OpenAI-compatible API)
  - MCP client managing a subprocess MCP server (FastMCP) with tools:
      search_hotels, book_hotel, get_hotel_comments
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.logging import configure_logging

SERVICE_NAME = "ai-agent-service"
logger = configure_logging(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting")
    # Phase 9: spawn the MCP server subprocess here.
    yield
    logger.info("service_stopping")


app = FastAPI(title="Hotel Booking — AI Agent Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}
