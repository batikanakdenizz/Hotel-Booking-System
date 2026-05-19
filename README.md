# Hotel Booking System

A microservice-based hotel booking platform built for **SE 4458 Software Architecture & Design of Modern Large Scale Systems — Final Project, Group 1**.

> **Status:** 🚧 Phase 0 — Scaffold (in progress). See [`docs/developing_process.md`](docs/developing_process.md) for the implementation journal.

---

## Overview

Seven backend microservices + a React frontend + an AI chat agent, all reachable through a single API gateway.

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 (async) · Pydantic v2 |
| Frontend | Vite · React 19 · TypeScript · Tailwind v4 · shadcn/ui |
| Auth | Firebase Authentication |
| Datastores | Supabase Postgres · MongoDB Atlas · Upstash Redis |
| Queue | CloudAMQP RabbitMQ |
| AI | Groq (Llama 3.3 70B) via MCP tools |
| Hosting | Render (backend) · Vercel (frontend) · Google Cloud Scheduler (cron) |

---

## Services

| Service | Port (local) | Responsibility |
|---|---|---|
| `gateway` | 8080 | Single entry point, JWT verification, rate limiting, CORS |
| `admin-service` | 8001 | Hotel + Room CRUD + availability management (admin-only) |
| `search-service` | 8002 | Date-range search, hotel-detail Redis cache, 15% discount logic |
| `booking-service` | 8003 | Transactional booking, durable RabbitMQ publish |
| `comments-service` | 8004 | MongoDB comments + 5-dimensional rating aggregation |
| `notification-service` | 8005 | RabbitMQ consumer (emails) + nightly low-capacity check |
| `ai-agent-service` | 8006 | Chat endpoint using MCP tools (search + book + comments) |

---

## Documentation

- [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) — full project plan (English, primary source)
- [`docs/PROJECT_PLAN_TR.md`](docs/PROJECT_PLAN_TR.md) — Turkish translation for reference
- [`docs/developing_process.md`](docs/developing_process.md) — implementation journal (Turkish, learning-focused)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — ER diagram + design decisions (added in Phase 14)
- [`docs/Guide/Final_Guideline.pdf`](docs/Guide/Final_Guideline.pdf) — assignment specification (primary source)

---

## Local Development (after Phase 0)

```bash
# Copy env template
cp .env.example .env
# (fill in real values from Phase 1 external services setup)

# Start the full local stack
docker compose -f infrastructure/docker-compose.yml up

# Health checks
curl http://localhost:8080/health
curl http://localhost:8001/health
# ... etc for each service

# Frontend dev server
cd frontend
npm install
npm run dev    # http://localhost:5173
```

---

## Deliverables Checklist

This section will be completed at Phase 14. See [`PROJECT_PLAN.md §17`](docs/PROJECT_PLAN.md).

- [ ] Public GitHub repository link
- [ ] Deployed URLs (frontend + gateway)
- [ ] Design rationale + assumptions + issues encountered
- [ ] Data models (ER diagram)
- [ ] Demo video link (≤ 5 min)

---

## License

MIT
