"""End-to-end smoke test against the running gateway.

Covers the *unauthenticated* golden path:
  1. Gateway health
  2. Anonymous search by destination
  3. Hotel detail
  4. Public comments list + rating distribution
  5. Agent chat (LLM tool-call loop)

Auth-gated paths (booking create, admin CRUD, comment POST) are NOT exercised here
because they need a real Firebase JWT — those are verified manually through the
frontend at http://localhost:5173.

Run from repo root after `scripts\\run_all_services.ps1`:
    python scripts/smoke_test_gateway.py

Exits 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

import sys
import time
import uuid

import httpx

GATEWAY = "http://127.0.0.1:8080"
TIMEOUT = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"


def _print(tag: str, name: str, detail: str = "") -> None:
    line = f"{tag} {name}"
    if detail:
        line += f" -- {detail}"
    print(line, flush=True)


def main() -> int:
    failures: list[str] = []
    client = httpx.Client(base_url=GATEWAY, timeout=TIMEOUT)

    # ---- 1. Gateway health ----
    name = "gateway /health"
    try:
        r = client.get("/health")
        r.raise_for_status()
        body = r.json()
        assert body.get("status") == "ok", body
        _print(PASS, name, body.get("service", ""))
    except Exception as exc:  # noqa: BLE001
        _print(FAIL, name, str(exc))
        failures.append(name)
        # If gateway is dead, nothing else will work
        print("\nGateway not reachable -- aborting.", file=sys.stderr)
        return 1

    # ---- 2. Anonymous search ----
    name = "GET /api/v1/search?destination=Rome"
    hotel_id: str | None = None
    try:
        r = client.get(
            "/api/v1/search",
            params={
                "destination": "Rome",
                "check_in": "2026-07-01",
                "check_out": "2026-07-03",
                "guests": 2,
            },
        )
        r.raise_for_status()
        body = r.json()
        total = body.get("total", 0)
        items = body.get("items", [])
        if items:
            hotel_id = items[0].get("hotel_id")
        _print(PASS, name, f"total={total} returned={len(items)}")
    except Exception as exc:  # noqa: BLE001
        _print(FAIL, name, str(exc))
        failures.append(name)

    # ---- 3. Hotel detail ----
    if hotel_id:
        name = f"GET /api/v1/search/hotels/{hotel_id[:8]}..."
        try:
            r = client.get(f"/api/v1/search/hotels/{hotel_id}")
            r.raise_for_status()
            body = r.json()
            _print(PASS, name, f"name={body.get('name')}")
        except Exception as exc:  # noqa: BLE001
            _print(FAIL, name, str(exc))
            failures.append(name)

        # ---- 4. Comments + distribution ----
        for path in [
            f"/api/v1/comments/hotels/{hotel_id}",
            f"/api/v1/comments/hotels/{hotel_id}/distribution",
        ]:
            short = path.replace(hotel_id, hotel_id[:8] + "...")
            name = f"GET {short}"
            try:
                r = client.get(path)
                r.raise_for_status()
                _print(PASS, name)
            except Exception as exc:  # noqa: BLE001
                _print(FAIL, name, str(exc))
                failures.append(name)
    else:
        _print(INFO, "Hotel detail + comments skipped -- no hotels in search result")

    # ---- 5. Agent chat ----
    name = "POST /api/v1/agent/chat"
    try:
        r = client.post(
            "/api/v1/agent/chat",
            json={
                "message": "Find me a hotel in Rome for 2 guests on 2026-07-01 to 2026-07-03",
                "session_id": str(uuid.uuid4()),
            },
            timeout=httpx.Timeout(60.0),
        )
        r.raise_for_status()
        body = r.json()
        reply = body.get("response", "")
        _print(PASS, name, f"len={len(reply)} -- {reply[:80]}...")
    except Exception as exc:  # noqa: BLE001
        _print(FAIL, name, str(exc))
        failures.append(name)

    # ---- Summary ----
    print()
    if failures:
        print(f"{FAIL} {len(failures)} check(s) failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"{PASS} All unauthenticated golden-path checks passed.")
    print("Manual verification still required for: login, booking create, comment post, admin CRUD.")
    return 0


if __name__ == "__main__":
    # Give services a moment if launched right before.
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        time.sleep(3)
    sys.exit(main())
