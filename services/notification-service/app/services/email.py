"""Brevo (formerly Sendinblue) transactional email client.

Brevo lets us send from a verified single-sender address (e.g. a personal
Gmail / Hotmail) to ANY recipient on the free tier (300 emails/day),
without buying a domain. Compare to Resend's sandbox sender which only
delivers to the account owner's email.

API ref: https://developers.brevo.com/reference/sendtransacemail
"""
from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger(__name__)

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


class EmailClient:
    def __init__(self, api_key: str, sender_email: str, sender_name: str = "Stayfinder") -> None:
        self._api_key = api_key
        self._sender_email = sender_email
        self._sender_name = sender_name
        self._http = httpx.AsyncClient(timeout=15.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def send(self, *, to: str, subject: str, html: str) -> bool:
        """Returns True on accepted (2xx), False on rejection.

        Brevo returns 201 + `{"messageId": "..."}` on success; 4xx with an
        explanatory body on failure (bad sender, account locked, daily
        quota hit, etc.). We log + return False on 4xx so the consumer
        can still ack the message — re-queueing won't change the verdict.
        """
        payload = {
            "sender": {"email": self._sender_email, "name": self._sender_name},
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html,
        }
        headers = {"api-key": self._api_key, "content-type": "application/json"}
        try:
            r = await self._http.post(BREVO_ENDPOINT, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning("brevo_transport_error", to=to, error=str(exc))
            return False

        if r.status_code >= 400:
            logger.warning(
                "brevo_rejected", to=to, status=r.status_code, body=r.text[:200]
            )
            return False
        try:
            message_id = r.json().get("messageId")
        except Exception:  # noqa: BLE001 -- 2xx with empty body shouldn't happen, but be safe
            message_id = None
        logger.info("email_sent", to=to, subject=subject, brevo_message_id=message_id)
        return True
