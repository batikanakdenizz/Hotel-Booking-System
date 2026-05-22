# Scheduling Guide — Cron Jobs & Cold-Start Mitigation

The system has two recurring jobs:

1. **Nightly low-availability check** (business logic) — every day at 02:00 UTC
2. **Warmup pings** (cold-start mitigation) — every 10 min during the demo window

Render's free plan sleeps services after 15 min idle and takes ~30s to wake.
For a demo / portfolio site this is acceptable, but the warmup pings keep the
gateway warm enough that the first click does not feel broken.

---

## 1. Nightly low-availability check — Google Cloud Scheduler

The notification-service exposes `POST /trigger/nightly` guarded by an
`X-Cron-Secret` header (see `services/notification-service/app/routers/trigger.py`).

### 1.1 Pick a secret

In your local `.env`, you already have:

```
CRON_SECRET=<some random uuid>
```

The same value must be set in the `hbs-notification-service` env on Render
(see `docs/DEPLOY.md` §1.2).

### 1.2 Create the Cloud Scheduler job

Using the `gcloud` CLI (replace placeholders):

```bash
gcloud scheduler jobs create http hbs-nightly-occupancy \
  --location=europe-west3 \
  --schedule="0 2 * * *" \
  --time-zone="Europe/Istanbul" \
  --uri="https://hbs-notification-service.onrender.com/trigger/nightly" \
  --http-method=POST \
  --headers="X-Cron-Secret=<your CRON_SECRET>,Content-Type=application/json" \
  --message-body='{}' \
  --attempt-deadline=120s
```

Or via Cloud Console UI:

1. https://console.cloud.google.com/cloudscheduler -> **Create Job**
2. Name: `hbs-nightly-occupancy`
3. Frequency: `0 2 * * *` (daily 02:00)
4. Time zone: Europe/Istanbul
5. Target type: HTTP
6. URL: `https://hbs-notification-service.onrender.com/trigger/nightly`
7. HTTP method: POST
8. Body: `{}`
9. Add header: `X-Cron-Secret` = `<your CRON_SECRET>`
10. Save & **Force Run** once to verify -> 200 OK in logs

### 1.3 Verify

Check the notification-service logs on Render — you should see
`nightly_check_started` and `nightly_check_completed` with a summary count.

---

## 2. Warmup pings — cron-job.org (free)

cron-job.org allows free HTTP GET pings every 1+ min, perfect for keeping
free-tier Render services warm.

### 2.1 Sign up & add jobs

1. https://cron-job.org -> Sign up (free)
2. **Create cronjob**

Repeat for each public-facing service URL. Recommend pinging the gateway
only — when the gateway wakes, downstream services wake on first proxied
request. But for a demo with multiple users, ping every service:

| Service | URL |
|---|---|
| Gateway | `https://hbs-gateway.onrender.com/health` |
| Admin | `https://hbs-admin-service.onrender.com/health` |
| Search | `https://hbs-search-service.onrender.com/health` |
| Booking | `https://hbs-booking-service.onrender.com/health` |
| Comments | `https://hbs-comments-service.onrender.com/health` |
| Notification | `https://hbs-notification-service.onrender.com/health` |
| AI Agent | `https://hbs-ai-agent-service.onrender.com/health` |

For each job:

- Title: `hbs-warmup-<service>`
- URL: as above
- Schedule: **Every 10 minutes**, **only during demo days** (toggle on / off as needed)
- Notifications: enable email on failure -> you find out before the demo does

### 2.2 Why 10 min and not 14?

Render says services sleep after **15 min** of inactivity. Pinging every
10 min leaves a comfortable 5-min cushion in case a ping fails or is delayed.

### 2.3 Free-tier ping budget

Render's free plan includes 750 instance-hours per month. Seven services
pinged every 10 min = 7 services running 24/7 = exceeds the budget. **Only
turn on warmup pings during the demo window** (e.g., 24 hours before until
1 hour after the presentation), otherwise leave them off and let the
services sleep.

---

## 3. Alternative: GitHub Actions (no third-party signup)

If you do not want a cron-job.org account, you can run warmup pings as a
GitHub Action. Create `.github/workflows/warmup.yml`:

```yaml
name: Render warmup ping
on:
  schedule:
    - cron: "*/10 * * * *"   # every 10 min
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping gateway
        run: curl -fsS https://hbs-gateway.onrender.com/health
```

GitHub Actions cron has ~5-15 min scheduling delay, so 10-min cadence is the
practical floor. The schedule is also disabled automatically if the repo has
been inactive for 60 days — fine for a demo, not for production.

---

## 4. Verification checklist

- [ ] `CRON_SECRET` matches between Render env and Cloud Scheduler header
- [ ] Force-run the Cloud Scheduler job once -> 200 OK
- [ ] cron-job.org or GitHub Action returns 200 on `/health`
- [ ] After 20 min idle, `curl https://hbs-gateway.onrender.com/health` answers in <2s

---

## 5. Next

Phase 14 — final documentation (README, ER diagram, demo video).
