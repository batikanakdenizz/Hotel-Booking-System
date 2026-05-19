# Hotel Booking System — Full Project Plan

**Course:** SE 4458 Software Architecture & Design of Modern Large Scale Systems
**Assignment:** Final Project — Group 1 (Hotel Booking System)
**Student:** Batikan Akdeniz
**Plan version:** 1.0
**Last updated:** 2026-05-17

---

## Table of Contents

1. [Project Vision & Scope](#1-project-vision--scope)
2. [Locked Tech Stack Decisions](#2-locked-tech-stack-decisions)
3. [System Architecture](#3-system-architecture)
4. [Services Catalog](#4-services-catalog)
5. [Data Models](#5-data-models)
6. [API Specifications](#6-api-specifications)
7. [Repository Structure](#7-repository-structure)
8. [External Services — Manual Setup Steps](#8-external-services--manual-setup-steps)
9. [Local Development Environment](#9-local-development-environment)
10. [Implementation Phases (Day-by-Day)](#10-implementation-phases-day-by-day)
11. [Environment Variables Reference](#11-environment-variables-reference)
12. [Deployment Plan](#12-deployment-plan)
13. [Scheduled Tasks Setup](#13-scheduled-tasks-setup)
14. [Testing Strategy](#14-testing-strategy)
15. [Risk Register & Mitigations](#15-risk-register--mitigations)
16. [Demo & Video Preparation](#16-demo--video-preparation)
17. [Deliverables Checklist](#17-deliverables-checklist)
18. [Time Estimate](#18-time-estimate)

---

## 1. Project Vision & Scope

Build a microservice-based hotel booking platform implementing all 6 use cases from the SE 4458 Group 1 Final guideline:

- **Hotel Admin Service** — authenticated CRUD for hotels and room availability
- **Hotel Search Service** — destination + date + people search with 15% discount for logged-in users
- **Book Hotel Service** — booking with capacity decrease, publishes event to queue
- **Hotel Comments Service** — comments with 5-dimensional rating distribution (matches the PDF mockup: cleanliness, staff, amenities, comfort, eco-friendliness)
- **Notification Service** — nightly low-capacity alert + reservation confirmation consumer
- **AI Agent Service** — chat-based hotel search and booking using MCP tools

**Non-functional requirements satisfied:**

- Distributed cache for hotel details (Upstash Redis)
- Comments stored in NoSQL DB (MongoDB Atlas)
- Reservations published to message queue (RabbitMQ via CloudAMQP)
- External IAM (Firebase Authentication) — no local auth
- API Gateway as the single entry point
- REST APIs with versioning (`/api/v1/`) and pagination
- Per-service Dockerfile
- Cloud deployment (Render + Vercel)
- Nightly scheduled task (Google Cloud Scheduler)
- "Haritada göster" map view (Leaflet)
- Image upload — **deferred** (nice-to-have only)

**Total monthly cost:** $0 (all services on free tier).

---

## 2. Locked Tech Stack Decisions

### 2.1 Backend
| Component | Choice | Version | Reason |
|---|---|---|---|
| Language | Python | 3.12 | Async, AI ecosystem, mature SDKs for all dependencies |
| Web framework | FastAPI | 0.115+ | Auto-OpenAPI, Pydantic, async-native |
| ASGI server | Uvicorn | 0.32+ | Standard FastAPI runtime |
| Validation | Pydantic | v2 | Type-safe, fast, built into FastAPI |
| ORM | SQLAlchemy | 2.x async | Standard, supports async with asyncpg |
| Migration | Alembic | 1.13+ | Standard SQLAlchemy migration tool |
| Postgres driver | asyncpg | 0.30+ | Async, fastest Python Postgres driver |
| MongoDB driver | Motor | 3.6+ | Async MongoDB driver |
| Redis client | redis-py (asyncio) | 5.2+ | Standard, async-compatible |
| RabbitMQ client | aio-pika | 9.5+ | Async RabbitMQ, robust connection handling |
| Firebase Admin | firebase-admin | 6.6+ | Official Google SDK for JWT verify |
| HTTP client | httpx | 0.27+ | Async HTTP, used by gateway proxy and AI agent |
| Rate limiting | slowapi | 0.1.9+ | FastAPI-compatible rate limiter |
| Logging | structlog | 24.4+ | Structured JSON logs |

### 2.2 AI Agent
| Component | Choice | Reason |
|---|---|---|
| Protocol | Model Context Protocol (MCP) | 2025 Anthropic standard, portable tools |
| SDK | FastMCP (Python) | Decorator-based tool registration |
| Transport | stdio subprocess | Same container as agent, no separate deploy |
| LLM provider | Groq (primary) | Free tier, Llama 3.3 70B, low latency |
| LLM fallback | OpenAI GPT-4o-mini (optional) | If user adds OPENAI_API_KEY |
| Chat orchestration | Direct httpx → Groq API | Lightweight, no LangChain dependency in production |

### 2.3 Data Stores
| Store | Service | Free tier | Used by |
|---|---|---|---|
| Relational | Supabase Postgres | 500 MB | admin, search, booking, notification |
| Document | MongoDB Atlas M0 | 512 MB | comments |
| Cache | Upstash Redis | 10k cmd/day, 256 MB | search (hotel detail cache) |
| Queue | CloudAMQP Little Lemur | 1M msg/mo | booking → notification |

### 2.4 IAM & Identity
| Component | Choice | Free tier |
|---|---|---|
| IAM provider | Firebase Authentication | Unlimited |
| Frontend SDK | `firebase` JS package | Free |
| Backend verify | `firebase-admin` Python | Free |
| Token taxonomy | Bearer (ID token in `Authorization` header) | — |

### 2.5 Frontend
| Component | Choice | Reason |
|---|---|---|
| Build tool | Vite | Fast HMR, modern |
| Language | **TypeScript** | Type safety, portfolio signal, type-shared DTOs with backend OpenAPI |
| UI library | React 19 | Latest stable, Suspense + concurrent features |
| Component primitives | **shadcn/ui (Radix UI + Tailwind)** | Production-quality accessible components, customizable, modern industry standard |
| Styling | **Tailwind CSS v4** | Utility-first, fast iteration, dark-mode native |
| Animation | **Framer Motion** | Page/element transitions, card hover, modal motion — wow factor |
| Server state | **TanStack Query (react-query)** | Caching, auto-refetch, optimistic updates — modern React data-fetching standard |
| Routing | react-router-dom v6 | Stable, nested routes |
| HTTP | axios + JWT interceptor | Familiar, integrates with TanStack Query |
| Forms | **react-hook-form + zod** | Type-safe validation, performant, fewer re-renders |
| Date picker | **react-day-picker** | Date range native, accessible, themeable |
| Map | react-leaflet + OpenStreetMap | Free, no API key |
| Chart | Recharts | Lightweight, React-native, declarative |
| Icons | **lucide-react** | Clean SVG icon set, ~1000 icons |
| Auth SDK | firebase JS | Firebase Auth integration |
| Notifications | **sonner** (toast) | Modern toast library, shadcn-aligned |

### 2.5.1 Design principles
- **Visual reference:** Booking.com layout structure + Airbnb-inspired warm modern aesthetic.
- **Palette:** Primary `#003580` (deep blue) or `#ff5a5f` (Airbnb coral) — to be locked at scaffold time. Accent `#feba02` (warm yellow). Neutral gray scale (Tailwind `gray` or `zinc`).
- **Typography:** Inter or Manrope (variable font, modern hierarchy).
- **Spacing/radius:** Tailwind defaults (rounded-xl on cards, generous padding).
- **Mobile-first:** Every page must work on 375px width. Booking flow becomes a bottom sheet on mobile.
- **Loading states:** Skeleton components (shadcn `Skeleton`), never blank screens during fetches.
- **Empty states:** Friendly illustrations + CTA (e.g., "No bookings yet — start exploring →").
- **Error states:** Toast (sonner) for transient errors, inline messages for form errors.
- **Accessibility:** Radix UI primitives handle a11y; add ARIA labels on icons; keyboard navigation tested on chat widget and admin tables.

### 2.6 Infrastructure / DevOps
| Component | Choice | Free tier |
|---|---|---|
| Backend hosting | Render | 750h/svc/month, Docker |
| Frontend hosting | Vercel | 100 GB BW |
| Scheduler (nightly) | Google Cloud Scheduler | 3 jobs/month |
| Warmup pinger | cron-job.org | 50 jobs |
| SMTP / Email | Resend | 100 emails/day |
| CI | GitHub Actions | 2000 min/month |
| Container | Docker / Dockerfile (no image commit) | — |

---

## 3. System Architecture

### 3.1 High-level diagram

```
                   ┌─────────────────────────────────┐
                   │      React Frontend (Vercel)    │
                   │  • Login (Firebase)              │
                   │  • Search + Map (Leaflet)        │
                   │  • Hotel detail + Chart          │
                   │  • AI ChatWindow                 │
                   │  • Admin panel                   │
                   └─────────────────┬───────────────┘
                                     │ HTTPS + JWT
                                     ▼
                   ┌─────────────────────────────────┐
                   │   API Gateway (FastAPI)          │
                   │   Render                          │
                   │  • Route table (env-driven)      │
                   │  • Firebase JWT verify           │
                   │  • slowapi rate limit            │
                   │  • CORS                          │
                   │  • Request logging               │
                   └────┬──────┬──────┬──────┬──────┘
              ┌────────┘      │      │      │     └────────┐
              ▼               ▼      ▼      ▼              ▼
        ┌──────────┐   ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │  Admin   │   │  Search  │ │ Booking  │ │   Comments   │
        │  Service │   │  Service │ │  Service │ │   Service    │
        │ (Render) │   │ (Render) │ │ (Render) │ │   (Render)   │
        └────┬─────┘   └────┬─────┘ └────┬─────┘ └──────┬───────┘
             │              │              │             │
             │              ▼              │             ▼
             │      ┌──────────────┐       │       ┌──────────┐
             │      │   Upstash    │       │       │ MongoDB  │
             │      │    Redis     │       │       │  Atlas   │
             │      └──────────────┘       │       └──────────┘
             │                              │
             ▼                              ▼
       ┌──────────────────────────┐  ┌────────────┐
       │   Supabase Postgres       │  │ CloudAMQP   │
       │   • hotels                │  │ RabbitMQ    │
       │   • rooms                 │  │ reservations│
       │   • room_availability     │  │   queue     │
       │   • bookings              │  └─────┬──────┘
       │   • users                 │        │
       └──────────────────────────┘        │ consume
                                            ▼
                                  ┌───────────────────────┐
                                  │ Notification Service   │
                                  │ • RabbitMQ consumer    │
                                  │ • Nightly worker       │
                                  │ • Resend SMTP          │
                                  │ (Render)                │
                                  └─────────▲─────────────┘
                                            │ POST /trigger/nightly
                                            │
                                  ┌───────────────────────┐
                                  │ Google Cloud Scheduler │
                                  │ (daily 03:00 UTC)      │
                                  └───────────────────────┘

                          ╔════════════════════════════════════╗
                          ║   AI Agent Service (Render)         ║
                          ║   ┌──────────────────────────────┐  ║
                          ║   │ FastAPI /api/v1/agent/chat   │  ║
                          ║   └────────────┬─────────────────┘  ║
                          ║                │                    ║
                          ║                ▼ stdio subprocess   ║
                          ║   ┌──────────────────────────────┐  ║
                          ║   │ MCP Server (FastMCP)         │  ║
                          ║   │ Tools:                        │  ║
                          ║   │  • search_hotels             │  ║
                          ║   │  • book_hotel                │  ║
                          ║   │  • get_hotel_comments        │  ║
                          ║   └────────────┬─────────────────┘  ║
                          ║                │ httpx              ║
                          ║                ▼                    ║
                          ║   (gateway URL — same as frontend)  ║
                          ╚════════════════════════════════════╝
```

### 3.2 Authentication & authorization flow

**Identity (who):**
1. User opens frontend → Firebase Auth (email/password sign-up or login)
2. Firebase issues ID token (JWT)
3. Frontend stores token in memory, attaches `Authorization: Bearer <token>` to every API call
4. Gateway intercepts request → `firebase-admin.auth.verify_id_token(token)`
5. Gateway decodes UID, injects `X-User-Id` (Firebase UID) header to downstream service
6. Downstream service trusts gateway (services not exposed publicly, only via gateway)

**Authorization (what — admin role):**
- Postgres `users.role` is the **source of truth** for the admin role (`'user' | 'hotel_admin'`).
- On first sign-in, a `users` row is upserted with `role = 'user'` by default. (Handled by a shared FastAPI dependency `Depends(get_or_create_user)` that runs on any authenticated route — it creates the row if `firebase_uid` is new.)
- Admin promotion is **out-of-band**: a one-shot script `scripts/promote_admin.py <email>` updates `role = 'hotel_admin'`. Demo seed (`seed_demo_data.py`) auto-promotes `admin@hotelapp.com`.
- Admin-only endpoints (everything under `/api/v1/admin/*`) use a `Depends(require_admin)` dependency:
  ```python
  async def require_admin(
      claims = Depends(verify_firebase_token),
      db = Depends(get_db),
  ):
      user = await db.fetch_one(
          "SELECT id, role FROM users WHERE firebase_uid = :uid",
          {"uid": claims["uid"]},
      )
      if not user or user["role"] != "hotel_admin":
          raise HTTPException(403, "admin only")
      return user
  ```
- All admins are equal — there is no hotel-level ownership. Any `hotel_admin` can CRUD any hotel. This is intentional scope reduction for demo simplicity (multi-tenant ownership would be a future iteration).

### 3.3 Booking event flow (async, durable + retry)

1. User clicks "Book" on frontend
2. Frontend → `POST /api/v1/bookings` (with JWT)
3. Gateway verifies JWT → forwards to booking-service
4. Booking-service:
   a. Begins Postgres transaction (`SERIALIZABLE` or `REPEATABLE READ`)
   b. `SELECT ... FOR UPDATE` on `room_availability` rows for the date range
   c. Verifies `available_count > 0` for every date
   d. Decrements `available_count` for each date
   e. Inserts `bookings` record
   f. Commits transaction
5. **Reliable publish to RabbitMQ** (after DB commit):
   a. Topic exchange `reservations-exchange` declared with `durable=True` (survives broker restart)
   b. Queue `q.reservations.notifications` declared with `durable=True`
   c. Message published with `delivery_mode=PERSISTENT` (written to disk by broker) and routing key `reservation.created`
   d. Connection uses `aio_pika.connect_robust(...)` — automatic reconnect on transient drops
   e. **Publish-level retry policy:** 3 attempts with exponential backoff (1s, 2s, 4s); on terminal failure log `publish_failed_terminal` with `booking_id` (manual replay path)
6. Booking-service returns `201 Created` to the frontend (booking record is the source of truth; `notification_dispatched: bool` field reflects publish outcome)
7. Notification-service consumer:
   a. Connects with `connect_robust` to the **durable** queue
   b. `basic_consume` with `auto_ack=False`
   c. Receives message → sends "Reservation confirmed" email via Resend
   d. If email send fails → log warning, still write the in-app notification (failure isolation)
   e. On success → `basic_ack`
   f. On unhandled exception → `basic_nack(requeue=True)` (transient errors get retried by the broker)

**Known limitation (Dual-Write Problem, see PPT_SE4458_04 slides 26-31):** If booking-service crashes between the Postgres COMMIT and a successful publish (or all 3 retries fail), the booking exists in Postgres but no event is dispatched. The chosen mitigation (durable + persistent + retry) handles ~95% of transient failures but does not give exactly-once guarantees. Full solutions (Transactional Outbox or SAGA Choreography) are documented in the README "Issues encountered" section as the next iteration.

### 3.4 Nightly low-capacity check

1. Google Cloud Scheduler fires at 03:00 UTC daily
2. POST `https://notification-service.onrender.com/trigger/nightly` with API key in header
3. Notification-service:
   a. Validates API key
   b. Queries Postgres: for each hotel, compute occupancy % for next 30 days
   c. For hotels with `occupied / total > 0.80` (≥80% booked = <20% available)
   d. Sends email to `hotels.admin_email`
   e. Logs result

### 3.5 Hotel detail caching flow (cache-aside, guideline-compliant)

**What's cached:** Static hotel fields only — `id`, `name`, `description`, `destination`, `address`, `latitude`, `longitude`, `star_rating`, `amenities`, `image_url`, plus each room's `room_type`, `capacity`, `base_price_per_night`. **Never cached:** `available_count` (dynamic, changes every booking) and the post-discount price (per-request, depends on auth state).

**Why this shape:** The guideline explicitly states *"Hotel details will be stored in a separate distributed cache like Redis"* — not search results. Caching availability would cause two bugs: (a) stale availability after a booking (user sees a room they can no longer book), (b) discount cross-contamination if cache key omits auth state. Caching only the static detail eliminates both.

**Cache keys:**
- `hotel:{hotel_id}` → static hotel detail JSON (24h TTL)
- `destination:{name_lower}:hotel_ids` → list of hotel UUIDs for that destination (6h TTL, optional optimization)

**Search flow (`GET /api/v1/search?...`):**
1. Frontend → search-service via gateway with `destination`, `check_in`, `check_out`, `guests`, `page`, `limit`
2. **Resolve hotel IDs for destination** — try `redis.get("destination:rome:hotel_ids")`; on miss, query Postgres `SELECT id FROM hotels WHERE LOWER(destination)=LOWER(?) AND deleted_at IS NULL` and cache 6h
3. **Fresh availability query** — Postgres `rooms JOIN room_availability` filtered by `hotel_id IN (...)`, the date range `[check_in, check_out)`, `capacity >= guests`, and `available_count > 0` on every date in range. **Never cached** — this is the dynamic part
4. **Hydrate hotel detail per result** — for each unique `hotel_id`, `redis.get("hotel:{id}")`; on miss, `SELECT` from Postgres and `redis.set(..., ex=86400)`
5. **Compose response** — merge static detail (cached) + room availability (fresh) + `base_price_per_night`
6. **Apply discount at response-build time** — if request carries a valid JWT, `price = base_price * 0.85` and set `discount_applied: true`. The discounted value is **never written to cache**
7. Paginate, return

**Hotel detail endpoint (`GET /api/v1/search/hotels/{id}`):**
1. `redis.get("hotel:{id}")` → on hit, return cached payload (apply runtime discount if authenticated)
2. On miss, read from Postgres, cache 24h, return

**Cache invalidation (write-through trigger):**
- Admin `PUT /api/v1/admin/hotels/{id}` → admin-service does `redis.delete("hotel:{id}")` after the DB commit
- Admin `POST/DELETE /api/v1/admin/hotels` → admin-service deletes the relevant `destination:{name_lower}:hotel_ids` key
- Room/availability mutations (`PUT /api/v1/admin/rooms/{id}/availability`, booking commits) **do not touch the cache** — availability is never cached, so no invalidation is needed

**Why this is correct:**
- High hit rate — hotel list is small, repeatedly read
- Availability is always fresh — no "ghost availability" bug after bookings
- Discount logic decoupled from cache — no cross-user price leakage
- Admin updates propagate immediately via explicit `redis.delete`
- Literally matches the guideline non-functional requirement

---

## 4. Services Catalog

### 4.1 Gateway (`services/gateway/`)

**Responsibilities:** route forwarding, Firebase JWT verify, rate limiting (60 req/min/IP), CORS, request logging.

**Endpoints:** Proxies everything matching prefixes below.

| Prefix | Downstream | Auth |
|---|---|---|
| `/api/v1/admin/*` | admin-service | Required |
| `/api/v1/search/*` | search-service | Optional (token = 15% discount) |
| `/api/v1/bookings/*` | booking-service | Required |
| `/api/v1/comments/*` | comments-service | Required for POST/DELETE, optional for GET |
| `/api/v1/agent/*` | ai-agent-service | Optional (token = agent acts as user) |
| `/health` | local | Public |

**Tech:** FastAPI + httpx + slowapi + firebase-admin.

### 4.2 Admin Service (`services/admin-service/`)

**Responsibilities:** Hotel + Room CRUD, room availability management, **cache invalidation on hotel-level writes** (delete `hotel:{id}` and the relevant `destination:{name_lower}:hotel_ids` keys after DB commit).

**Endpoints:**
- `POST /api/v1/admin/hotels` — create hotel (lat, long, admin_email required)
- `GET /api/v1/admin/hotels` — list hotels with pagination
- `GET /api/v1/admin/hotels/{id}` — get hotel detail
- `PUT /api/v1/admin/hotels/{id}` — update hotel
- `DELETE /api/v1/admin/hotels/{id}` — soft delete
- `POST /api/v1/admin/hotels/{id}/rooms` — create room
- `GET /api/v1/admin/hotels/{id}/rooms` — list rooms with pagination
- `PUT /api/v1/admin/rooms/{id}/availability` — set/update availability for date range
- `GET /api/v1/admin/rooms/{id}/availability?from=…&to=…` — get availability

**Storage:** Supabase Postgres (`hotels`, `rooms`, `room_availability` tables).

### 4.3 Search Service (`services/search-service/`)

**Responsibilities:** Date-range availability query against Postgres (always fresh), hydrate static hotel detail from Redis (cache-aside on `hotel:{id}`), apply 15% discount at response-build time for authenticated callers, pagination. **Search-service never writes to the hotel-detail cache as a side effect of writes — only fills it on read miss; invalidation is owned by admin-service.**

**Endpoints:**
- `GET /api/v1/search?destination=&check_in=&check_out=&guests=&page=&limit=` — search hotels (availability fresh, static detail cached)
- `GET /api/v1/search/hotels/{id}` — hotel detail (cache-aside)

**Caching:** See §3.5. Cache stores **static hotel detail only** (`hotel:{id}`, 24h TTL) and optional destination → hotel-id lookup (`destination:{name}:hotel_ids`, 6h TTL). Availability and discounted prices are **never** cached.

**Storage:** Supabase Postgres (availability + cache-miss fallback) + Upstash Redis (hot hotel details).

### 4.4 Booking Service (`services/booking-service/`)

**Responsibilities:** Create booking with transactional capacity decrease, **reliably publish** `reservation.created` event (durable exchange + persistent message + exponential-backoff retry, see §3.3), idempotency key handling.

**Endpoints:**
- `POST /api/v1/bookings` — book a room for a date range
- `GET /api/v1/bookings` — list user's bookings (uses JWT UID)
- `GET /api/v1/bookings/{id}` — get booking detail
- `DELETE /api/v1/bookings/{id}` — cancel booking (capacity restore)

**Storage:** Supabase Postgres + RabbitMQ publish.

### 4.5 Comments Service (`services/comments-service/`)

**Responsibilities:** Comment CRUD with **5-dimensional ratings** (matches the PDF mockup: `cleanliness`, `staff`, `amenities`, `comfort`, `eco_friendliness`, each 1-10 scale as shown in the mockup), aggregation endpoint for the per-service distribution chart.

**Endpoints:**
- `POST /api/v1/comments` — add comment (auth required)
- `GET /api/v1/comments/hotels/{hotel_id}?page=&limit=` — list comments
- `GET /api/v1/comments/hotels/{hotel_id}/distribution` — rating distribution aggregation
- `DELETE /api/v1/comments/{id}` — delete own comment

**Storage:** MongoDB Atlas.

### 4.6 Notification Service (`services/notification-service/`)

**Responsibilities:** RabbitMQ consumer for new reservations + scheduled task for nightly low-capacity alert.

**Endpoints:**
- `POST /trigger/nightly` — invoked by Google Cloud Scheduler (API key auth)
- `GET /health`

**Workers:**
- `queue_consumer` — runs as asyncio task in FastAPI lifespan, consumes `reservations` queue, sends confirmation email
- `occupancy_checker` — invoked by `/trigger/nightly`, scans hotels with low availability, sends admin alert

**Storage:** Supabase Postgres (read) + Resend SMTP.

### 4.7 AI Agent Service (`services/ai-agent-service/`)

**Responsibilities:** Chat endpoint, LLM orchestration, MCP client managing tool server subprocess.

**Endpoints:**
- `POST /api/v1/agent/chat` — `{message: str, session_id: str, token?: str}` → `{response: str}`

**MCP Server tools:**
- `search_hotels(destination, check_in, check_out, guests)` → JSON list of hotels
- `book_hotel(hotel_id, room_id, check_in, check_out, token)` → booking confirmation
- `get_hotel_comments(hotel_id)` → comments + ratings

**Storage:** In-memory session map (per browser tab).

---

## 5. Data Models

### 5.1 Postgres Schema (Supabase)

```sql
-- Schema: public
-- Used by: admin, search, booking, notification services

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(32) NOT NULL DEFAULT 'user', -- 'user' | 'hotel_admin'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);

CREATE TABLE hotels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    destination VARCHAR(255) NOT NULL, -- searchable city/region (e.g., "Rome", "Istanbul")
    address TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    admin_email VARCHAR(255) NOT NULL,   -- recipient of low-capacity alerts
    star_rating SMALLINT,                -- 1-5
    amenities JSONB DEFAULT '[]',        -- ["wifi", "pool", "breakfast", ...]
    image_url TEXT,                      -- optional, may be NULL in v1
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ                -- soft delete
);

CREATE INDEX idx_hotels_destination ON hotels(LOWER(destination));
CREATE INDEX idx_hotels_location ON hotels(latitude, longitude);

CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    room_type VARCHAR(100) NOT NULL,     -- "Single", "Double", "Suite"
    capacity SMALLINT NOT NULL,           -- max guests per room
    base_price_per_night DECIMAL(10,2) NOT NULL,
    total_rooms SMALLINT NOT NULL,        -- how many of this type exist
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rooms_hotel_id ON rooms(hotel_id);

CREATE TABLE room_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    available_count SMALLINT NOT NULL,    -- decremented on booking
    UNIQUE(room_id, date)
);

CREATE INDEX idx_room_availability_date ON room_availability(room_id, date);

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    room_id UUID NOT NULL REFERENCES rooms(id),
    hotel_id UUID NOT NULL REFERENCES hotels(id),
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    guests SMALLINT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'confirmed', -- 'confirmed' | 'cancelled'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_dates ON bookings(check_in, check_out);
```

### 5.2 MongoDB Schema (Comments)

```javascript
// Collection: comments
// Database: hotel_booking_comments

{
  _id: ObjectId,
  hotel_id: String,           // UUID from Postgres hotels.id
  user_id: String,            // Firebase UID
  user_display_name: String,
  text: String,               // comment body
  ratings: {                  // 5-dimensional, each on 1-10 scale (matches PDF mockup)
    cleanliness:      Number, // Temizlik
    staff:            Number, // Personel ve servis
    amenities:        Number, // İmkân ve özellikler
    comfort:          Number, // Konaklama yerinin durumu, imkânları ve kolaylıkları
    eco_friendliness: Number  // Çevre dostluğu
  },
  overall_rating: Number,     // computed average of the 5 ratings (1-10 scale)
  created_at: ISODate,
  deleted_at: ISODate         // null if active
}

// Indexes:
db.comments.createIndex({ hotel_id: 1, created_at: -1 });
db.comments.createIndex({ user_id: 1 });
```

### 5.3 Rating Distribution Aggregation

```javascript
// Endpoint: GET /api/v1/comments/hotels/{hotel_id}/distribution
// MongoDB aggregation pipeline:

[
  { $match: { hotel_id: "...", deleted_at: null } },
  { $group: {
      _id: null,
      total_comments: { $sum: 1 },
      avg_cleanliness:      { $avg: "$ratings.cleanliness" },
      avg_staff:            { $avg: "$ratings.staff" },
      avg_amenities:        { $avg: "$ratings.amenities" },
      avg_comfort:          { $avg: "$ratings.comfort" },
      avg_eco_friendliness: { $avg: "$ratings.eco_friendliness" },
      avg_overall:          { $avg: "$overall_rating" },
      // Score distribution buckets (overall on 1-10 scale, bucketed into 1-10)
      ratings_breakdown: {
        $push: { $floor: "$overall_rating" }
      }
  }}
]
```

Frontend renders this as a horizontal bar chart with 5 service dimensions (mirroring the PDF mockup) + an overall score-distribution histogram.

### 5.4 RabbitMQ Message Format

**Exchange:** `reservations-exchange` (topic, **durable=True**)
**Queue:** `q.reservations.notifications` (**durable=True**)
**Routing key:** `reservation.created`
**Message:** `delivery_mode=PERSISTENT` (broker writes to disk; mandatory for broker-restart resilience)
**Consumer:** `auto_ack=False` → explicit `basic_ack` on success / `basic_nack(requeue=True)` on transient error

```json
{
  "event_type": "reservation.created",
  "booking_id": "uuid",
  "user_email": "user@example.com",
  "user_display_name": "John Doe",
  "hotel_id": "uuid",
  "hotel_name": "Hotel Roma Plaza",
  "check_in": "2026-07-15",
  "check_out": "2026-07-18",
  "guests": 2,
  "total_price": 630.00,
  "created_at": "2026-05-17T10:30:00Z"
}
```

---

## 6. API Specifications

### 6.1 Conventions
- All endpoints use `/api/v1/` prefix
- Pagination: `?page=1&limit=20` (default page=1, limit=20, max=100)
- Errors: `{ "detail": "message", "code": "ERROR_CODE" }`
- Dates: ISO 8601 (`2026-07-15`)
- Datetimes: ISO 8601 UTC (`2026-05-17T10:30:00Z`)
- Authentication: `Authorization: Bearer <firebase_id_token>`

### 6.2 Example: POST /api/v1/admin/hotels

**Request**
```http
POST /api/v1/admin/hotels HTTP/1.1
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "name": "Hotel Roma Plaza",
  "description": "Luxury hotel in city center",
  "destination": "Rome",
  "address": "Via del Corso 123, Rome, Italy",
  "latitude": 41.9028,
  "longitude": 12.4964,
  "admin_email": "admin@romaplaza.com",
  "star_rating": 4,
  "amenities": ["wifi", "pool", "breakfast"]
}
```

**Response 201**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Hotel Roma Plaza",
  "destination": "Rome",
  "latitude": 41.9028,
  "longitude": 12.4964,
  "admin_email": "admin@romaplaza.com",
  "created_at": "2026-05-17T10:30:00Z"
}
```

### 6.3 Example: GET /api/v1/search

**Request**
```http
GET /api/v1/search?destination=Rome&check_in=2026-07-15&check_out=2026-07-18&guests=2&page=1&limit=10 HTTP/1.1
Authorization: Bearer eyJhbGc...   # optional - if present, applies 15% discount
```

**Response 200**
```json
{
  "page": 1,
  "limit": 10,
  "total": 23,
  "items": [
    {
      "hotel_id": "uuid",
      "name": "Hotel Roma Plaza",
      "destination": "Rome",
      "latitude": 41.9028,
      "longitude": 12.4964,
      "star_rating": 4,
      "amenities": ["wifi", "pool", "breakfast"],
      "image_url": null,
      "available_rooms": [
        {
          "room_id": "uuid",
          "room_type": "Double",
          "capacity": 2,
          "price_per_night": 178.50,
          "original_price": 210.00,
          "discount_applied": true
        }
      ]
    }
  ]
}
```

### 6.4 Full endpoint table

| Service | Method | Path | Auth | Notes |
|---|---|---|---|---|
| admin | POST | /api/v1/admin/hotels | ✓ | Create hotel |
| admin | GET | /api/v1/admin/hotels | ✓ | List with pagination |
| admin | GET | /api/v1/admin/hotels/{id} | ✓ | Hotel detail |
| admin | PUT | /api/v1/admin/hotels/{id} | ✓ | Update hotel |
| admin | DELETE | /api/v1/admin/hotels/{id} | ✓ | Soft delete |
| admin | POST | /api/v1/admin/hotels/{id}/rooms | ✓ | Create room |
| admin | GET | /api/v1/admin/hotels/{id}/rooms | ✓ | List rooms |
| admin | PUT | /api/v1/admin/rooms/{id}/availability | ✓ | Set availability range |
| admin | GET | /api/v1/admin/rooms/{id}/availability | ✓ | Get availability |
| search | GET | /api/v1/search | opt | Search hotels |
| search | GET | /api/v1/search/hotels/{id} | opt | Cached detail |
| booking | POST | /api/v1/bookings | ✓ | Book a room |
| booking | GET | /api/v1/bookings | ✓ | User's bookings |
| booking | GET | /api/v1/bookings/{id} | ✓ | Booking detail |
| booking | DELETE | /api/v1/bookings/{id} | ✓ | Cancel |
| comments | POST | /api/v1/comments | ✓ | Add comment |
| comments | GET | /api/v1/comments/hotels/{id} | – | List comments |
| comments | GET | /api/v1/comments/hotels/{id}/distribution | – | Rating distribution |
| comments | DELETE | /api/v1/comments/{id} | ✓ | Delete own comment |
| notify | POST | /trigger/nightly | API key | Cloud Scheduler trigger |
| agent | POST | /api/v1/agent/chat | opt | Chat with AI agent |

---

## 7. Repository Structure

```
Hotel-Booking-System/
├── .github/
│   └── workflows/
│       ├── ci.yml                          # pytest + lint on PR
│       └── deploy.yml                      # optional: notify Render
├── docs/
│   ├── Guide/                              # final guideline (existing)
│   ├── Lecture_Slides/                     # slides (existing)
│   ├── PROJECT_PLAN.md                     # this document
│   └── ARCHITECTURE.md                     # ER diagram + design rationale
├── frontend/                               # Vite + React + TypeScript (Vercel)
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts                  # axios with JWT interceptor
│   │   │   ├── endpoints.ts               # typed endpoint definitions
│   │   │   ├── hotels.ts                  # TanStack Query hooks: useHotels, useHotel, useSearch
│   │   │   ├── bookings.ts                # useBookings, useCreateBooking
│   │   │   ├── comments.ts                # useComments, useDistribution
│   │   │   └── agent.ts                   # useAgentChat
│   │   ├── components/
│   │   │   ├── ui/                        # shadcn/ui primitives (button, card, dialog, etc.)
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── AdminShell.tsx         # sidebar layout for admin pages
│   │   │   ├── hotel/
│   │   │   │   ├── HotelCard.tsx
│   │   │   │   ├── HotelGallery.tsx       # photo carousel
│   │   │   │   ├── RoomCard.tsx
│   │   │   │   └── AmenitiesGrid.tsx      # icon grid (lucide)
│   │   │   ├── search/
│   │   │   │   ├── SearchBar.tsx          # destination + dates + guests
│   │   │   │   ├── FilterPane.tsx         # star rating, amenities, price range slider
│   │   │   │   └── MapView.tsx            # react-leaflet, synced with list
│   │   │   ├── booking/
│   │   │   │   ├── BookingWidget.tsx      # sticky reserve panel on detail page
│   │   │   │   ├── BookingModal.tsx       # multi-step reserve flow
│   │   │   │   └── BookingSuccess.tsx     # post-reserve confirmation
│   │   │   ├── comments/
│   │   │   │   ├── CommentList.tsx
│   │   │   │   ├── CommentForm.tsx        # 5-dimensional rating input (sliders 1-10)
│   │   │   │   └── RatingChart.tsx        # Recharts bar + histogram
│   │   │   ├── agent/
│   │   │   │   └── ChatWidget.tsx         # floating bottom-right chat
│   │   │   └── common/
│   │   │       ├── ProtectedRoute.tsx
│   │   │       ├── AdminRoute.tsx         # gates on role
│   │   │       └── Skeletons.tsx          # loading placeholders
│   │   ├── pages/
│   │   │   ├── HomePage.tsx               # hero search + featured destinations
│   │   │   ├── SearchResults.tsx          # list + map layout
│   │   │   ├── HotelDetail.tsx            # gallery + rooms + booking widget + comments
│   │   │   ├── MyBookings.tsx             # user's reservations list
│   │   │   ├── LoginPage.tsx
│   │   │   ├── SignUpPage.tsx
│   │   │   ├── ForbiddenPage.tsx
│   │   │   └── admin/
│   │   │       ├── HotelsPage.tsx         # data table with search + sort + paginate
│   │   │       ├── HotelEditPage.tsx      # tabs: detail / rooms / availability
│   │   │       ├── AvailabilityCalendar.tsx  # date grid editor
│   │   │       └── BookingsOverview.tsx   # read-only occupancy view
│   │   ├── hooks/
│   │   │   ├── useAuth.ts                 # Firebase auth state hook
│   │   │   └── useDebounce.ts
│   │   ├── lib/
│   │   │   ├── firebase.ts
│   │   │   ├── utils.ts                   # cn() helper from shadcn
│   │   │   └── format.ts                  # date/currency formatters
│   │   ├── types/
│   │   │   ├── hotel.ts                   # mirrors backend Pydantic schemas
│   │   │   ├── booking.ts
│   │   │   ├── comment.ts
│   │   │   └── api.ts                     # pagination, error shapes
│   │   ├── App.tsx                        # routes + QueryClientProvider
│   │   ├── main.tsx
│   │   └── index.css                      # Tailwind directives
│   ├── public/
│   ├── components.json                    # shadcn config
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── .env.example
├── services/
│   ├── shared/                            # editable Python package
│   │   ├── shared/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # pydantic-settings base
│   │   │   ├── logging.py                # structlog config
│   │   │   ├── pagination.py
│   │   │   ├── schemas/                  # Pydantic v2 models
│   │   │   │   ├── hotel.py
│   │   │   │   ├── room.py
│   │   │   │   ├── booking.py
│   │   │   │   ├── comment.py
│   │   │   │   └── user.py
│   │   │   ├── auth/
│   │   │   │   ├── firebase.py           # verify_id_token wrapper
│   │   │   │   └── deps.py               # FastAPI Depends() helpers
│   │   │   └── clients/
│   │   │       ├── postgres.py           # async engine + session
│   │   │       ├── mongo.py              # motor client
│   │   │       ├── redis.py              # asyncio redis
│   │   │       └── rabbitmq.py           # aio-pika connection pool
│   │   └── pyproject.toml
│   ├── gateway/                          # FastAPI proxy
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes.py
│   │   │   └── middleware/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── admin-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   ├── models/                   # SQLAlchemy ORM
│   │   │   └── repositories/
│   │   ├── migrations/                   # Alembic
│   │   ├── alembic.ini
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── search-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   └── services/                 # cache, pricing
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── booking-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   └── services/                 # booking, queue publisher
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── comments-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   └── services/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── notification-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/                  # /trigger/nightly
│   │   │   ├── workers/                  # queue consumer, occupancy checker
│   │   │   └── services/                 # email
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   └── ai-agent-service/
│       ├── app/
│       │   ├── main.py
│       │   ├── agent.py
│       │   ├── mcp_client.py
│       │   └── session.py
│       ├── mcp_server/
│       │   ├── server.py
│       │   └── tools/
│       ├── requirements.txt
│       ├── Dockerfile
│       └── .env.example
├── infrastructure/
│   ├── docker-compose.yml                # local dev: full stack
│   ├── render.yaml                       # Render Blueprint
│   └── postman_collection.json           # API test collection
├── scripts/
│   ├── warmup.py                         # cron-job.org pings here
│   ├── seed_demo_data.py                 # demo data seeder
│   └── load_test.js                      # k6 (ported from midterm)
├── .gitignore
├── .env.example                          # root env template
├── CLAUDE.md                             # existing
└── README.md                             # main project README
```

---

## 8. External Services — Manual Setup Steps

> **IMPORTANT:** You must complete these setup steps yourself. I will help you wire up the integrations in code, but cannot create accounts on your behalf. Each section ends with the env vars you should collect into a single `.env.template` file.

### 8.1 Supabase (Postgres)

**Free tier:** 500 MB storage, 2 GB egress/month, 50 concurrent connections, no card required.

**Steps:**
1. Go to https://supabase.com and click **Sign up** (use GitHub login for fastest setup)
2. After login, click **New project**
3. Project name: `hotel-booking-system`
4. Database password: generate a strong one and **save it in a password manager** — you'll need it for the connection string
5. Region: choose closest to you (e.g., `Central EU (Frankfurt)` for Turkey)
6. Pricing plan: **Free**
7. Click **Create new project** — wait ~2 minutes for provisioning
8. Once ready, go to **Settings → Database**
9. Under **Connection string**, copy the URI (URI tab). It looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxx.supabase.co:5432/postgres
   ```
10. Replace `[YOUR-PASSWORD]` with your actual password
11. Also note the **Project URL** and **anon public key** from **Settings → API** (for frontend if you want to use Supabase Storage later for images)

**Collect these:**
```bash
POSTGRES_URL=postgresql://postgres:<password>@db.xxxxxxxxxx.supabase.co:5432/postgres
POSTGRES_HOST=db.xxxxxxxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your-password>
POSTGRES_DB=postgres
```

### 8.2 Firebase Authentication

**Free tier:** Unlimited authentications, 50k MAU SMS verification (we won't use SMS).

**Steps:**
1. Go to https://console.firebase.google.com
2. Sign in with a Google account
3. Click **Add project**
4. Project name: `hotel-booking-system`
5. **Disable Google Analytics** (not needed, simpler setup)
6. Click **Create project** — wait ~30 seconds
7. Once ready, in left sidebar click **Build → Authentication**
8. Click **Get started**
9. Under **Sign-in method** tab, enable:
   - **Email/Password** (click pencil icon → toggle ON → Save)
   - **Google** (optional, for one-click login)
10. Now create the **web app** for frontend integration:
    - On project overview page, click the **</> Web icon** ("Add app")
    - App nickname: `hotel-booking-web`
    - **Do not** check "Firebase Hosting"
    - Click **Register app**
    - Copy the `firebaseConfig` object shown — looks like:
      ```js
      const firebaseConfig = {
        apiKey: "AIzaSyXXX...",
        authDomain: "hotel-booking-system.firebaseapp.com",
        projectId: "hotel-booking-system",
        storageBucket: "hotel-booking-system.appspot.com",
        messagingSenderId: "123456789",
        appId: "1:123:web:abc"
      };
      ```
11. Now create the **service account** (for backend JWT verification):
    - Go to **Project Settings** (gear icon) → **Service accounts** tab
    - Click **Generate new private key**
    - Confirm and download the JSON file
    - Save as `firebase-service-account.json` in a secure location
    - **DO NOT commit this file to git** (it's in our `.gitignore`)

**Collect these:**
```bash
# Frontend (.env in frontend/)
VITE_FIREBASE_API_KEY=AIzaSyXXX...
VITE_FIREBASE_AUTH_DOMAIN=hotel-booking-system.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=hotel-booking-system
VITE_FIREBASE_APP_ID=1:123:web:abc

# Backend (.env for services)
FIREBASE_SERVICE_ACCOUNT_JSON=<paste full JSON content as single line>
# OR
FIREBASE_SERVICE_ACCOUNT_PATH=/secrets/firebase-service-account.json
FIREBASE_PROJECT_ID=hotel-booking-system
```

### 8.3 MongoDB Atlas (Comments)

**Free tier:** M0 shared cluster, 512 MB storage, no card required.

**Steps:**
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up (Google login works)
3. Answer the onboarding questions:
   - Goal: "Learning MongoDB"
   - Language: "Python"
   - Click **Finish**
4. Choose a deployment option:
   - Select **M0 FREE**
   - Provider: **AWS**
   - Region: closest to you (e.g., `eu-central-1` Frankfurt)
   - Cluster name: `hotel-booking-cluster`
   - Click **Create deployment**
5. **Security setup**:
   - Authentication method: **Username and Password**
   - Username: `hotelapp`
   - Password: generate strong, save in password manager
   - Click **Create user**
6. **Network access**:
   - Click **Add my current IP address** (for local dev)
   - **ALSO** click **Add a different IP address** → enter `0.0.0.0/0` (for Render deployment — necessary since Render IPs are dynamic on free tier)
   - Click **Add Entry**
7. After cluster is ready (~3 minutes), click **Connect**
   - Choose **Drivers** → Python → version 3.12 or later
   - Copy the connection string:
     ```
     mongodb+srv://hotelapp:<password>@hotel-booking-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - Replace `<password>` with your actual password
8. Create the database:
   - Go to **Database → Browse Collections**
   - Click **Add my own data**
   - Database name: `hotel_booking_comments`
   - Collection name: `comments`
   - Click **Create**

**Collect these:**
```bash
MONGO_URL=mongodb+srv://hotelapp:<password>@hotel-booking-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=hotel_booking_comments
```

### 8.4 Upstash Redis (Cache)

**Free tier:** 10,000 commands/day, 256 MB max DB size, 1 database.

**Steps:**
1. Go to https://upstash.com
2. Sign up with GitHub or Google
3. Click **Create Database**
4. Name: `hotel-booking-cache`
5. Type: **Regional** (cheaper, fine for free)
6. Region: closest to you (e.g., `eu-central-1` Frankfurt)
7. Eviction: **allkeys-lru** (auto-evict when full)
8. TLS: **Enabled** (default, required)
9. Click **Create**
10. On the database page, you'll see:
    - **Endpoint**: `xxx-yyy-zzz.upstash.io`
    - **Port**: `6379`
    - **Password**: shown — copy this
    - **REST URL** and **REST Token** (optional, we'll use Redis protocol, not REST)
11. The standard Redis URL format:
    ```
    rediss://default:<password>@xxx-yyy-zzz.upstash.io:6379
    ```
    Note: `rediss://` (double 's') for TLS

**Collect these:**
```bash
REDIS_URL=rediss://default:<password>@xxx-yyy-zzz.upstash.io:6379
```

### 8.5 CloudAMQP (RabbitMQ)

**Free tier "Little Lemur":** 1 million messages/month, 100 connections, 1k queues, 100 MB disk.

**Steps:**
1. Go to https://www.cloudamqp.com
2. Click **Try it for free** → sign up (GitHub login works)
3. Click **Create new instance**
4. Name: `hotel-booking-mq`
5. Plan: **Little Lemur** (free)
6. Region: closest (e.g., `Amazon Web Services - eu-central-1`)
7. Tags: leave empty
8. Click **Create instance**
9. Click on the new instance to see details
10. Note the **URL** field — it looks like:
    ```
    amqps://username:password@xxx.rmq.cloudamqp.com/username
    ```
11. (Optional) Click **RabbitMQ Manager** link to open admin UI — verify connection

**Collect these:**
```bash
RABBITMQ_URL=amqps://username:password@xxx.rmq.cloudamqp.com/username
```

### 8.6 Groq (LLM API)

**Free tier:** 30 req/min, 6000 tokens/min for Llama 3.3 70B Versatile.

**Steps:**
1. Go to https://console.groq.com
2. Sign up (Google login works)
3. Once logged in, go to **API Keys** in left sidebar
4. Click **Create API Key**
5. Name: `hotel-booking-agent`
6. Copy the key (shown only once)

**Collect these:**
```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
```

### 8.7 Resend (Email/SMTP)

**Free tier:** 100 emails/day, 3000/month, 1 domain.

**Steps:**
1. Go to https://resend.com
2. Sign up (GitHub login works)
3. After login, you'll be in the dashboard
4. Click **API Keys** → **Create API Key**
5. Name: `hotel-booking-notifier`
6. Permission: **Full access** (or sending only)
7. Copy the key
8. For sending emails:
   - **Free option:** Use Resend's test domain `onboarding@resend.dev` (only sends to your registered email)
   - **Better option:** Add and verify your own domain — but requires owning a domain
   - **For this project:** Use the test domain since notifications are demo-only

**Collect these:**
```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxx
EMAIL_FROM=onboarding@resend.dev   # change if you verify your own domain
```

### 8.8 Render (Backend Hosting)

**Free tier:** 750 hours/month/service, 512 MB RAM, 0.1 CPU, sleeps after 15 min idle.

**Steps:**
1. Go to https://render.com
2. Sign up with **GitHub** (required for repo-based deploy)
3. Authorize Render to access your repos
4. **Do not deploy yet** — we'll use `render.yaml` Blueprint after pushing code to GitHub
5. Note: You'll create services via Blueprint in a later phase

**Collect these:** _No env vars needed yet — Render dashboard URL will be `https://dashboard.render.com`_

### 8.9 Vercel (Frontend Hosting)

**Free tier:** 100 GB bandwidth/month, automatic HTTPS, GitHub integration.

**Steps:**
1. Go to https://vercel.com
2. Sign up with **GitHub**
3. Authorize Vercel
4. We'll import the project after pushing to GitHub

**Collect these:** _Vercel dashboard URL: https://vercel.com/dashboard_

### 8.10 Google Cloud Scheduler (Nightly Task)

**Free tier:** 3 jobs/month free across all Google Cloud projects. Requires billing account but won't charge if you stay in free tier.

**Steps:**
1. Go to https://console.cloud.google.com
2. Sign in with Google account
3. Create new project:
   - Click project selector at top → **New Project**
   - Name: `hotel-booking-system`
   - Click **Create**
4. **Enable billing** (required for Scheduler but free tier won't charge):
   - Go to **Billing**
   - Link a billing account (must add credit card, will not be charged in free tier)
5. **Enable Cloud Scheduler API**:
   - Search for "Cloud Scheduler API" in top search
   - Click **Enable**
6. **Don't create the job yet** — wait until notification-service is deployed (Phase 8). You'll need the deployed Render URL.

**Collect these:** _No env vars yet — Cloud Scheduler hits your endpoint, doesn't need keys_

### 8.11 cron-job.org (Warmup Pinger)

**Free tier:** 50 cronjobs, every minute granularity.

**Steps:**
1. Go to https://cron-job.org
2. Sign up (email + password, no card)
3. Verify email
4. **Don't create jobs yet** — wait until services are deployed

**Collect these:** _Configured via UI, no env vars_

### 8.12 GitHub Repository

**Steps:**
1. Go to https://github.com (you have an account: `batikanakdenizz`)
2. Click **New repository**
3. Name: `Hotel-Booking-System` or `se4458-hotel-booking-system`
4. Description: "SE 4458 Final Project — Microservice Hotel Booking System with AI Agent"
5. **Public** (required for deliverable submission)
6. Do **not** initialize with README — we have one locally
7. Click **Create repository**
8. Copy the repository URL (HTTPS): `https://github.com/batikanakdenizz/<repo-name>.git`

**Collect these:**
```bash
GITHUB_REPO_URL=https://github.com/batikanakdenizz/Hotel-Booking-System.git
```

---

## 9. Local Development Environment

### 9.1 Required tools

| Tool | Version | Purpose | Install |
|---|---|---|---|
| Docker Desktop | Latest | Run services + DBs locally | https://www.docker.com/products/docker-desktop |
| Python | 3.12+ | Run services without Docker (optional) | https://www.python.org/downloads/ |
| Node.js | 20+ LTS | Frontend dev server | https://nodejs.org |
| Git | Any | Version control | https://git-scm.com |
| VS Code (or PyCharm) | Latest | Editor | https://code.visualstudio.com |
| k6 | Latest | Load testing (optional) | https://k6.io/docs/get-started/installation |
| Postman / Bruno | Latest | API testing | https://www.postman.com or https://www.usebruno.com |
| MongoDB Compass | Optional | GUI for Atlas | https://www.mongodb.com/products/compass |

### 9.2 VS Code recommended extensions
- Python (Microsoft)
- Pylance
- Docker
- ESLint
- Prettier
- REST Client
- Thunder Client (or Postman extension)

### 9.3 Local environment file

Create `.env` in repo root (gitignored). Each service's `.env.example` tells you what subset it needs. The root `.env` can contain everything for `docker-compose.yml`.

---

## 10. Implementation Phases (Day-by-Day)

> **Estimated total time:** ~40-60 hours over 1-2 weeks.

### Phase 0 — Scaffold (Day 1, ~2-3 hours)
**Goal:** Empty repo runs `docker compose up` with all services replying `{"status": "ok", "service": "<name>"}`.

**Tasks:**
1. Create folder structure
2. Write stub `main.py` for each service (FastAPI + `/health`)
3. Per-service `requirements.txt`, `Dockerfile`, `.env.example`
4. `services/shared/` package with `pyproject.toml`, `__init__.py`, `config.py`
5. `infrastructure/docker-compose.yml` — local stack
6. Root `README.md`, `.gitignore`, `ARCHITECTURE.md` stub
7. Vite + React frontend scaffold
8. `git init`, initial commit, push to GitHub

**Verification:**
- `docker compose -f infrastructure/docker-compose.yml up` succeeds
- All `/health` endpoints return 200
- Frontend dev server shows blank page at http://localhost:5173

### Phase 1 — External services setup (Day 1-2, ~2-3 hours, manual)
**Goal:** All cloud accounts created, all env vars in local `.env`.

**Tasks:** Complete Section 8 above — every subsection.

**Verification:**
- `.env` populated with all credentials
- Can `psql` into Supabase Postgres from local machine
- Can `redis-cli ping` into Upstash
- Can connect to MongoDB Atlas with Compass

### Phase 2 — Shared package + data layer (Day 2-3, ~6 hours)
**Goal:** SQLAlchemy models, Pydantic schemas, Alembic migrations, seed data.

**Tasks:**
1. `services/shared/shared/clients/` — Postgres/Mongo/Redis/RabbitMQ async clients
2. `services/shared/shared/schemas/` — all Pydantic models (Hotel, Room, Booking, Comment, User)
3. `services/shared/shared/auth/firebase.py` — `verify_id_token` wrapper
4. `services/admin-service/app/models/` — SQLAlchemy ORM (Hotel, Room, RoomAvailability, Booking, User)
5. Initialize Alembic in admin-service: `alembic init migrations`
6. Generate initial migration: `alembic revision --autogenerate -m "initial schema"`
7. Apply migration to Supabase: `alembic upgrade head`
8. `scripts/seed_demo_data.py` — seed 10 hotels (Rome, Paris, Istanbul, NYC, etc.) with rooms, availability, sample bookings; **also auto-promote `admin@hotelapp.com` to `role='hotel_admin'`** (assuming that user has signed up via Firebase at least once)
9. `scripts/promote_admin.py <email>` — standalone helper to promote any user to admin role (used by README and demo prep)
10. Run seed script

**Verification:**
- Tables exist in Supabase (check via Table Editor)
- Seed script creates 10 hotels successfully
- Can query Postgres from a Python REPL

### Phase 3 — Admin service (Day 3, ~3 hours)
**Goal:** Full CRUD for hotels + rooms + availability, gated by `role='hotel_admin'` (Firebase JWT for identity + Postgres role check, see §3.2).

**Tasks:**
1. `routers/hotels.py` — POST/GET/PUT/DELETE
2. `routers/rooms.py` — POST/GET, availability PUT/GET
3. `repositories/` — DB access functions
4. Add shared dependency `Depends(require_admin)` per §3.2 (verifies Firebase JWT, looks up `users.role`, returns 403 if not `hotel_admin`)
5. Cache invalidation on hotel-level writes — after Postgres COMMIT, `redis.delete(f"hotel:{id}")` and `redis.delete(f"destination:{name_lower}:hotel_ids")` (see §3.5, §4.2)
6. Auto-Swagger at `/docs`

**Verification:**
- Postman collection: admin user can create hotel, list, update, delete
- Auth: requests without `Authorization` header return **401**
- Authz: requests with a valid JWT but `role='user'` return **403** (test with two seeded accounts: `admin@hotelapp.com` (admin) and `user@hotelapp.com` (regular))
- Cache invalidation: after `PUT /hotels/{id}`, subsequent `GET` from search-service returns updated payload (cache key was deleted)

### Phase 4 — Search service (Day 4, ~4 hours)
**Goal:** Date-range availability search (always-fresh from Postgres) + hotel-detail cache-aside (Redis `hotel:{id}`, 24h TTL) + 15% discount applied at response time + pagination. **Per §3.5 — never cache availability or discounted prices.**

**Tasks:**
1. `routers/search.py` — main search endpoint + hotel-detail endpoint
2. `services/hotel_detail_cache.py` — cache-aside helper specifically for `hotel:{id}` (NOT search results). On read: `redis.get` → miss → Postgres `SELECT` → `redis.set(..., ex=86400)`. On admin-side invalidation: handled by admin-service, not search-service.
3. `services/destination_index.py` — optional cache for `destination:{name_lower}:hotel_ids` (6h TTL)
4. `services/pricing_service.py` — given a request's auth state and a base price, return final price + `discount_applied` flag (runtime computation, never persisted in cache)
5. `services/availability_query.py` — Postgres join (`rooms` + `room_availability`) with date range + capacity filter, returns `(hotel_id, room_id, available_count, base_price)` rows (always fresh)

**Verification:**
- Cold detail lookup: `GET /api/v1/search/hotels/{id}` first call hits Postgres (logs show cache miss + DB query)
- Warm detail lookup: second call hits Redis (logs show cache hit) — TTL 24h
- Search results: availability rows always come from Postgres regardless of cache state (logs show DB query on every search call)
- Discount: token-bearing request returns `price = base_price * 0.85` and `discount_applied: true`; same search without token returns full `base_price` and `discount_applied: false` (proves no discount leak across users)
- Cache invalidation: after admin updates a hotel, next search-service detail call returns updated payload (admin-service `redis.delete` worked)
- `/api/v1/search?destination=Rome` returns Rome hotels with paginated structure

### Phase 5 — Booking service (Day 4, ~3.5 hours)
**Goal:** Transactional booking + reliable durable publish.

**Tasks:**
1. `routers/bookings.py`
2. `services/booking_service.py` — Postgres transaction:
   - SELECT FOR UPDATE on `room_availability` rows for date range
   - Verify all dates have `available_count > 0`
   - Decrement each row
   - INSERT into `bookings`
   - COMMIT
3. `services/queue_publisher.py` — reliable publisher after commit:
   - `aio_pika.connect_robust(...)` for auto-reconnect
   - Declare exchange/queue with `durable=True`
   - Publish with `delivery_mode=PERSISTENT`
   - Wrap in retry decorator (e.g., `tenacity`): 3 attempts, exponential backoff (1s/2s/4s)
   - On terminal failure: structlog.error with `booking_id`, return `False`; endpoint still returns 201 (DB is source of truth) with `notification_dispatched: false` field
4. Idempotency key handling (`Idempotency-Key` header → check `bookings.idempotency_key` unique index)

**Verification:**
- Booking creates Postgres rows
- Capacity decreased
- Message visible in CloudAMQP RabbitMQ Manager with `delivery_mode=2`
- Test scenario: stop the notification-service consumer, place 3 bookings → all 3 events sit durably in the queue, start consumer → 3 emails dispatched (no message loss)

### Phase 6 — Comments service (Day 5, ~3 hours)
**Goal:** MongoDB CRUD with **5-dimensional ratings** matching the PDF mockup + aggregation endpoint feeding the distribution chart.

**Tasks:**
1. `routers/comments.py`
2. Pydantic schemas with the 5 rating fields (`cleanliness`, `staff`, `amenities`, `comfort`, `eco_friendliness`), each constrained to 1-10 inclusive
3. `services/comment_service.py` — compute `overall_rating` as `mean(5 dims)` on insert
4. Aggregation pipeline for `/distribution` endpoint (avg per dim + bucketed overall histogram)
5. Soft delete (`deleted_at`)

**Verification:**
- Can POST a comment with all 5 ratings; missing any one returns 422
- GET returns paginated comments sorted by `created_at DESC`
- `/distribution` returns 5 averages + bucketed overall histogram JSON, matching the PDF mockup shape (Temizlik/Personel/İmkân/Konaklama durumu/Çevre dostluğu)

### Phase 7 — Notification service (Day 5, ~4 hours)
**Goal:** Queue consumer (always running) + nightly endpoint.

**Tasks:**
1. `routers/trigger.py` — `POST /trigger/nightly` with API key header check
2. `workers/queue_consumer.py` — async consumer started in `lifespan`
3. `workers/occupancy_checker.py` — Postgres query for next 30 days
4. `services/email_service.py` — Resend HTTP API client

**Verification:**
- Post a fake booking → email arrives within seconds
- Manually call `/trigger/nightly` → admin email arrives if low capacity hotel exists

### Phase 8 — Gateway (Day 6, ~3 hours)
**Goal:** All traffic routes through gateway with auth + rate limit.

**Tasks:**
1. `routes.py` — route table with ENV-driven URLs
2. `middleware/auth.py` — verify Firebase JWT for protected prefixes
3. `middleware/rate_limit.py` — slowapi 60 req/min per IP
4. CORS for frontend origin

**Verification:**
- All previous test requests work through `http://localhost:8080`
- Protected endpoints reject without token

### Phase 9 — AI Agent service (Day 7, ~5 hours)
**Goal:** Chat endpoint that uses MCP tools to fulfill search + book intents.

**Tasks:**
1. Port MCP server from `SE448-AiAgentFlight`:
   - Replace `query_flights` → `search_hotels`
   - Replace `buy_ticket` → `book_hotel`
   - Add `get_hotel_comments`
2. `app/agent.py` — Groq API client (httpx, OpenAI-compatible endpoint)
3. `app/mcp_client.py` — spawns MCP server subprocess (same pattern as SE448)
4. Session management (in-memory dict keyed by `session_id`)
5. Tool-call loop: LLM → tool selection → MCP call → result → LLM → response

**Verification:**
- POST `/api/v1/agent/chat` with "Find hotels in Rome for July 15-18 for 2 adults" returns list
- Follow-up "Book the first one" creates a booking

### Phase 10 — Frontend (Day 8-10, ~14-16 hours)
**Goal:** Production-quality UX: Booking.com-grade search, Airbnb-warm aesthetic, animated, responsive, fully typed.

**Phase 10.1 — Scaffold & foundations (~2-3h)**
1. `npm create vite@latest -- --template react-ts`
2. Install Tailwind v4, configure `tailwind.config.ts` + `index.css`
3. Initialize shadcn/ui (`npx shadcn@latest init`) — pick base color & theme
4. Install: `framer-motion`, `@tanstack/react-query`, `react-hook-form`, `zod`, `react-day-picker`, `react-leaflet`, `recharts`, `lucide-react`, `sonner`, `firebase`, `axios`
5. `lib/firebase.ts` — initialize Firebase, export `auth`
6. `api/client.ts` — axios instance with JWT interceptor reading from `auth.currentUser.getIdToken()`
7. `App.tsx` — `<QueryClientProvider>` + `<BrowserRouter>` + `<Toaster>` (sonner) + route table
8. `hooks/useAuth.ts` — subscribes to `onAuthStateChanged`, exposes `user`, `role`, `loading`

**Phase 10.2 — Auth pages (~1-2h)**
9. `LoginPage` — split-screen layout: hotel hero image (Unsplash) + form. shadcn `<Input>` `<Button>` with react-hook-form + zod schema. Email/password + "Continue with Google" button. Error toast on failure
10. `SignUpPage` — same layout, password strength indicator, terms checkbox
11. `ProtectedRoute` + `AdminRoute` HOCs — redirect to login or `/forbidden`

**Phase 10.3 — Home + Search (~3-4h)**
12. `HomePage`:
    - Hero section: gradient background or Unsplash hotel collage + floating glass-effect search bar
    - **SearchBar component** — destination input (autocomplete from `destination:*` cache hint via API), date range picker (react-day-picker), guest counter (shadcn `<Popover>` with stepper)
    - "Popular destinations" grid (6 hardcoded city cards with Unsplash images)
    - "Featured hotels" carousel (TanStack Query → `useHotels(featured=true)`)
    - Framer Motion fade-in on scroll
13. `SearchResults`:
    - Two-column layout: filters+list left (60%), Leaflet map right (40%, sticky)
    - Filter pane: star rating (checkbox tree), amenities (toggle chips), price range slider (`Slider` from shadcn)
    - Sort dropdown (price asc/desc, star, distance)
    - HotelCard list: photo, name, stars, amenity chips, price block (strikethrough original + discounted if auth'd)
    - Hover on card → map marker pulses; click marker → card scrolls into view
    - Skeleton states during load (8 cards), empty state if no results

**Phase 10.4 — Hotel detail + Booking (~3-4h)**
14. `HotelDetail`:
    - Photo gallery (HotelGallery) — main image + thumbnail strip, click → lightbox
    - Header: name + stars + address + map mini-link
    - Three-column body:
      - Left: description, AmenitiesGrid (lucide icons), location
      - Center: room cards (RoomCard) — each showing type, capacity, price, "Reserve"
      - Right: sticky BookingWidget — date picker + guests + total price + "Reserve Now" CTA
    - Comments section:
      - Left: RatingChart (Recharts) — horizontal bar chart over the 5 service dimensions (cleanliness/staff/amenities/comfort/eco-friendliness, 1-10 scale, mirroring the PDF mockup) + overall-score-distribution histogram
      - Right: CommentList + "Write a comment" form (if auth'd)
15. `BookingModal` — multi-step (Dialog from shadcn):
    - Step 1: review dates/guests
    - Step 2: review user info (auto-filled from Firebase profile)
    - Step 3: confirm + "Reserve" button
    - Success → checkmark animation (Framer Motion) + "Email sent" message + "View my bookings" link

**Phase 10.5 — User & admin areas (~2-3h)**
16. `MyBookings` — card list of user's reservations (TanStack Query), filter by status, cancel button (status='confirmed')
17. `AdminShell` — sidebar layout with shadcn `<NavigationMenu>`
18. Admin `HotelsPage` — shadcn `<DataTable>` with TanStack Table (search, sort, paginate). "Add Hotel" → `HotelModal` form
19. `HotelEditPage` — tabs (`<Tabs>` from shadcn): "Detail" / "Rooms" / "Availability"
20. `AvailabilityCalendar` — month grid, each cell shows `available_count`, click cell to edit. Save button → batch PUT
21. `BookingsOverview` — read-only occupancy chart per hotel (Recharts area chart)

**Phase 10.6 — AI ChatWidget (~1-2h)**
22. Floating action button (bottom-right, gradient, lucide message-circle icon) on every page
23. Open → 400×600 dialog (slide-up Framer Motion)
24. Message bubbles (user right, AI left), typing indicator (3 dot animation)
25. When AI returns search results: render mini HotelCard list inline; clicking → navigates to detail
26. Quick suggestion chips: "Find hotels in Rome", "Show my bookings"
27. Hooks into `agent.ts` → TanStack Query mutation to `/api/v1/agent/chat`

**Phase 10.7 — Polish (~1-2h)**
28. Dark mode toggle in header (Tailwind `dark:` classes already inherited from shadcn)
29. 404 page (illustrated)
30. Mobile sweep: bottom-sheet booking on mobile, hamburger nav, hide map (button to toggle)
31. Performance: lazy-load admin pages with `React.lazy` + `Suspense`
32. Lighthouse audit ≥ 90 on Performance + Accessibility + Best Practices

**Verification:**
- Full user flow works end-to-end locally (sign up → search → book → comment → chat with AI)
- Lighthouse ≥ 90 on home page + search page + detail page
- Works on 375px mobile width (Chrome DevTools)
- Admin can manage hotels via UI (no Postman needed for demo)
- Dark mode toggle works
- All loading states show skeletons, all errors show toasts

### Phase 11 — Local integration testing (Day 10, ~3 hours)
**Goal:** Everything works via `docker compose up` + Postman collection passes.

**Tasks:**
1. Postman collection covering all endpoints
2. End-to-end manual test:
   - Sign up → admin creates hotel → user searches → user books → user comments → user chats with AI
3. Fix any bugs found
4. k6 load test on search endpoint (port from midterm)

### Phase 12 — Cloud deployment (Day 11, ~4 hours)
**Goal:** All services deployed to Render, frontend to Vercel.

**Tasks:**
1. Finalize `infrastructure/render.yaml`
2. In Render dashboard: **New → Blueprint** → connect repo → apply
3. For each service, paste env vars from local `.env`
4. Wait for builds (~10-15 min for 7 services)
5. Deploy frontend to Vercel:
   - **Add New Project** → import GitHub repo
   - Root directory: `frontend`
   - Framework preset: Vite
   - Add env vars (VITE_FIREBASE_*)
   - Deploy
6. Update `VITE_API_GATEWAY_URL` in Vercel to point to deployed gateway
7. Update CORS in gateway to allow Vercel frontend domain

**Verification:**
- All Render services show "Live"
- Vercel frontend opens, can log in, can search

### Phase 13 — Scheduled tasks + warmup (Day 11, ~2 hours)
**Goal:** Nightly task runs on schedule, services don't sleep.

**Tasks:**
1. **Google Cloud Scheduler**:
   - Go to https://console.cloud.google.com/cloudscheduler
   - **Create Job**
   - Name: `nightly-occupancy-check`
   - Frequency: `0 3 * * *` (3 AM UTC daily)
   - Timezone: `Europe/Istanbul`
   - Target type: **HTTP**
   - URL: `https://notification-service.onrender.com/trigger/nightly`
   - HTTP method: POST
   - Headers: `X-Cron-Secret: <random secret matching notification-service env var>`
   - Auth header: leave empty
   - Click **Create**
2. **cron-job.org** for warmup:
   - Create 7 cronjobs, one per Render service URL
   - Frequency: every 10 minutes
   - URL: `https://<service>.onrender.com/health`
   - Title: `warmup-<service>`
   - Or: single job that pings `scripts/warmup.py` endpoint that bounces to all services

**Verification:**
- Trigger Cloud Scheduler job manually → notification arrives
- Wait 30 min — visit any Render service URL → no cold start

### Phase 14 — Documentation + demo (Day 12, ~4 hours)
**Goal:** README polished, ER diagram in ARCHITECTURE.md, demo video recorded.

**Tasks:**
1. Update `README.md`:
   - Fill in deployed URLs (Vercel frontend, gateway, per-service Swagger)
   - Final assumptions list
   - Issues encountered (genuine problems found during development)
2. `ARCHITECTURE.md`:
   - ER diagram (use dbdiagram.io — free, exports PNG)
   - Service interaction diagram
   - Design decision log
3. Demo video (5 min max):
   - **Script:**
     - 0:00-0:30 — Project intro, architecture diagram on screen
     - 0:30-1:00 — Sign up as user, sign in
     - 1:00-2:00 — Search "Rome" hotels, show map, click hotel, view comments chart
     - 2:00-2:30 — Book a room, show capacity decrease in admin
     - 2:30-3:00 — Sign in as admin, add new hotel
     - 3:00-4:00 — AI agent chat: "Find hotels in Paris for next month, 2 people"
     - 4:00-4:30 — Show RabbitMQ message arrived, email received
     - 4:30-5:00 — Architecture recap, GitHub link
4. Upload to YouTube as **Unlisted**
5. Add video link to README

**Verification:**
- README has all required sections per guideline
- Video plays under 5 min
- All links work

---

## 11. Environment Variables Reference

> Every service has its own `.env` file. The root `.env` aggregates everything for `docker-compose.yml`.

### 11.1 Shared (all backend services need)
```bash
# Auth
FIREBASE_PROJECT_ID=hotel-booking-system
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}   # full JSON as string

# Logging
LOG_LEVEL=INFO
```

### 11.2 admin-service, search-service, booking-service, notification-service
```bash
POSTGRES_URL=postgresql+asyncpg://postgres:<password>@db.xxx.supabase.co:5432/postgres
```

### 11.3 search-service and admin-service (additionally — both need Redis)
```bash
# search-service: cache-aside reads + miss-fill on hotel:{id}
# admin-service: invalidation (redis.delete) after hotel CRUD commits
REDIS_URL=rediss://default:<password>@xxx.upstash.io:6379
HOTEL_DETAIL_TTL_SECONDS=86400        # 24h for hotel:{id}
DESTINATION_INDEX_TTL_SECONDS=21600   # 6h for destination:{name}:hotel_ids
```

### 11.4 booking-service (additionally)
```bash
RABBITMQ_URL=amqps://user:password@xxx.cloudamqp.com/user
RABBITMQ_EXCHANGE=reservations-exchange
RABBITMQ_ROUTING_KEY=reservation.created
RABBITMQ_PUBLISH_MAX_RETRIES=3        # exponential-backoff retry count
RABBITMQ_PUBLISH_TIMEOUT_S=10         # per-attempt timeout
```

### 11.5 comments-service
```bash
MONGO_URL=mongodb+srv://hotelapp:<password>@xxx.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=hotel_booking_comments
```

### 11.6 notification-service (additionally)
```bash
RABBITMQ_URL=amqps://user:password@xxx.cloudamqp.com/user
RABBITMQ_QUEUE=q.reservations.notifications
RESEND_API_KEY=re_xxx
EMAIL_FROM=onboarding@resend.dev
CRON_SECRET=<random-uuid-for-google-scheduler-auth>
```

### 11.7 gateway
```bash
ADMIN_SERVICE_URL=http://admin-service:8001
SEARCH_SERVICE_URL=http://search-service:8002
BOOKING_SERVICE_URL=http://booking-service:8003
COMMENTS_SERVICE_URL=http://comments-service:8004
NOTIFICATION_SERVICE_URL=http://notification-service:8005
AGENT_SERVICE_URL=http://ai-agent-service:8006
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://hotel-booking.vercel.app
RATE_LIMIT_PER_MINUTE=60
```

### 11.8 ai-agent-service
```bash
GATEWAY_URL=http://gateway:8080
GROQ_API_KEY=gsk_xxx
GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_API_KEY=                  # optional fallback
```

### 11.9 frontend (`frontend/.env`)
```bash
VITE_FIREBASE_API_KEY=AIzaSyXXX
VITE_FIREBASE_AUTH_DOMAIN=hotel-booking-system.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=hotel-booking-system
VITE_FIREBASE_APP_ID=1:123:web:abc
VITE_API_GATEWAY_URL=http://localhost:8080  # or https://gateway.onrender.com in prod
```

---

## 12. Deployment Plan

### 12.1 Render Blueprint

`infrastructure/render.yaml` defines all 7 backend services declaratively. After pushing to GitHub, in Render dashboard:

1. **New → Blueprint**
2. Select your repo
3. Render parses `render.yaml`, shows 7 services to be created
4. Click **Apply**
5. For each service, enter env vars (Render injects them at runtime)
6. Wait for builds

Each service deploys independently. Build context is the monorepo root; each `Dockerfile` references `services/<svc>/...` paths.

### 12.2 Render service settings (per service)

- **Type:** Web Service (except notification-service consumer-only could be Background Worker — but we make it Web Service so `/trigger/nightly` HTTP endpoint works)
- **Environment:** Docker
- **Build command:** automatic from Dockerfile
- **Health check path:** `/health`
- **Plan:** Free
- **Auto-deploy:** Yes (on `main` branch push)

### 12.3 Vercel frontend

1. Vercel dashboard → **Add New → Project**
2. Import GitHub repo
3. **Configure project:**
   - Framework Preset: Vite
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`
4. **Environment variables:** add all `VITE_*` from your local `frontend/.env`
   - Critical: `VITE_API_GATEWAY_URL=https://<your-gateway>.onrender.com`
5. **Deploy**

### 12.4 Post-deploy adjustments

- **CORS:** After Vercel deploys, copy the Vercel URL (e.g., `https://hotel-booking-system-xxx.vercel.app`) and update `CORS_ALLOWED_ORIGINS` env var in gateway service on Render
- **Firebase Auth domain whitelist:** In Firebase console → Authentication → Settings → **Authorized domains**, add your Vercel domain

---

## 13. Scheduled Tasks Setup

### 13.1 Google Cloud Scheduler — Nightly Occupancy Check

**One-time setup (after notification-service is deployed):**

1. https://console.cloud.google.com/cloudscheduler
2. Select your `hotel-booking-system` project
3. **Create Job:**
   ```
   Name:               nightly-occupancy-check
   Region:             europe-west1 (or closest)
   Description:        Daily check for hotels with <20% availability
   Frequency:          0 3 * * *
   Timezone:           Europe/Istanbul
   Target type:        HTTP
   URL:                https://notification-service-xxx.onrender.com/trigger/nightly
   HTTP method:        POST
   Auth header:        None (use custom header instead)
   Add header:         X-Cron-Secret = <CRON_SECRET env var value>
   Body:               {} (empty JSON)
   Retry config:       Max attempts 1
   ```
4. Click **Create**
5. **Test:** Click ⋮ menu → **Force run** → check notification-service logs

### 13.2 cron-job.org — Service Warmup

**For each Render service** (7 services), or use one job hitting a single endpoint that pings all:

**Option A (simple, 7 jobs):**
1. https://cron-job.org/en/members/jobs/
2. **Create cronjob**
3. Title: `warmup-gateway`
4. URL: `https://gateway-xxx.onrender.com/health`
5. Schedule: **Every 10 minutes** (`*/10 * * * *`)
6. Save
7. Repeat for each service

**Option B (1 job + warmup script):**
1. Add a `/warmup` endpoint to gateway that fan-out pings all services
2. Single cron-job.org job hitting `https://gateway-xxx.onrender.com/warmup` every 10 min

Choose Option B to save the 50-job limit.

---

## 14. Testing Strategy

### 14.1 Unit tests (pytest)
- Per service: `tests/` folder
- Focus: business logic (pricing 15% discount, availability calculation, rating aggregation)
- Mocked DB clients

### 14.2 Integration tests
- Spin up Postgres + Mongo + Redis via testcontainers (optional, for advanced setup)
- Or: use docker-compose + pytest

### 14.3 End-to-end (Postman collection)
- `infrastructure/postman_collection.json`
- Pre-request: login to Firebase, save token
- Tests cover: create hotel → search → book → comment → chat

### 14.4 Load testing (k6) — bonus
- Port from `SE4458-AirlineTicketing/loadtests/`
- Scenarios:
  - 20 VU constant on `/api/v1/search`
  - 50 VU ramping on booking
- Run locally against staging or production
- Document results in README

---

## 15. Risk Register & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Render free tier sleep causes demo lag | High | Med | cron-job.org warmup every 10 min |
| Upstash 10k cmd/day limit hit | Low | Med | 24h TTL on `hotel:{id}` — hot keys hit only on miss/invalidation; very low cardinality (one key per hotel), monitor usage in Upstash console |
| MongoDB Atlas M0 connection storm | Low | Med | Single client per service, connection pool |
| CloudAMQP connection limit (100) | Low | Low | aio-pika `connect_robust` + single connection pool |
| Firebase quota issues | Very Low | High | Free tier is unlimited, no risk |
| Demo on Friday before mobile freeze | n/a | n/a | Project unrelated, no risk |
| Dual-write between Postgres and RabbitMQ (booking commit succeeds, publish fails) | Med | Med | Durable exchange/queue + persistent messages + 3-retry exponential backoff (handles ~95% of transient failures). Known limitation documented in README; full solution is Outbox/SAGA (PPT_04 slides 26-31). |
| MCP server subprocess fails on Render | Med | High | Test stdio transport in Docker locally before deploy; fallback to direct LangChain @tool if MCP breaks |
| Groq rate limit during demo | Med | Med | Cache LLM responses where possible, have OpenAI key as backup |
| Postgres connection pool exhaustion | Low | High | SQLAlchemy `pool_size=5, max_overflow=10` per service |
| Cold start > 30s on Render free | Med | Med | Warmup keeps services hot; demo from already-hot session |
| Build fails on Render due to shared package | Med | High | Test docker build locally with monorepo context first |

---

## 16. Demo & Video Preparation

### 16.1 Pre-demo checklist (1 hour before recording)
- [ ] All cron-job.org warmups have fired in last 10 min (services hot)
- [ ] Seed data is up-to-date on Supabase
- [ ] Test user account created with bookings
- [ ] Admin account has hotel ownership
- [ ] Browser cache cleared, use fresh window
- [ ] Recording software ready (OBS Studio, free)
- [ ] Microphone audio test

### 16.2 5-minute video script (detailed)

| Time | Action | Notes |
|---|---|---|
| 0:00-0:20 | Title card + architecture diagram | "SE 4458 Final — Batikan Akdeniz" |
| 0:20-0:40 | Walk through architecture (gateway, services, DBs, queue, AI) | Use ARCHITECTURE.md diagram |
| 0:40-1:00 | Open frontend, sign up as new user | Show Firebase login |
| 1:00-1:30 | Search "Rome", show map (Leaflet), show 15% discount for logged-in | Highlight discount label |
| 1:30-2:00 | Click hotel → comments chart (Recharts) | Mention MongoDB |
| 2:00-2:30 | Book a room → show booking confirmation → check inbox for Resend email | Demonstrate queue + notification |
| 2:30-3:00 | Open admin panel, add new room availability | Show authenticated CRUD |
| 3:00-4:00 | Open AI ChatWindow: "Find me a hotel in Paris for July 20-23 for 2 adults" → "Book the first option" | Demonstrate MCP tool calls |
| 4:00-4:30 | Show CloudAMQP RabbitMQ Manager — message visible | Demonstrate queue infrastructure |
| 4:30-5:00 | Show Render dashboard with all 7 services live, GitHub URL | Wrap up |

### 16.3 Recording tips
- Practice the script 2-3 times before recording
- Speak slowly and clearly
- Mute notifications, close other tabs
- Record at 1080p, 30 fps
- Edit out long loading times if needed (max 5 min)
- Upload as **unlisted** YouTube video → link in README

---

## 17. Deliverables Checklist

### 17.1 Per Final_Guideline.pdf

- [ ] Public GitHub repository link
- [ ] README contains:
  - [ ] Final deployed URLs (frontend + at least gateway)
  - [ ] Design rationale
  - [ ] **Assumptions** section, including:
    - [ ] Hotel admin role is set out-of-band via `scripts/promote_admin.py` (no self-service promotion UI)
    - [ ] Resend free-tier test domain `onboarding@resend.dev` only sends to registered emails (demo limitation)
    - [ ] All admins can manage all hotels (no per-hotel ownership) — bilinçli scope reduction
    - [ ] 5 rating dimensions chosen to match the PDF mockup (Temizlik / Personel ve servis / İmkân ve özellikler / Konaklama yerinin durumu / Çevre dostluğu); scale 1-10
  - [ ] **Issues encountered** section, including:
    - [ ] **Dual-write between Postgres and RabbitMQ on booking** — mitigated with durable exchange/queue + persistent messages + 3-attempt exponential-backoff retry + `connect_robust` auto-reconnect; full solution (Outbox / SAGA, PPT_04 slides 26-31) noted as next iteration
    - [ ] Render free-tier cold-start mitigated with cron-job.org warmup
    - [ ] Any genuine bugs found and fixed during development
  - [ ] Data models (ER diagram, link or embedded)
  - [ ] Video link (max 5 min, unlisted YouTube)

### 17.2 Code quality

- [ ] Each service has `/health` endpoint returning 200
- [ ] Each service has auto-generated `/docs` (Swagger UI)
- [ ] API versioning `/api/v1/` throughout
- [ ] Pagination on all list endpoints
- [ ] Per-service Dockerfile (committed, not Docker image)
- [ ] `.gitignore` excludes secrets, credentials, `__pycache__`, `node_modules`
- [ ] No SQLite usage
- [ ] No local auth — Firebase only
- [ ] CORS configured on gateway

### 17.3 Architecture compliance

- [ ] API Gateway in front of all services
- [ ] Distributed cache (Redis) for hotel details
- [ ] NoSQL (MongoDB) for comments only
- [ ] RabbitMQ queue for reservations
- [ ] External IAM (Firebase Auth)
- [ ] Nightly scheduled task (Google Cloud Scheduler)
- [ ] At least 3 services deployed separately (we have 7)
- [ ] Map view ("Haritada göster") working
- [ ] 15% discount for logged-in users
- [ ] AI Agent chat works for search + booking

---

## 18. Time Estimate

| Phase | Hours | Calendar Days (working) |
|---|---|---|
| 0. Scaffold | 2-3 | 0.5 |
| 1. External services | 2-3 | 0.5 (parallel) |
| 2. Shared + data | 4-6 | 1 |
| 3. Admin service | 3 | 0.5 |
| 4. Search service | 4 | 0.5-1 |
| 5. Booking service | 3.5 | 0.5 |
| 6. Comments service | 3 | 0.5 |
| 7. Notification service | 4 | 0.5-1 |
| 8. Gateway | 3 | 0.5 |
| 9. AI Agent | 5 | 1 |
| 10. Frontend | 14-16 | 2.5-3 |
| 11. Integration testing | 3 | 0.5 |
| 12. Cloud deployment | 4 | 0.5-1 |
| 13. Scheduled tasks | 2 | 0.25 |
| 14. Docs + demo video | 4 | 0.5 |
| **TOTAL** | **60-73 hours** | **9-12 working days** |

Add 20% buffer for unexpected issues → **~10-13 working days**.

If you work 4-6 hours/day, this is **2-3 weeks**.

---

## Appendix A — Useful References

- FastAPI docs: https://fastapi.tiangolo.com
- SQLAlchemy 2.0 async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Pydantic v2: https://docs.pydantic.dev/latest/
- aio-pika tutorial: https://aio-pika.readthedocs.io/en/latest/quick-start.html
- motor (async MongoDB): https://motor.readthedocs.io
- firebase-admin Python: https://firebase.google.com/docs/admin/setup
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- FastMCP: https://github.com/jlowin/fastmcp
- Render Blueprints: https://render.com/docs/blueprint-spec
- Vercel Vite deployment: https://vercel.com/docs/frameworks/vite
- Google Cloud Scheduler: https://cloud.google.com/scheduler/docs
- Leaflet React: https://react-leaflet.js.org
- Recharts: https://recharts.org
- dbdiagram.io (ER): https://dbdiagram.io
- Groq API (OpenAI-compatible): https://console.groq.com/docs/quickstart

## Appendix B — Common Commands

```bash
# Local development
docker compose -f infrastructure/docker-compose.yml up
docker compose -f infrastructure/docker-compose.yml up admin-service
docker compose logs -f gateway

# Database
cd services/admin-service
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1

# Run a single service without Docker
cd services/admin-service
pip install -e ../shared
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev    # http://localhost:5173
npm run build

# Tests
cd services/admin-service
pytest

# Seed data
python scripts/seed_demo_data.py

# Deploy
git push origin main   # Render + Vercel auto-deploy on push
```

---

**End of Project Plan v1.0**

This plan is a living document. Update it as decisions change during implementation. Each phase should produce a working artifact that can be reviewed before moving on.
