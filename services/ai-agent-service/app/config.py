"""ai-agent-service settings."""
from __future__ import annotations

from pydantic import Field

from shared.config import BaseServiceSettings


class AgentSettings(BaseServiceSettings):
    service_name: str = "ai-agent-service"

    # Groq (OpenAI-compatible API)
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_api_base: str = "https://api.groq.com/openai/v1"

    # Gateway URL — tools call the public API surface (search/booking/comments)
    # via this URL. Locally http://127.0.0.1:8080; on Render this is the
    # deployed gateway. Tools do NOT call the downstream services directly —
    # going through gateway gives us auth + rate limit + logging for free.
    gateway_url: str = Field(default="http://127.0.0.1:8080", description="Gateway base URL")

    # Tool-call loop safety: hard cap on iterations so a misbehaving LLM
    # can't make us hammer the gateway forever.
    max_tool_iterations: int = 5

    # Tools that send HTTP traffic via httpx — share timeouts with the gateway.
    tool_http_timeout_s: float = 30.0


settings = AgentSettings()
