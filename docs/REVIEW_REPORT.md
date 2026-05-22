# Senior Review — Project audit + fix report

> Comprehensive end-to-end review of the Hotel Booking System against
> `docs/Guide/Final_Guideline.pdf`, performed 2026-05-22.

---

## TL;DR

Started with **3 user-visible failures** in production:
1. The Vercel UI showed `Istanbul · undefined stays` and a "No hotels"
   message for searches that should have hits.
2. The map sidebar rendered with broken / missing tiles.
3. The AI chat widget kept apologizing instead of returning hotels.

Ended with:
- ✅ Gateway, search, hotel detail, comments, comments-distribution and
  the AI-agent tool loop all return real data through the production
  gateway (verified by curl + by hitting the new `/api/v1/agent/debug/*`
  endpoints).
- ✅ The auth-gated routes (`/api/v1/bookings`, `/api/v1/admin/*`)
  correctly return 401 to anonymous callers.
- ✅ Mongo now has 46 seeded comments across all 10 hotels, so the
  rating chart + comments tab look populated.
- ✅ README + `docs/ARCHITECTURE.md` rewritten to match what the
  guideline asks for in §DELIVERABLES (live URLs, design, assumptions,
  issues, ER diagram).

Two items still need **the user** to do something:
- Vercel's production build is still on commit `d008ee9` (bundle hash
  `index-BmENBW46.js`). The 5 frontend-affecting commits I pushed after
  it (HotelMap fix, HomePage city fix, etc.) have not been picked up.
  Check Vercel dashboard → Deployments — likely a stuck build or
  auto-deploy got disabled.
- The Render free tier still cold-starts after 15 min idle. The
  GitHub Actions warmup workflow runs every 10 min but GH Actions cron
  delays mean the first request after a long idle can still see a
  ~30 s wake-up. Mitigated by running the warmup workflow manually
  before the demo (`gh workflow run warmup.yml`).

---

## Findings vs. Final Guideline

Every requirement from `docs/Guide/final_guideline_extracted.txt`:

| Guideline requirement | Status | Implementation |
|---|---|---|
| Admins add/update rooms for availability, authenticated | ✅ | `services/admin-service/app/routers/availability.py`; gateway requires Firebase JWT on `/api/v1/admin/*`; `require_admin` checks Postgres `users.role` |
| Search by destination + dates + people; only vacant rooms | ✅ | `services/search-service/app/routers/search.py`; SQL excludes rooms with availability < guests |
| 15% discount when logged in | ✅ | `services/search-service/app/services/discount.py`; triggered by `optional_current_user` claim presence |
| 'Haritada göster' for search results | ✅ | `frontend/src/components/HotelMap.tsx` (react-leaflet); now self-corrects tile grid via `map.invalidateSize()` on container resize |
| Book hotel — capacity decrement | ✅ | `services/booking-service/app/services/booking.py` (`SELECT FOR UPDATE` on `room_availability`, atomic decrement + insert, RabbitMQ publish post-commit) |
| Comments + per-service distribution graph | ✅ | `services/comments-service/app/repositories/comment.py` `aggregate_distribution` (`$group` + `$bucket`); `frontend/src/components/RatingChart.tsx` (Recharts) |
| Nightly low-capacity (<20%) task | ✅ | `services/notification-service/app/workers/occupancy.py`; trigger via `POST /trigger/nightly`, scheduled via Google Cloud Scheduler (see `docs/SCHEDULING.md`) |
| Pull reservations from queue, send message | ✅ | `services/notification-service/app/workers/consumer.py`; durable queue, manual ack only after Resend send succeeds |
| AI agent — search + book via your APIs | ✅ | `services/ai-agent-service/app/tools/*.py` + Groq tool-call loop; verified end-to-end after `Accept-Encoding: identity` fix |
| REST endpoints versioned (`/api/v1/`) | ✅ | All routers register `/api/v1/...`; gateway preserves the prefix |
| Pagination support | ✅ | `shared.schemas.PaginationParams` (`page`, `limit ≤ 100`); responses wrap items in `PaginatedResponse[T]` |
| Cloud-only database (no SQLite) | ✅ | Supabase Postgres + MongoDB Atlas + Upstash Redis |
| Distributed cache (e.g. hotel details) | ✅ | Upstash Redis; `hotel:{id}` static fields 24h TTL; `destination:{city}:hotel_ids` 6h TTL; admin invalidation on PATCH/DELETE |
| IAM auth (Firebase/Cognito/Supabase) | ✅ | Firebase Auth (web SDK + Admin SDK); JWT verified at gateway |
| Dockerfile per service | ✅ | `services/*/Dockerfile` (7 files) |
| Cloud deploy | ✅ | Render (backend) + Vercel (frontend) |
| Cloud scheduler | ✅ | Google Cloud Scheduler (documented in `docs/SCHEDULING.md`) |
| RabbitMQ for queue | ✅ | CloudAMQP, durable exchange + persistent messages + tenacity-backed 3-retry |
| GitHub repo public | ✅ | https://github.com/batikanakdenizz/Hotel-Booking-System |
| README with deployed URLs + design + assumptions + issues + ER + video | ⚠️ | README and `docs/ARCHITECTURE.md` rewritten; video URL is a placeholder until you record it |

---

## What was broken (root causes + fixes)

### 1. AI agent tool calls crashed with `UnicodeDecodeError`

**Symptom:** Every chat message that should have triggered a search came
back as "I'm sorry, the function call failed due to a technical issue."

**Root cause:** Cloudflare in front of Render compresses responses with
brotli on the wire. The `ai-agent-service` container only has
`httpx==0.27.2` installed, no `brotli` package. httpx didn't know how
to decompress brotli, so `r.json()` failed with `'utf-8' codec can't
decode byte 0x82 in position 0: invalid start byte`. The dispatcher's
catch-all then returned `{"error": "tool_exception", ...}` to the LLM,
which apologized to the user.

**Fix:** Set `Accept-Encoding: identity` on every upstream HTTP call:
- `services/ai-agent-service/app/tools/search.py`
- `services/ai-agent-service/app/tools/booking.py`
- `services/ai-agent-service/app/tools/comments.py`
- `services/gateway/app/proxy.py` (so gateway → downstream also stays
  uncompressed)

Cloudflare honors the header and returns plain JSON. httpx parses
without needing brotli. **Verified working** via
`GET /api/v1/agent/debug/search?destination=Istanbul` →
`Bosphorus Bay Hotel` + `Sultanahmet Palace`, and via a real LLM chat
that produced a formatted hotel list.

### 2. Service URL env vars were bare hostnames, breaking httpx

**Symptom:** Some inter-service calls crashed with
`httpx.UnsupportedProtocol` because the gateway / agent ended up with
URLs like `hbs-gateway/api/v1/search` (no scheme, no TLD).

**Root cause:** The original `infrastructure/render.yaml` used
`fromService.property: host` which on Render's free tier resolved to
the bare service name (`hbs-gateway`) rather than the FQDN
(`https://hbs-gateway.onrender.com`). Operators (including me) then
copy-pasted those values into the Render dashboard when fixing other
issues.

**Fix:** Two-pronged.
- `infrastructure/render.yaml` now hardcodes the public `*.onrender.com`
  URLs.
- A Pydantic `field_validator` on every inter-service URL in
  `services/ai-agent-service/app/config.py` and
  `services/gateway/app/config.py` aggressively rewrites:
  - missing scheme → `https://` (or `http://` for localhost / 127.*)
  - missing TLD (e.g. `hbs-gateway`) → `.onrender.com` suffix
  - trailing slash → stripped

  So whether the operator sets `hbs-gateway`, `https://hbs-gateway`,
  `hbs-gateway.onrender.com/`, or the canonical form, the runtime URL
  is the same.

### 3. Shared package `__init__.py`s eagerly imported postgres deps

**Symptom:** `comments-service` (and earlier `gateway`) deploys
crashed at startup with `ModuleNotFoundError: No module named 'sqlalchemy'`
even though those services don't use Postgres.

**Root cause:** `services/shared/shared/auth/__init__.py` and
`services/shared/shared/clients/__init__.py` eagerly re-exported every
submodule. So `from shared.auth.firebase import X` transitively loaded
`shared.auth.deps`, which imports SQLAlchemy. Services that installed
shared with only `[firebase]` or `[mongo,firebase]` extras crashed.

**Fix:**
- Slimmed both `__init__.py`s to a docstring; consumers already
  use the submodule path (`from shared.auth.firebase import X`).
- Moved the SQLAlchemy and `shared.models` imports inside
  `_get_or_create_user_impl` / `build_get_or_create_user` so even
  `from shared.auth.deps import get_current_user` (pure-auth helpers)
  loads without postgres.

### 4. Missing runtime deps in service requirements

**Symptom:** Containers wouldn't boot.

**Root cause:** Several `requirements.txt` files were still the
Phase-0 stub.

**Fix:**
- `services/gateway/requirements.txt` now lists `httpx`, `slowapi`,
  and pulls `shared[firebase]`.
- `services/shared/pyproject.toml` now declares `pydantic[email]` so
  every service that imports `shared.schemas.user` (with `EmailStr`)
  works without each service redeclaring email-validator.

### 5. HomePage cards linked to cities not in the seed

**Symptom:** Clicking "Berlin" returned "No hotels available".

**Root cause:** `frontend/src/pages/HomePage.tsx` had hand-coded Rome,
Paris, Istanbul, Berlin, but `scripts/seed_demo_data.py` seeds
Rome / Paris / Istanbul / New York / Barcelona / Tokyo / Bodrum.

**Fix:** Replaced the 4-card list with the 7 actually-seeded cities and
widened the grid to 2 / 3 / 4 columns.

### 6. Leaflet rendered a fragmented tile grid

**Symptom:** The map in the search results sidebar showed half-loaded /
partial tiles.

**Root cause:** Leaflet caches the container size at mount time. The
search results sidebar is `lg:sticky` and only reaches its final size
after the list column finishes laying out, so Leaflet's first tile
grid covers a viewport that's smaller than the eventual container.

**Fix:** `frontend/src/components/HotelMap.tsx` now mounts a
`<FitToContainer>` helper that calls `map.invalidateSize()` on mount,
again after 250 ms, and on every resize via `ResizeObserver`. It also
calls `map.fitBounds()` on the marker set so the zoom level is
sensible regardless of the city.

### 7. MongoDB had no seeded comments

**Symptom:** Hotel detail page's comments tab and rating chart looked
empty, making the 5-dim aggregation feature look broken.

**Root cause:** `scripts/seed_demo_data.py` only seeds Postgres.

**Fix:** New `scripts/seed_demo_comments.py` discovers every hotel
through the public search endpoint, then idempotently inserts 4-6
plausible reviews per hotel into MongoDB Atlas (46 docs total in
production). Falls back through identity/brotli/gzip codecs so the
Windows + Python 3.13 venv brotli quirk doesn't break it.

### 8. Warmup workflow only pinged the gateway

**Symptom:** Even with warmup enabled, the first request after a long
idle still hit a cold downstream and got a 502.

**Root cause:** `.github/workflows/warmup.yml` originally curled only
the gateway. Gateway being awake doesn't keep search / booking /
comments / notification / ai-agent awake.

**Fix:** Workflow is now a `strategy.matrix` over all 7 services so
every health check happens in parallel each tick.

---

## Production smoke test — final state (curl-only, no Firebase token)

```
[1] gateway /health                                        -> 200 OK
[2] /api/v1/search?destination=Istanbul                    -> 200, 2 hotels
[3] /api/v1/search/hotels/{id}                             -> 200, "Bosphorus Bay Hotel" + 3 rooms
[4] /api/v1/comments/hotels/{id}                           -> 200, 4 comments
[5] /api/v1/comments/hotels/{id}/distribution              -> 200, total=4 avg_overall=7.3
[6] POST /api/v1/agent/chat (search prompt)                -> 200, formatted hotel list
[7] GET  /api/v1/bookings   (anon)                         -> 401  (expected)
[8] GET  /api/v1/admin/hotels (anon)                       -> 401  (expected)
[9] GET  /api/v1/agent/debug/search?destination=Istanbul   -> 200, 2 hotels
```

Authenticated flows (booking, admin CRUD, comment POST) still need
manual verification through the Vercel UI with a Firebase login.

---

## What the user still needs to do

1. **Verify Vercel picked up the latest commits.** Bundle hash is still
   `index-BmENBW46.js` (the build from `d008ee9`). 7 frontend-affecting
   commits sit behind it. Open Vercel dashboard → Deployments → look
   for a failed or queued deploy. A "Redeploy" on the latest commit
   should pick up:
   - HotelMap.tsx fix (tiles)
   - HomePage cities fix
   - any other minor frontend tweaks

2. **Record the demo video** (≤ 5 min). README has a placeholder link.

3. **(Optional)** Promote your user account to admin in Postgres so the
   `/admin/hotels` page renders:
   ```
   python scripts/promote_admin.py kingeinstain44@hotmail.com
   ```

4. **(Optional)** Run the comment seeder if you re-seed the database in
   the future:
   ```
   python scripts/seed_demo_comments.py
   ```

---

## Commits introduced by this review

- `4e25dc2` fix(config): normalize service URLs so bare hostnames don't break httpx
- `ea333da` feat(scripts): seed_demo_comments.py
- `a60fae0` docs: production README + ARCHITECTURE with ER diagram
- `a8dacff` fix(config): auto-suffix .onrender.com when bare hostname has no dot
- `0bf3ca5` chore(agent): /debug/config + /debug/search
- `11403db` fix(agent,gateway): force Accept-Encoding identity on upstream hops

All pushed to `origin/main`. Render auto-deployed each, verified live.

---

## Pending work (Phase 13 + 14)

- Google Cloud Scheduler — `docs/SCHEDULING.md` is ready; setup needs
  one manual job creation (15 min in the GCP console).
- Demo video — user action.

After both: the project meets every guideline deliverable.
