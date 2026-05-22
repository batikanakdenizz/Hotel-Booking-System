"""ai-agent-service settings."""
from __future__ import annotations

from pydantic import Field, field_validator

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

    @field_validator("gateway_url")
    @classmethod
    def _normalize_gateway_url(cls, v: str) -> str:
        """Accept either a bare hostname ('hbs-gateway') or a full URL.

        Render's `fromService.property: host` returned bare service names in
        practice, so an operator who copy-pastes that value into the dashboard
        would otherwise crash every tool call with an httpx ProtocolError.
        Defensively prepend https:// when the scheme is missing and strip any
        trailing slash so f-strings build clean URLs.
        """
        v = v.strip().rstrip("/")
        if not v:
            raise ValueError("gateway_url must not be empty")
        if "://" not in v:
            # Assume HTTPS for anything that looks like a hostname; only an
            # explicit localhost / 127.0.0.1 falls back to http.
            scheme = "http" if v.startswith(("localhost", "127.")) else "https"
            v = f"{scheme}://{v}"
        return v


settings = AgentSettings()
