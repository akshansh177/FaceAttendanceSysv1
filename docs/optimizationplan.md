# Face Attendance System — Optimization Plan

## Objectives

Optimize for: recognition accuracy, recognition speed, database performance, scalability, security, UX, and infrastructure cost.

**Scale targets:** 10,000+ employees · 1M+ attendance records · recognition &lt; 1s · dashboard load &lt; 2s

## Performance SLOs

| Metric | Target |
|--------|--------|
| Recognition time | &lt; 800 ms (p95) |
| Face match accuracy | &gt; 97% (with tuned threshold + quality gates) |
| Dashboard load | &lt; 2 s |
| Attendance save | &lt; 300 ms |
| Report generation (cached) | &lt; 5 s |
| System availability | 99.9% |
| Concurrent users | 500+ |

**Service ports (local):** Frontend 6001 · Backend 6002 · Recognition 6003

---

## Implementation status

| Phase | Focus | Status |
|-------|--------|--------|
| 1 | FAISS index, enrollment quality, match margin, metrics | Implemented |
| 2 | Kiosk offline queue, camera recovery, lean route | Implemented |
| 3 | DB indexes, unique summary constraint, partition runbook | Implemented |
| 4 | Redis entity cache, pagination, dashboard invalidation | Implemented |
| 5 | 5-min summary job, cron leader lock | Implemented |
| 6 | Report cache, async export queue | Implemented |
| 7 | Lazy charts, SSE live feed, paginated lists | Implemented |
| 8 | Threshold presets, audit expansion, middleware guard | Implemented |
| 9 | Multi-recognition compose, worker profile, Grafana stub | Implemented |
| 10 | Policy/RBAC Redis cache, multi-branch filters | Implemented |

---

## Phase 1: Face recognition

- **Embeddings:** Fernet-encrypted in MySQL; optional **FAISS** `IndexFlatIP` in memory (`USE_FAISS_INDEX=true`).
- **Matching:** Top-K search → per-employee max cosine score → threshold + **match margin**.
- **Enrollment:** Min det score, blur variance, reject `fallback` model embeddings.
- **Liveness:** Multi-frame heuristics on kiosk (recognition service).

## Phase 2: Kiosk

- Dedicated `/kiosk` route and API client.
- **IndexedDB** offline queue + `client_event_id` dedup.
- Camera **auto-recovery** on track end.

## Phase 3: Database

- Alembic `004_performance`: summary date index, unique `(employee_id, date)`.
- Partitioning SQL in `docker/scripts/partition-attendance-logs.sql` (ops-run).

## Phase 4: API

- Redis cache for reference data; invalidate on CRUD.
- `page` / `page_size` (max 100) on employees and audit.
- Dashboard cache invalidation on punch.

## Phase 5: Attendance engine

- `attendance_summary` updated on punch; **5-minute** recompute job.
- **Redis leader lock** for schedulers across replicas.

## Phase 6: Reporting

- Redis report cache keys.
- Async export via Redis queue + `GET /api/reports/jobs/{id}`.

## Phase 7: Frontend

- Dynamic Recharts; React Query caching.
- **SSE** live feed stream.
- Paginated employees table support.

## Phase 8: Security

- JWT + refresh; encrypted embeddings; audit logs.
- Match threshold presets in attendance settings.
- Next.js middleware redirects unauthenticated dashboard routes.

## Phase 9: Infrastructure

- Docker Compose profiles; Prometheus metrics.
- Optional `backend-worker` service for jobs.
- Grafana dashboard JSON under `docker/grafana/dashboards/`.

## Phase 10: Enterprise

- Policy cache in Redis.
- RBAC permission cache per user session.

---

See also: [scaling.md](./scaling.md) · [deploy.md](./deploy.md)
