# Deployment Guide

This guide walks through the **one-time** production deploy of the Hotel Booking
System to **Render** (backend) + **Vercel** (frontend). All steps are manual
because they require interactive sign-in to those platforms.

Estimated time: **30-45 min** end-to-end.

---

## 0. Prerequisites

- GitHub repository with the latest `main` branch pushed
- All external services from `.env.example` already provisioned (Supabase,
  Mongo Atlas, Upstash, CloudAMQP, Firebase, Groq, Resend)
- A working local stack (gateway returns `200` on `/health`)

> Tip: keep your local `.env` open in another tab -- you will be copy-pasting
> ~10 secrets into the Render dashboard.

---

## 1. Backend -> Render (Blueprint)

### 1.1 Connect the repo

1. Log in to https://dashboard.render.com
2. **New +** -> **Blueprint**
3. **Connect a GitHub repo** -> select `Hotel-Booking-System`
4. Render detects `infrastructure/render.yaml` automatically and lists 7 services.
   Confirm the names match:
   - `hbs-gateway` (the only public-facing one for the frontend)
   - `hbs-admin-service`
   - `hbs-search-service`
   - `hbs-booking-service`
   - `hbs-comments-service`
   - `hbs-notification-service`
   - `hbs-ai-agent-service`
5. Click **Apply**. Render creates the services but they will fail to start
   because the secrets are not set yet. **That is expected**.

### 1.2 Set secrets (per service)

For each service, open it in the dashboard -> **Environment** tab -> **Add Environment Variable**.
The `sync: false` keys in `render.yaml` are the ones you must set manually.

| Service | Secrets to set |
|---|---|
| `hbs-gateway` | `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `CORS_ALLOWED_ORIGINS` (set later, after Vercel deploy) |
| `hbs-admin-service` | `POSTGRES_URL`, `REDIS_URL`, `FIREBASE_PROJECT_ID` |
| `hbs-search-service` | `POSTGRES_URL`, `REDIS_URL` |
| `hbs-booking-service` | `POSTGRES_URL`, `RABBITMQ_URL` |
| `hbs-comments-service` | `MONGO_URL` |
| `hbs-notification-service` | `POSTGRES_URL`, `RABBITMQ_URL`, `RESEND_API_KEY`, `CRON_SECRET` |
| `hbs-ai-agent-service` | `GROQ_API_KEY` |

> **Important** for `FIREBASE_SERVICE_ACCOUNT_JSON`: paste the FULL JSON content
> of `.secrets/firebase-service-account.json` as a single line.

### 1.3 First deploy

For each service: **Manual Deploy** -> **Deploy latest commit**.
Watch the logs panel; you should see `service_started` for each.

Verify:

```bash
curl https://hbs-gateway.onrender.com/health
# {"status":"ok","service":"gateway"}
```

> Free-plan services sleep after 15 min idle. First request after sleep
> takes ~30s to cold-start. Warmup pings are set up in Phase 13.

---

## 2. Frontend -> Vercel

### 2.1 Import the project

1. Log in to https://vercel.com
2. **Add New** -> **Project**
3. Select `Hotel-Booking-System` -> set **Root Directory** = `frontend`
4. Framework preset: **Vite** (auto-detected)
5. Do NOT deploy yet -- click **Environment Variables** first

### 2.2 Set environment variables

Add these (values from `frontend/.env.production.example`):

| Key | Value |
|---|---|
| `VITE_API_GATEWAY_URL` | `https://hbs-gateway.onrender.com` |
| `VITE_FIREBASE_API_KEY` | from Firebase Console |
| `VITE_FIREBASE_AUTH_DOMAIN` | from Firebase Console |
| `VITE_FIREBASE_PROJECT_ID` | from Firebase Console |
| `VITE_FIREBASE_STORAGE_BUCKET` | from Firebase Console |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | from Firebase Console |
| `VITE_FIREBASE_APP_ID` | from Firebase Console |

Click **Deploy**.

### 2.3 Wire CORS back

After Vercel deploys, copy the production URL (e.g.
`https://hotel-booking-system.vercel.app`) and:

1. Render -> `hbs-gateway` -> **Environment** -> edit `CORS_ALLOWED_ORIGINS`
2. Set to your Vercel URL (and optionally `http://localhost:5173` for local dev)
3. **Manual Deploy** the gateway again so the new origin takes effect

Also add the Vercel URL as an **authorized domain** in Firebase Console ->
Authentication -> Settings -> Authorized domains.

---

## 3. Verification

1. Open the Vercel URL in a private window
2. Sign up with a new email
3. Search `Rome` -> see hotel cards + map
4. Click a hotel, pick a room, book
5. Visit `/my-bookings` -> see the confirmed booking
6. Floating AI chat -> "find hotels in Paris next weekend"
7. (Optional, admin path) Promote your user to admin via
   `python scripts/promote_admin.py <your-email>` against the prod
   `POSTGRES_URL`, then visit `/admin/hotels`.

---

## 4. Troubleshooting

- **502 from gateway**: a downstream service is asleep. Wait ~30s and retry,
  or hit the slow service's `/health` directly to wake it.
- **CORS error in browser**: `CORS_ALLOWED_ORIGINS` on `hbs-gateway` must include
  the exact Vercel origin (no trailing slash).
- **Firebase "auth/unauthorized-domain"**: add your Vercel URL to Firebase ->
  Authentication -> Settings -> Authorized domains.
- **Postgres `DuplicatePreparedStatementError`**: the shared client already
  patches asyncpg with UUID prepared-statement names + `statement_cache_size=0`.
  If you see this in prod, double-check that the Supabase URL ends with the
  transaction pooler (`...pooler.supabase.com`) and not the direct connection.

---

## 5. Next

- **Phase 13** -- warmup pings (cron-job.org) + nightly low-capacity check
  (Google Cloud Scheduler), so the free-tier services do not cold-start
  during the demo.
- **Phase 14** -- final README, ER diagram, demo video.
