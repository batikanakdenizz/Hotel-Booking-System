"""Verify the 15% member discount end-to-end on production.

Flow:
  1. Mint a Firebase custom token for a demo user via the Admin SDK.
  2. Exchange it for an ID token via Firebase Identity Toolkit.
  3. Call /api/v1/search anonymously -- record prices.
  4. Call the same /api/v1/search with `Authorization: Bearer <id_token>`.
  5. Diff and report.

Reads FIREBASE_SERVICE_ACCOUNT_JSON and VITE_FIREBASE_API_KEY from the local
.env (the frontend .env contains the web API key needed for token exchange).
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import brotli
import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / "frontend" / ".env")

GATEWAY = os.environ.get("DEMO_GATEWAY_URL", "https://hbs-gateway.onrender.com")
API_KEY = os.environ["VITE_FIREBASE_API_KEY"]
DEMO_UID = "discount-verify-demo-user"


def decode(r: httpx.Response) -> dict:
    body = r.content
    for fn in [lambda b: b, lambda b: brotli.decompress(b), lambda b: gzip.decompress(b)]:
        try:
            return json.loads(fn(body).decode("utf-8"))
        except Exception:
            continue
    raise RuntimeError(f"could not decode body, first bytes: {body[:8].hex()}")


def mint_id_token() -> str:
    """Use Admin SDK to make a custom token, then exchange via Identity Toolkit."""
    import firebase_admin
    from firebase_admin import credentials, auth

    path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
    json_blob = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if path:
        cred = credentials.Certificate(str(REPO_ROOT / path))
    elif json_blob:
        cred = credentials.Certificate(json.loads(json_blob))
    else:
        raise RuntimeError("Need FIREBASE_SERVICE_ACCOUNT_PATH or _JSON in .env")

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    custom_token = auth.create_custom_token(DEMO_UID).decode("utf-8")

    # Exchange custom token -> ID token via Identity Toolkit REST API.
    url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
        f"?key={API_KEY}"
    )
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json={"token": custom_token, "returnSecureToken": True})
    r.raise_for_status()
    return r.json()["idToken"]


def call_search(token: str | None) -> dict:
    headers = {"Accept-Encoding": "identity"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=60.0, headers=headers) as client:
        r = client.get(
            f"{GATEWAY}/api/v1/search",
            params={
                "destination": "Istanbul",
                "check_in": "2026-07-15",
                "check_out": "2026-07-18",
                "guests": 2,
            },
        )
    r.raise_for_status()
    return decode(r)


def main() -> int:
    print("[verify-discount] minting demo ID token...")
    id_token = mint_id_token()
    print(f"[verify-discount] got ID token (len={len(id_token)})")
    print()

    print("[verify-discount] calling /api/v1/search (anonymous)...")
    anon = call_search(None)
    print("[verify-discount] calling /api/v1/search (with Bearer token)...")
    auth = call_search(id_token)
    print()

    if anon.get("total") == 0:
        print("[verify-discount] no hotels in seed -- aborting")
        return 1

    # Match rooms by (hotel_id, room_id) -- response order is not guaranteed
    # to be the same between anon and auth calls.
    auth_index: dict[tuple[str, str], dict] = {
        (h["hotel_id"], r["room_id"]): r
        for h in auth["items"]
        for r in h["available_rooms"]
    }
    rows = []
    for a_h in anon["items"]:
        for a_r in a_h["available_rooms"]:
            key = (a_h["hotel_id"], a_r["room_id"])
            b_r = auth_index.get(key)
            if b_r is None:
                continue
            rows.append(
                {
                    "hotel": a_h["name"],
                    "room": a_r["room_type"],
                    "anon_price": Decimal(a_r["price_per_night"]),
                    "anon_orig": Decimal(a_r["original_price"]),
                    "anon_flag": a_r["discount_applied"],
                    "auth_price": Decimal(b_r["price_per_night"]),
                    "auth_orig": Decimal(b_r["original_price"]),
                    "auth_flag": b_r["discount_applied"],
                }
            )

    print(f"{'Hotel':30} {'Room':20} {'Anon':>10} {'Auth':>10} {'Ratio':>10} {'Auth flag':>12}")
    print("-" * 100)
    all_ok = True
    for r in rows:
        ratio = (r["auth_price"] / r["anon_price"]) if r["anon_price"] else Decimal("0")
        ok = abs(ratio - Decimal("0.85")) < Decimal("0.01") and r["auth_flag"] is True and r["anon_flag"] is False
        marker = "OK" if ok else "FAIL"
        all_ok = all_ok and ok
        print(
            f"{r['hotel']:30} {r['room']:20} "
            f"${r['anon_price']:>8} ${r['auth_price']:>8}  "
            f"{ratio:>9.4f}   {str(r['auth_flag']):>10}  [{marker}]"
        )

    print()
    if all_ok:
        print("[verify-discount] PASS -- discount is exactly 15% for every room")
        return 0
    print("[verify-discount] FAIL -- one or more rooms did NOT receive the 15% discount")
    return 1


if __name__ == "__main__":
    sys.exit(main())
