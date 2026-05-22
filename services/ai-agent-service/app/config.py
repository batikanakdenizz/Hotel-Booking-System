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
        """Accept any reasonable spelling of the gateway URL.

        Render's `fromService.property: host` returned bare service names
        ('hbs-gateway') instead of FQDNs, so an operator who copy-pasted that
        value into the dashboard would otherwise crash every tool call with an
        httpx ProtocolError. Be aggressive about turning typos into a working
        URL:
          - strip whitespace + trailing slash
          - prepend https:// (or http:// for localhost / 127.*)
          - if the host has no dot (e.g. 'hbs-gateway'), assume .onrender.com
        """
        v = v.strip().rstrip("/")
        if not v:
            raise ValueError("gateway_url must not be empty")
        if "://" not in v:
            scheme = "http" if v.startswith(("localhost", "127.")) else "https"
            v = f"{scheme}://{v}"
        # Now v has a scheme. Inspect the host portion.
        scheme, _, rest = v.partition("://")
        host_and_path = rest.split("/", 1)
        host = host_and_path[0]
        # Tail = trailing /path if any, e.g. '' or 'foo/bar'.
        tail = "/" + host_and_path[1] if len(host_and_path) == 2 else ""
        # Strip ':port' for the dot check.
        bare_host = host.split(":", 1)[0]
        if (
            "." not in bare_host
            and bare_host not in ("localhost",)
            and not bare_host.replace(".", "").isdigit()  # not an IP
        ):
            host = f"{bare_host}.onrender.com" + (host[len(bare_host) :] if ":" in host else "")
        return f"{scheme}://{host}{tail}".rstrip("/")


settings = AgentSettings()
