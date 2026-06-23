<div align="center">

<img src="docs/screenshots/Home.png" alt="Hotel Booking System" width="100%" />

# Hotel Booking System

**A production-grade, microservice hotel booking platform.**

*SE 4458 — Software Architecture & Design of Modern Large Scale Systems · Final Project · Group 1*

<p>
  <a href="https://hotel-booking-system-psi-beryl.vercel.app">
    <img src="https://img.shields.io/badge/Live_app-Open-22c55e?style=for-the-badge&logo=vercel&logoColor=white" alt="Live app" />
  </a>
  <a href="https://hbs-gateway.onrender.com/health">
    <img src="https://img.shields.io/badge/API_gateway-Healthy-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="API gateway" />
  </a>
  <a href="https://youtu.be/OdYu_x2EO3o">
    <img src="https://img.shields.io/badge/Demo_video-Watch-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Demo video" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-1f6feb?style=for-the-badge" alt="License" />
  </a>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Supabase-336791?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-Upstash-DC382D?logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/RabbitMQ-CloudAMQP-FF6600?logo=rabbitmq&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Render-2496ED?logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Firebase-Auth-FFCA28?logo=firebase&logoColor=black" />
  <img src="https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036?logo=meta&logoColor=white" />
</p>

</div>

---

<table align="center">
<tr>
<td align="center" width="20%">

### `7`
**Microservices**
<sub>Gateway + 6 domain services</sub>

</td>
<td align="center" width="20%">

### `20+`
**REST endpoints**
<sub>Versioned under `/api/v1/`</sub>

</td>
<td align="center" width="20%">

### `4`
**Managed datastores**
<sub>Postgres · Mongo · Redis · RabbitMQ</sub>

</td>
<td align="center" width="20%">

### `7`
**Verification scripts**
<sub>End-to-end proof in `scripts/`</sub>

</td>
<td align="center" width="20%">

### `100%`
**Cloud-deployed**
<sub>Render · Vercel · GCP Scheduler</sub>

</td>
</tr>
</table>

> [!NOTE]
> The backend runs on **Render's free tier**. A GitHub Actions matrix pings
> every service every 10 minutes (auto-disables on 2026-05-29) so the
> first click during the grading window is instant. After that date the
> first request takes ~30 s to wake the containers.

**Try it now:** open the [live app](https://hotel-booking-system-psi-beryl.vercel.app),
search for **Istanbul** with future dates, click any hotel, and try the
floating AI chat in the bottom-right corner — ask it
*"find me a hotel in Rome on Jul 15 to Jul 18 for 2 guests."*

---

## Highlights

<table>
<tr>
<td width="50%" valign="top">

**Transactional booking**
Postgres `SELECT FOR UPDATE` on every availability row in the date range, atomic decrement, durable RabbitMQ publish after commit — no double-booking under load.

</td>
<td width="50%" valign="top">

**Real LLM tool-calling agent**
Groq Llama 3.3 70B drives an in-process tool registry (`search_hotels`, `book_hotel`, `get_hotel_comments`) against the platform's own gateway, forwarding the user's Firebase token so bookings stay per-user.

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Cache-aside with admin invalidation**
Upstash Redis holds `hotel:{id}` (24 h) and `destination:{city}:hotel_ids` (6 h). Availability is never cached, so we never sell a sold room.

</td>
<td width="50%" valign="top">

**Multi-dimensional reviews**
Single MongoDB pipeline computes 5-dimension averages (`$group`) and the 1–10 histogram (`$bucket`) in one pass; Recharts renders the horizontal-bar distribution on the detail page.

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Event-driven notifications**
Booking events flow through a durable CloudAMQP queue with persistent messages and tenacity-backed 3-retry; consumer acks only after Brevo delivers the email.

</td>
<td width="50%" valign="top">

**Scheduled background work**
Google Cloud Scheduler hits `notification-service` nightly at 02:00 Europe/Istanbul; the worker flags hotels below 20% next-30-day capacity and emails their admin.

</td>
</tr>
</table>

---

## Contents

[Demo](#demo) · [Architecture](#architecture) · [Features](#features) · [Tech stack](#tech-stack) · [Data models](#data-models) · [API surface](#api-surface) · [Project structure](#project-structure) · [Local development](#local-development) · [Production deployment](#production-deployment) · [Verification scripts](#verification-scripts) · [Design decisions](#design-decisions) · [Assumptions](#assumptions) · [Issues encountered](#issues-encountered) · [Demo video](#demo-video) · [License](#license)

---

## Demo

A quick visual tour of the deployed app.

<table>
<tr>
<td width="50%"><img src="docs/screenshots/Location_Hotel_List.png" alt="Search results with map" /><p align="center"><sub><b>Search</b> · destination + dates + guests, with live map</sub></p></td>
<td width="50%"><img src="docs/screenshots/Hotel_Detail_Ratings.png" alt="Hotel detail ratings" /><p align="center"><sub><b>Hotel detail</b> · 5-dim rating distribution + reviews</sub></p></td>
</tr>
<tr>
<td width="50%"><img src="docs/screenshots/Mybookings.png" alt="My bookings" /><p align="center"><sub><b>My bookings</b> · transactional, email-confirmed</sub></p></td>
<td width="50%"><img src="docs/screenshots/Admin_HotelList.png" alt="Admin hotel list" /><p align="center"><sub><b>Admin</b> · authenticated CRUD over hotels & rooms</sub></p></td>
</tr>
<tr>
<td colspan="2" align="center"><img src="docs/screenshots/Ai_Chat.png" alt="AI chat widget" width="420" /><p><sub><b>AI agent</b> · natural-language search + book via Groq Llama 3.3</sub></p></td>
</tr>
</table>

---

## Architecture

```mermaid
flowchart LR
    subgraph Browser ["Browser (Vercel CDN)"]
        UI["React SPA<br/>(Stayfinder)"]
    end

    subgraph Render ["Render — Frankfurt, Docker"]
        GW{{"Gateway :8080<br/>JWT verify · rate limit · CORS"}}
        ADM["admin-service :8001"]
        SRCH["search-service :8002"]
        BK["booking-service :8003"]
        CMT["comments-service :8004"]
        NTF["notification-service :8005"]
        AI["ai-agent-service :8006"]
    end

    subgraph DataStores ["Managed datastores"]
        PG[("Supabase Postgres<br/>hotels / rooms / availability / users / bookings")]
        REDIS[("Upstash Redis<br/>hotel:{id} · destination:{city}:hotel_ids")]
        MONGO[("MongoDB Atlas<br/>comments (5-dim ratings)")]
        MQ[("CloudAMQP RabbitMQ<br/>reservations exchange + queue")]
    end

    subgraph External ["External SaaS"]
        FB[("Firebase Auth")]
        GROQ[("Groq Llama 3.3 70B")]
        RESEND[("Brevo email")]
        GCP[("Google Cloud Scheduler")]
    end

    UI -- "JWT-bearing HTTPS" --> GW
    GW --> ADM & SRCH & BK & CMT & NTF & AI

    ADM --> PG
    ADM --> REDIS
    SRCH --> PG
    SRCH --> REDIS
    BK --> PG
    BK -- "publish reservation.created" --> MQ
    CMT --> MONGO
    NTF <-- "consume" --> MQ
    NTF --> PG
    NTF --> RESEND
    AI -- "tool-call loop<br/>(HTTP, OpenAI fn-calling)" --> GW
    AI -.-> GROQ

    GCP -- "POST /trigger/nightly<br/>(X-Cron-Secret)" --> NTF
    UI -. "ID-token verify" .-> FB
    GW -. verify .-> FB
```

> Sequence diagrams, decision log, and cache key invariants live in
> [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Features

Each feature maps to a requirement in the final guideline; the file
path points reviewers straight to the implementation.

<details open>
<summary><b>1 · Hotel admin — authenticated CRUD over rooms & availability</b></summary>

- Add / update hotels, rooms, and per-date availability.
- Gated by Firebase JWT at the gateway **and** a Postgres
  `users.role = 'hotel_admin'` check downstream; promoting a user is a
  single SQL `UPDATE`.
- Cache invalidation on every write so search readers see fresh data.
- Code: `services/admin-service/app/routers/`.

</details>

<details>
<summary><b>2 · Hotel search — destination + dates + guests, with map</b></summary>

- Searches only rooms whose `room_availability.available_count > 0` for
  every date in `[check_in, check_out)`.
- Destination input has an **autocomplete dropdown** with the seeded
  cities; accent / case / Turkish dotted-İ insensitive so *İstanbul* /
  *istanbul* / *İSTANBUL* all canonicalize to the same search.
- "Haritada göster" via **react-leaflet + CartoDB Voyager tiles**.
- Hotel-detail payloads served from Upstash Redis (`hotel:{id}`, 24 h
  TTL); availability is **never cached**.
- Code: `services/search-service/app/routers/search.py`,
  `frontend/src/components/SearchBar.tsx`.

</details>

<details>
<summary><b>3 · Member-only 15% discount</b></summary>

- Search-service applies a runtime 0.85× multiplier when the request
  carries a verified Firebase token. Anonymous calls get full price.
- `discount_applied: true` flag drives the "Member 15% off" badge.
- Verified by `scripts/verify_discount.py` — every room costs exactly
  0.85× the anonymous price.
- Code: `services/search-service/app/services/pricing.py`.

</details>

<details>
<summary><b>4 · Transactional booking</b></summary>

Inside one async transaction:
- `SELECT … FOR UPDATE` on every `room_availability` row in the date range.
- Assert `available_count > 0`, decrement.
- Insert the booking row (optional `idempotency_key`).
- Commit.

After commit, publish `reservation.created` to a durable RabbitMQ
exchange with `delivery_mode=2` and a 3-retry exponential backoff via
`tenacity`.

Code: `services/booking-service/app/services/booking.py`.

</details>

<details>
<summary><b>5 · Reviews + per-dimension rating distribution</b></summary>

- 5-dimensional ratings on a 1–10 scale per the PDF mockup:
  cleanliness, staff, amenities, comfort, eco-friendliness.
- A single MongoDB aggregation pipeline computes averages (`$group`)
  **and** the histogram (`$bucket`) per hotel — feeds the Recharts
  horizontal-bar chart on the detail page.
- Code: `services/comments-service/app/repositories/comment.py`.

</details>

<details>
<summary><b>6 · Nightly low-occupancy alerts</b></summary>

- `notification-service` exposes `POST /trigger/nightly`, guarded by an
  `X-Cron-Secret` header.
- A scheduled Google Cloud Scheduler job hits it every night at 02:00
  Europe/Istanbul. The worker scans next-30-day availability, flags
  hotels under the 20% threshold, and emails their admin via Brevo.
- Code: `services/notification-service/app/workers/occupancy.py`.

</details>

<details>
<summary><b>7 · RabbitMQ-driven booking notifications</b></summary>

The consumer (`services/notification-service/app/workers/consumer.py`)
pulls every `reservation.created` event, sends a confirmation email via
Brevo, and acks only after the email succeeds — manual ack, at-least-once
semantics.

</details>

<details>
<summary><b>8 · AI agent chat</b></summary>

- Persistent floating widget powered by **Groq Llama 3.3 70B** via the
  OpenAI-compatible API.
- In-process tool registry exposes three tools: `search_hotels`,
  `book_hotel`, `get_hotel_comments`. The agent calls the gateway over
  HTTPS the same way the browser does, forwarding the signed-in user's
  bearer token so per-user bookings work.
- Per-session conversation memory; max 5 tool-iteration cap so a
  misbehaving LLM cannot hammer the API.
- Code: `services/ai-agent-service/app/`.

</details>

<details>
<summary><b>9 · Distributed cache (hotel details + destination index)</b></summary>

- `hotel:{uuid}` strings hold every static hotel field plus its rooms,
  24 h TTL.
- `destination:{lower_city}:hotel_ids` sets index the search-service's
  "all hotels in this city" lookup, 6 h TTL.
- Invalidation owned by `admin-service` on PATCH/DELETE.
- Verified live by `scripts/inspect_cache.py`.

</details>

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend language | **Python 3.12** | Mature async ecosystem; matches stated career goal |
| Web framework | **FastAPI 0.115** | First-class async, Pydantic v2 validation, OpenAPI for free |
| ORM | **SQLAlchemy 2 (async) + asyncpg** | Battle-tested; supports the patterns the Supabase pooler requires |
| Migrations | **Alembic** | Owned by `admin-service`, autogen targets the shared models |
| Postgres | **Supabase** (Frankfurt) | Managed Postgres + free tier; uses Supavisor transaction pooler |
| Document store | **MongoDB Atlas** (M0) | Fits the soft, denormalised comment schema |
| Cache | **Upstash Redis** | Serverless Redis; usage-based free tier |
| Queue | **CloudAMQP RabbitMQ** | Durable exchanges + persistent messages on free "Little Lemur" |
| Auth (IAM) | **Firebase Authentication** | Web SDK + Admin SDK; satisfies the "external IAM" guideline rule |
| LLM | **Groq Llama 3.3 70B** | Sub-second latency, OpenAI-compatible API, generous free tier |
| Email | **Brevo** | 300 emails/day free tier; single-sender verification, no domain needed |
| Frontend framework | **React 19 + Vite + TypeScript** | Fastest dev loop, content-hash chunking, SPA-friendly |
| UI styling | **Tailwind CSS 3.4** | Hand-rolled brand palette + Inter font |
| Data fetching | **TanStack Query 5** | Smart cache, retries, query invalidation hooks |
| Forms | **react-hook-form + zod** | Type-safe validation with a single schema |
| Map | **react-leaflet + CartoDB Voyager** | Voyager has friendlier rate-limits than raw OSM for production |
| Charts | **Recharts 3** | Hand-tuned horizontal-bar chart for the 5-dim rating |
| Toasts / Animations | **Sonner · Framer Motion** | Lightweight toasts + chat widget transitions |
| Backend hosting | **Render** (7 Docker services) | One Blueprint, free tier, Frankfurt region |
| Frontend hosting | **Vercel** (Vite SPA + CDN) | Auto-deploys on every push to `main` |
| Scheduling | **GCP Scheduler + GitHub Actions** | Cloud Scheduler for nightly cron; GH Actions for warmup |

---

## Data models

### Postgres — relational core

```mermaid
erDiagram
    USERS ||--o{ BOOKINGS : "makes"
    HOTELS ||--o{ ROOMS : "has"
    HOTELS ||--o{ BOOKINGS : "for"
    ROOMS  ||--o{ ROOM_AVAILABILITY : "per-day"
    ROOMS  ||--o{ BOOKINGS : "occupies"

    USERS {
        uuid id PK
        string firebase_uid UK
        string email
        string display_name
        string role "user | hotel_admin"
        timestamptz created_at
    }
    HOTELS {
        uuid id PK
        string name
        text description
        string destination "indexed lower()"
        text address
        float latitude
        float longitude
        string admin_email
        smallint star_rating
        jsonb amenities
        text image_url
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
    }
    ROOMS {
        uuid id PK
        uuid hotel_id FK
        string room_type
        smallint capacity
        numeric base_price_per_night
        smallint total_rooms
        timestamptz created_at
    }
    ROOM_AVAILABILITY {
        uuid id PK
        uuid room_id FK
        date date
        smallint available_count
    }
    BOOKINGS {
        uuid id PK
        uuid user_id FK
        uuid hotel_id FK
        uuid room_id FK
        date check_in
        date check_out
        smallint guests
        numeric total_price
        string status "confirmed | cancelled"
        string idempotency_key UK
        timestamptz created_at
    }
```

### MongoDB — `comments` collection

```jsonc
{
  "_id": ObjectId("..."),
  "hotel_id": "439b7445-…",          // logical FK to Postgres hotels.id
  "user_id": "firebase-uid",
  "user_display_name": "Elif K.",
  "text": "Spotless room, generous breakfast …",
  "ratings": {
    "cleanliness": 10,
    "staff": 10,
    "amenities": 9,
    "comfort": 9,
    "eco_friendliness": 7
  },
  "overall_rating": 9.0,             // denormalised average
  "created_at": ISODate("…"),
  "deleted_at": null                 // soft delete
}
```

---

## API surface

Every endpoint is mounted under `/api/v1/`. The gateway preserves the
prefix when proxying.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/search` | optional | Search hotels by destination + dates + guests |
| `GET` | `/api/v1/search/hotels/{id}` | optional | Single hotel detail (cache-aside) |
| `POST` | `/api/v1/admin/hotels` | admin | Create a hotel |
| `GET` | `/api/v1/admin/hotels` | admin | Paginated admin hotel list |
| `PATCH` | `/api/v1/admin/hotels/{id}` | admin | Update a hotel (invalidates cache) |
| `DELETE` | `/api/v1/admin/hotels/{id}` | admin | Soft delete + cache invalidation |
| `POST` | `/api/v1/admin/hotels/{id}/rooms` | admin | Add a room type |
| `PUT` | `/api/v1/admin/rooms/{id}/availability` | admin | Bulk-upsert availability for a date range |
| `POST` | `/api/v1/bookings` | required | Create a transactional booking |
| `GET` | `/api/v1/bookings` | required | Logged-in user's bookings |
| `DELETE` | `/api/v1/bookings/{id}` | required | Cancel a booking |
| `GET` | `/api/v1/comments/hotels/{id}` | optional | Paginated reviews for a hotel |
| `GET` | `/api/v1/comments/hotels/{id}/distribution` | optional | 5-dim averages + histogram |
| `POST` | `/api/v1/comments` | required | Post a 5-dim review |
| `DELETE` | `/api/v1/comments/{id}` | required | Soft-delete own review |
| `POST` | `/api/v1/agent/chat` | optional | AI chat (forwards token for tool auth) |
| `GET` | `/api/v1/agent/debug/config` | optional | Echo effective agent config |
| `GET` | `/api/v1/agent/debug/search` | optional | Bypass-LLM tool sanity check |
| `POST` | `/trigger/nightly` | X-Cron-Secret | Run the nightly low-availability scan |
| `GET` | `/health` | optional | Liveness probe (every service exposes this) |

Pagination uses `?page=<n>&limit=<m>` with a hard `limit ≤ 100`; listing
responses follow `{ items: T[], page: int, limit: int, total: int }`.

---

## Project structure

```
Hotel-Booking-System/
├── README.md
├── .env.example                ← every env var documented here
├── docs/
│   ├── ARCHITECTURE.md         ← sequence diagrams, decision log
│   ├── DEPLOY.md               ← step-by-step Render + Vercel
│   ├── SCHEDULING.md           ← Cloud Scheduler + warmup setup
│   └── Plan/                   ← original implementation plan (TR + EN)
├── infrastructure/
│   ├── docker-compose.yml      ← local 7-service stack (optional)
│   └── render.yaml             ← one-click Render Blueprint
├── .github/workflows/
│   └── warmup.yml              ← 10-min ping matrix, auto-disables 2026-05-29
├── frontend/                   ← React 19 + Vite + TS SPA
│   ├── vercel.json             ← SPA rewrite for React Router
│   ├── tailwind.config.js
│   └── src/
│       ├── App.tsx             ← router + providers
│       ├── pages/              ← Home · Search · HotelDetail · Login · SignUp · MyBookings · AdminHotels
│       ├── components/         ← HotelCard · HotelMap · RatingChart · ChatWidget
│       ├── api/                ← typed TanStack Query hooks
│       ├── hooks/              ← AuthProvider (Firebase)
│       └── lib/                ← axios client, firebase init, utils
├── services/
│   ├── shared/                 ← installable editable package
│   │   └── shared/
│   │       ├── auth/           ← firebase.py + deps.py (lazy SQLAlchemy)
│   │       ├── clients/        ← postgres · mongo · redis · rabbitmq
│   │       ├── models/         ← SQLAlchemy 2 ORM (single source of truth)
│   │       └── schemas/        ← Pydantic v2 DTOs
│   ├── gateway/                ← single public surface
│   ├── admin-service/          ← also home to Alembic migrations
│   ├── search-service/
│   ├── booking-service/
│   ├── comments-service/
│   ├── notification-service/
│   └── ai-agent-service/
└── scripts/
    ├── verify_external_services.py   ← Postgres / Mongo / Redis / RabbitMQ / Firebase / Groq / Brevo
    ├── seed_demo_data.py             ← seed Postgres with 10 hotels + 90-day availability
    ├── seed_demo_comments.py         ← seed Mongo with 4-6 reviews per hotel
    ├── promote_admin.py              ← UPDATE users SET role='hotel_admin'
    ├── smoke_test_gateway.py         ← unauthenticated golden-path e2e check
    ├── verify_discount.py            ← prove the 15% member discount is exact
    ├── inspect_cache.py              ← dump live Upstash Redis keys + TTLs
    └── run_all_services.ps1          ← Windows launcher for 7 dev services
```

---

## Local development

> Tested with Python 3.12 / 3.13, Node 20+, PowerShell 5.1 on Windows 11.
> Same commands work on macOS/Linux with minor path tweaks.

**1. Clone and configure**

```bash
git clone https://github.com/batikanakdenizz/Hotel-Booking-System.git
cd Hotel-Booking-System
cp .env.example .env
# Fill in real values (Supabase URL, Firebase service account JSON, etc.)
```

**2. Backend setup**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r scripts/requirements.txt
pip install -r services/admin-service/requirements.txt
pip install -r services/search-service/requirements.txt
# ... or: for /R %f in (requirements.txt) do pip install -r %f
```

Apply schema and seed data:

```powershell
$env:POSTGRES_URL = (Get-Content .env | Where-Object { $_ -like "POSTGRES_URL=*" }) -replace "^POSTGRES_URL=", ""
cd services/admin-service
alembic upgrade head
cd ../..
python scripts/seed_demo_data.py
python scripts/seed_demo_comments.py
```

**3. Run all services**

```powershell
.\scripts\run_all_services.ps1
```

This opens seven PowerShell windows, one per service.

**4. Run the frontend**

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

The Vite dev server proxies `/api/*` to the local gateway.

**5. Smoke-check everything**

```bash
python scripts/smoke_test_gateway.py
```

Expected output (each step under 1 s after warmup):

```
[PASS] gateway /health
[PASS] GET /api/v1/search?destination=Rome -- total=2
[PASS] GET /api/v1/search/hotels/{id}
[PASS] GET /api/v1/comments/hotels/{id}
[PASS] GET /api/v1/comments/hotels/{id}/distribution
[PASS] POST /api/v1/agent/chat -- LLM returned hotel list
```

---

## Production deployment

The step-by-step lives in [`docs/DEPLOY.md`](docs/DEPLOY.md). High-level:

| # | Step | Where | Time |
|---|---|---|---|
| 1 | Push code to GitHub | local | 1 min |
| 2 | Render Blueprint → reads `infrastructure/render.yaml`, creates 7 services | Render dashboard | 5 min |
| 3 | Set per-service secrets (Postgres / Mongo / Redis / RabbitMQ / Groq / Brevo / Firebase) | Render env tab | 10 min |
| 4 | Verify `/health` returns 200 | terminal | 1 min |
| 5 | Vercel project import, root = `frontend/` | Vercel dashboard | 3 min |
| 6 | Set `VITE_*` env vars (Firebase web SDK + gateway URL) | Vercel env tab | 5 min |
| 7 | Add Vercel URL to `CORS_ALLOWED_ORIGINS` on the gateway | Render env tab | 2 min |
| 8 | Add Vercel host to Firebase Authorized Domains | Firebase console | 2 min |
| 9 | Create the Cloud Scheduler nightly job | GCP console | 5 min |

<table>
<tr>
<td width="50%"><img src="docs/screenshots/Render_Dashboard.png" alt="Render dashboard" /></td>
<td width="50%"><img src="docs/screenshots/Vercel_Dashboard.png" alt="Vercel dashboard" /></td>
</tr>
</table>

---

## Verification scripts

Every claim in this README has a matching script in `scripts/` that
proves it on the live system.

| Script | Proves |
|---|---|
| `verify_external_services.py` | Every external dep (Postgres / Mongo / Redis / RabbitMQ / Firebase / Groq / Brevo) reachable with configured credentials |
| `smoke_test_gateway.py` | Unauthenticated golden path returns 200 with valid bodies |
| `verify_discount.py` | Mints a Firebase ID token, calls `/api/v1/search` anon + auth, asserts **exact** 0.85× ratio |
| `inspect_cache.py` | Walks Upstash Redis, lists every `hotel:*` and `destination:*` key with TTL + payload preview |
| `seed_demo_data.py` | Seeds Postgres with 10 hotels across 7 cities + 90 days of availability + 5 sample bookings |
| `seed_demo_comments.py` | Idempotently inserts 4–6 reviews per hotel into MongoDB (46 docs total) |
| `promote_admin.py` | Flips a user's Postgres `role` to `hotel_admin` |

<details>
<summary><b>Sample output — <code>verify_discount.py</code></b></summary>

```
Hotel                          Room                       Anon       Auth      Ratio   Auth flag
----------------------------------------------------------------------------------------------------
Bosphorus Bay Hotel            Double                   $140.00   $119.00     0.8500    True  [OK]
Bosphorus Bay Hotel            Suite                    $294.00   $249.90     0.8500    True  [OK]
Sultanahmet Palace             Suite                    $294.00   $249.90     0.8500    True  [OK]
Sultanahmet Palace             Double                   $140.00   $119.00     0.8500    True  [OK]

[verify-discount] PASS -- discount is exactly 15% for every room
```

</details>

<details>
<summary><b>Sample output — <code>inspect_cache.py</code></b></summary>

```
=== Hotel-detail entries (pattern=hotel:*) ===
  hotel:439b7445-…  ttl=17.9h  preview={"name": "Bosphorus Bay Hotel", …}
  hotel:5cef9cf5-…  ttl=17.9h  preview={"name": "Sultanahmet Palace", …}
  …
=== Destination index sets (pattern=destination:*) ===
  destination:istanbul:hotel_ids  ttl=5.8h  members=[…, …]
```

</details>

---

## Design decisions

A condensed log of the calls that shaped the system. Long-form versions
in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

1. **Cache hotel details, not search results.** Caching search would
   force aggressive invalidation on every booking; caching the static
   per-hotel fields gives near-instant detail pages without staleness.
2. **Booking commits first, then publishes.** The accepted failure mode
   is "Postgres has the booking, RabbitMQ doesn't" — the user still
   sees their booking, and the durable queue + retry loop makes this
   vanishingly rare.
3. **Identity (Firebase) separated from authorization (Postgres).** The
   gateway verifies the JWT once; downstream services trust the
   forwarded `X-User-Id`. Role checks read from Postgres `users.role`,
   so promoting a user is a single SQL UPDATE.
4. **AI agent uses an in-process tool registry** instead of MCP-over-
   subprocess. Simpler deploy, same behaviour from the LLM's
   perspective.
5. **Pooler-safe asyncpg.** Supabase's transaction pooler reuses
   backend sessions, so prepared statement names are randomised with
   UUIDs (`prepared_statement_name_func`) and the cache is disabled
   (`statement_cache_size=0`).
6. **`Accept-Encoding: identity` on every inter-service hop.**
   Cloudflare in front of Render aggressively brotli-compresses
   responses, and httpx without the optional `brotli` package can't
   decode them.

---

## Assumptions

Explicitly documented so a reviewer can challenge them:

- **Capacity is room-type-based**, not specific-room-based. A single
  `room_availability` row tracks how many physical rooms of a type are
  free on a date.
- **Cancelling a booking does not roll back availability.** A deliberate
  cut-for-time; production would do the opposite under the same lock.
- **"Next month"** in the nightly check is interpreted as the next 30
  days from UTC midnight.
- **Ratings use a 1–10 scale** (matching the PDF mockup), not 1–5 stars.
- **AI agent state is in-memory.** Restarting `ai-agent-service` loses
  per-session chat history; acceptable for a demo.
- **Email is sent from a Brevo-verified single sender** (a personal
  Gmail/Hotmail) so we can deliver to any recipient on the 300/day free
  tier without owning a domain.
- **Render free-tier services sleep after 15 min** of idle. The warmup
  GitHub Action runs only until 2026-05-29 so the project doesn't burn
  free-tier instance hours indefinitely.

---

## Issues encountered

The full audit log (every bug + its commit) lives in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The highlights:

| Symptom | Root cause | Resolution |
|---|---|---|
| `DuplicatePreparedStatementError` from asyncpg | Supabase transaction pooler reuses backend sessions | `prepared_statement_name_func` with UUIDs + `statement_cache_size=0` |
| `ModuleNotFoundError: sqlalchemy` in mongo-only service | Eager re-exports in `shared/__init__.py`s | Slimmed package inits; moved DB imports into function scope |
| `UnicodeDecodeError: byte 0x82` in AI agent | Cloudflare brotli-compressed response; httpx couldn't decode | `Accept-Encoding: identity` on tool & proxy requests |
| "undefined stays" in search results UI | Stale Vercel CDN cache + Render cold-start 502 cascade | Hard refresh + warmup matrix + `Accept-Encoding` fix |
| Fragmented map tiles | Leaflet CSS dropped because `@import` came after `@tailwind` directives | `import 'leaflet/dist/leaflet.css'` in `main.tsx` instead |
| Render Blueprint `fromService.host` returned bare service names | Render's free tier resolves this differently than docs imply | Hardcoded `*.onrender.com` URLs + Pydantic `field_validator` auto-suffixing `.onrender.com` |
| Booking-confirmation emails silently rejected for non-account-owner recipients | Resend sandbox sender only delivers to the account's verified email | Migrated `EmailClient` to Brevo's transactional API |
| `Istanbul` / `İstanbul` / `istanbul` returned different results | Free text input let the user submit a non-canonical destination | Autocomplete dropdown with NFD-normalised, dotted-I tolerant fuzzy match |

All fixed as of commit [`3824e87`](https://github.com/batikanakdenizz/Hotel-Booking-System/commit/3824e87).

---

## Acknowledgements

- **Render · Vercel** for the free hosting tier that makes student
  projects like this deployable.
- **Supabase · MongoDB Atlas · Upstash · CloudAMQP · Firebase · Groq ·
  Brevo** for the no-credit-card free tiers.
- **CartoDB Voyager** for production-grade map tiles after the OSM tile
  server started throttling us.
- The teaching staff of **SE 4458 (Yaşar University)** for the project
  brief.

---

## License

[MIT](LICENSE) — feel free to study, fork, or build on top of this project.

<div align="center">
<sub>Built by <a href="https://github.com/batikanakdenizz">@batikanakdenizz</a> · SE 4458 Final Project · 2026</sub>
</div>
