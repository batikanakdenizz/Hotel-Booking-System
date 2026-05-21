"""Resend HTTP email client.

Tiny — Resend's REST API is one POST. We don't pull `resend` SDK to keep the
container slim.
"""
from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"


class EmailClient:
    def __init__(self, api_key: str, sender: str) -> None:
        self._api_key = api_key
        self._sender = sender
        self._http = httpx.AsyncClient(timeout=15.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def send(self, *, to: str, subject: str, html: str) -> bool:
        """Returns True on accepted (2xx), False on rejection.

        Resend free-tier test domain (onboarding@resend.dev) only delivers to
        the account's registered email. Rejections are logged but the consumer
        still acks the message (no point in requeueing — same outcome).
        """
        payload = {"from": self._sender, "to": [to], "subject": subject, "html": html}
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            r = await self._http.post(RESEND_ENDPOINT, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning("resend_transport_error", to=to, error=str(exc))
            return False

        if r.status_code >= 400:
            logger.warning(
                "resend_rejected", to=to, status=r.status_code, body=r.text[:200]
            )
            return False
        logger.info("email_sent", to=to, subject=subject, resend_id=r.json().get("id"))
        return True
