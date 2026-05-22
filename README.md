# Hotel Booking System

A microservice-based hotel booking platform built for
**SE 4458 — Software Architecture & Design of Modern Large Scale Systems — Final Project, Group 1**.

[![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React-blue)]()
[![Auth](https://img.shields.io/badge/auth-Firebase-orange)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 🌐 Live Deployment

| Layer | URL |
|---|---|
| **Frontend (Vercel)** | https://hotel-booking-system-psi-beryl.vercel.app |
| **API Gateway (Render)** | https://hbs-gateway.onrender.com |
| **Source (GitHub)** | https://github.com/batikanakdenizz/Hotel-Booking-System |
| **Demo video (5 min)** | _link added after recording_ |

> Backend runs on Render's free tier — services sleep after 15 min of idle. A
> `render-warmup` GitHub Action pings every service every 10 min until
> 2026-05-29 so the first click during the grading window responds instantly.
> After that date services go back to sleeping; the first request takes
> ~30 s to wake.

---

## 🧭 Architecture

Seven backend microservices + a React/Vite frontend + an AI chat agent, all
reachable through a single API gateway.

```
                          Browser
                             │
                             ▼
      ┌──────────────────────────────────────────────┐
      │  Vercel (React SPA + CDN)                    │
      └──────────────────────────────────────────────┘
                             │ HTTPS + Firebase JWT
                             ▼
      ┌──────────────────────────────────────────────┐
      │  Gateway  (FastAPI · auth · rate-limit · CORS) │
      └──────────────────────────────────────────────┘
        │           │           │             │
        ▼           ▼           ▼             ▼
   admin       search      booking       comments
   (Postgres)  (Postgres   (Postgres   (MongoDB Atlas)
              + Redis)    + RabbitMQ)
        │           │           │             │
        ▼           ▼           ▼             ▼
                       ai-agent  ←── Groq (Llama 3.3 70B)
                                     via OpenAI-compatible API
                       notification ──→ Resend (email)
                            ▲
                            │ POST /trigger/nightly
                       Google Cloud Scheduler
```

Detailed component diagram + design decisions: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## 🛠️ Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI 0.115 · SQLAlchemy 2 async · Pydantic v2 |
| Frontend | Vite · React 19 · TypeScript · Tailwind 3 · TanStack Query · react-leaflet · Recharts |
| Auth | **Firebase Authentication** (email/password + Google) |
| Databases | **Supabase Postgres** · **MongoDB Atlas** · **Upstash Redis** |
| Queue | **CloudAMQP RabbitMQ** (durable + persistent + retry) |
| AI | **Groq** Llama 3.3 70B via OpenAI-compatible API |
| Email | **Resend** |
| Hosting | **Render** (7 Docker services) · **Vercel** (frontend) |
| Scheduling | **Google Cloud Scheduler** + GitHub Actions warmup |

---

## 🧩 Services

| Service | Port (local) | Responsibility |
|---|---|---|
| `gateway` | 8080 | Single entry point, Firebase JWT verification, rate-limit (60/min/IP), CORS, httpx reverse proxy |
| `admin-service` | 8001 | Hotel + Room + RoomAvailability CRUD, cache invalidation, admin-role gate |
| `search-service` | 8002 | Date-range availability query, hotel-detail Redis cache, 15% logged-in discount |
| `booking-service` | 8003 | Transactional booking under `SELECT FOR UPDATE` + durable RabbitMQ publish |
| `comments-service` | 8004 | MongoDB comments + 5-dimensional rating aggregation (`$group` + `$bucket`) |
| `notification-service` | 8005 | RabbitMQ consumer for reservation events + nightly low-capacity check via Cloud Scheduler |
| `ai-agent-service` | 8006 | Chat endpoint, Groq tool-call loop (search_hotels, book_hotel, get_hotel_comments) |

All 7 services have a `Dockerfile`. Build them with the `infrastructure/render.yaml`
Blueprint (one-click deploy on Render).

---

## ✅ Guideline compliance

Final guideline excerpts (from `docs/Guide/Final_Guideline.pdf`) mapped to where
they live in this codebase:

| Requirement | Where |
|---|---|
| Admins can add/update rooms for availability between dates — authenticated | `services/admin-service/app/routers/{hotels,rooms,availability}.py`; gateway requires Firebase JWT on `/api/v1/admin/*`; `users.role` check in `app/deps.py` |
| Search by destination + dates + guests; only vacant rooms; "Haritada göster" | `services/search-service/app/routers/search.py`; `frontend/src/components/HotelMap.tsx` (Leaflet) |
| 15% member discount when logged in | `services/search-service/app/services/discount.py` triggered by `optional_current_user` |
| Book hotel — capacity decrement | `services/booking-service/app/services/booking.py` (single async transaction, `SELECT FOR UPDATE`) |
| Comments + distribution graph | `services/comments-service/app/repositories/comment.py` (`aggregate_distribution`); `frontend/src/components/RatingChart.tsx` (Recharts) |
| Nightly low-availability check (< 20% next month) | `services/notification-service/app/workers/occupancy.py`; trigger via `POST /trigger/nightly` (Cloud Scheduler, see [`docs/SCHEDULING.md`](docs/SCHEDULING.md)) |
| Notification consumer pulling reservations from the queue | `services/notification-service/app/workers/consumer.py` |
| AI agent uses your APIs to search + book | `services/ai-agent-service/app/tools/{search,booking,comments}.py` + Groq tool-call loop |
| REST + versioning + pagination | All endpoints mounted under `/api/v1/`; pagination via `shared.schemas.PaginationParams` (`page`, `limit`) |
| Cloud database (SQLite NOT allowed) | Supabase Postgres (relational), MongoDB Atlas (comments), Upstash Redis (cache) |
| Distributed cache (e.g. hotel details) | Upstash Redis caches `hotel:{id}` for 24 h; `destination:{name}:hotel_ids` index for 6 h |
| Firebase / Cognito / Supabase Auth — **no local auth** | Firebase Auth (web SDK + Admin SDK) |
| Each service has a Dockerfile | `services/*/Dockerfile` (7 files) |
| Deployed on a cloud provider | Render (backend) + Vercel (frontend) |
| Cloud-based scheduler | Google Cloud Scheduler ([`docs/SCHEDULING.md`](docs/SCHEDULING.md)) |
| RabbitMQ for queue | CloudAMQP, durable exchange `reservations-exchange`, queue `q.reservations.notifications` |

---

## 🗂️ Data models

See [`docs/ARCHITECTURE.md#er-diagram`](docs/ARCHITECTURE.md) for the full ER diagram.
Quick summary (one row per table):

- **Postgres**
  - `users`: `id, firebase_uid, email, display_name, role, created_at`
  - `hotels`: `id, name, description, destination, address, latitude, longitude, admin_email, star_rating, amenities, image_url, …`
  - `rooms`: `id, hotel_id → hotels, room_type, capacity, base_price_per_night, total_rooms`
  - `room_availability`: `id, room_id → rooms, date, available_count` (UNIQUE on (room_id, date))
  - `bookings`: `id, user_id → users, hotel_id, room_id, check_in, check_out, guests, total_price, status, idempotency_key`
- **MongoDB** (`comments` collection)
  - `{ _id, hotel_id, user_id, user_display_name, text, ratings: {cleanliness, staff, amenities, comfort, eco_friendliness}, overall_rating, created_at, deleted_at }`

---

## 📐 Design highlights & assumptions

Full write-up: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Key choices:

1. **Single API gateway, no client-to-microservice fan-out.** The browser never
   sees more than one host. Auth, rate-limit, and CORS are centralized.
2. **Cache hotel _details_, not search _results_.** Per guideline ("hotel
   details"). `hotel:{id}` static fields live in Redis with a 24 h TTL.
   `room_availability` is never cached — booking would race the cache.
3. **Dual-write reliability.** `booking-service` commits Postgres first,
   then publishes to a durable exchange with `delivery_mode=2` and 3-retry
   exponential backoff. Notification-service consumes with manual ack only
   after the email is dispatched.
4. **Pooler-safe asyncpg.** Supabase's transaction pooler reuses backend
   sessions, so prepared statement names must be unique per query
   (`prepared_statement_name_func` with UUIDs) and the cache must be off
   (`statement_cache_size=0`). Without this we'd see
   `DuplicatePreparedStatementError` under load.
5. **5-dimension ratings (cleanliness / staff / amenities / comfort / eco)**
   matching the PDF mockup, aggregated with a single MongoDB `$group` plus a
   `$bucket` histogram for the chart.
6. **Auth model.** Firebase verifies the JWT at the gateway, downstream
   services trust the forwarded `X-User-Id` header. Authorization
   (`users.role = 'hotel_admin'`) lives in Postgres so we can promote users
   without touching Firebase.

---

## 🚧 Issues encountered

Recorded so the next reviewer has the same context:

- **Supabase pooler + asyncpg prepared-statement collisions** → fixed with
  `prepared_statement_name_func` + `statement_cache_size=0`.
- **Render Blueprint `fromService.host` returned bare service names**, not
  FQDNs. Worked around by hardcoding `https://<name>.onrender.com` in
  `infrastructure/render.yaml` and adding a defensive Pydantic
  `field_validator` so even an operator typo cannot reach httpx.
- **Eager `__init__.py` re-exports forced SQLAlchemy onto every importer**.
  Slimmed `shared.auth/__init__.py` and `shared.clients/__init__.py` so a
  service that only needs Mongo doesn't drag in postgres deps. SQLAlchemy
  imports inside `shared.auth.deps` were moved to function scope.
- **Cold-start UX on Render free tier**. Mitigated with a GitHub Actions
  matrix that hits every service's `/health` every 10 min during the demo
  window. See [`docs/SCHEDULING.md`](docs/SCHEDULING.md).
- **Leaflet tile grid fragmenting** when the map mounts inside a
  sticky sidebar. Fixed with a `useEffect` that calls `map.invalidateSize()`
  on mount and on every container resize.

---

## 💻 Local development

```bash
# 1. Clone + create .env (copy .env.example then fill in real values)
git clone https://github.com/batikanakdenizz/Hotel-Booking-System.git
cd Hotel-Booking-System
cp .env.example .env

# 2. Python venv + deps
python -m venv .venv
.venv\Scripts\activate    # (PowerShell)
pip install -r services/admin-service/requirements.txt        # any service pulls in shared
pip install -r scripts/requirements.txt                       # for seeding scripts

# 3. Start every backend service (Windows PowerShell launcher pops 7 windows)
.\scripts\run_all_services.ps1

# 4. Smoke test
python scripts/smoke_test_gateway.py

# 5. Frontend
cd frontend
npm install
npm run dev    # http://localhost:5173
```

See [`docs/DEPLOY.md`](docs/DEPLOY.md) for production deployment steps.

---

## 🧪 Smoke test

```bash
# Unauthenticated golden path (search, hotel detail, comments, AI agent)
python scripts/smoke_test_gateway.py
```

Authenticated paths (booking create, admin CRUD, comment POST) are verified
manually through the frontend with a real Firebase login.

---

## 📜 License

MIT — see [`LICENSE`](LICENSE) (or use the file mentioned in the badge).
