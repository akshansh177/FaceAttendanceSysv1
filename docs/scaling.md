# Scaling Guide

Target: **10k employees**, **10M attendance logs**, **~500 concurrent** kiosk/API users.

## Database (MySQL 8)

### Indexes (V2 migration)

- `attendance_summary (employee_id, date)`
- `attendance_logs (employee_id, timestamp)`
- `attendance_corrections (status)`
- `audit_logs (created_at)`

### Partitioning (when volume warrants)

Partition `attendance_logs` by month:

```sql
ALTER TABLE attendance_logs
PARTITION BY RANGE (TO_DAYS(timestamp)) (...);
```

Archive partitions older than retention policy to cold storage.

### Read replicas

For heavy reporting, point read-only report queries to a MySQL replica. Configure connection URL in deploy environment (see `docs/deploy.md`).

## Caching

Dashboard metrics and trends use Redis TTL (120s / 300s). Invalidate or shorten TTL during peak hours if needed.

## Recognition path

Keep recognition on a dedicated service; scale horizontally. Target p95 recognize &lt; 1s.

**FAISS index (backend):** Set `USE_FAISS_INDEX=true`. Rebuilds on startup and after face enroll/delete. Redis pub/sub channel `faiss:index:reload` notifies all backend replicas to reload.

**Pagination & cache:** List APIs use `?page=&page_size=`; entity lists cached in Redis (`cache:departments`, etc.). See [`docs/optimizationplan.md`](optimizationplan.md).

**Background worker:** `docker compose --profile prod up backend-worker` runs cron, 5-minute summary recompute, and async report exports.

**Partitioning:** See `docker/scripts/partition-attendance-logs.sql` for monthly `attendance_logs` partitions (ops-run).

**Pagination:** List APIs use `?page=1&page_size=25` (max 100). See [optimizationplan.md](./optimizationplan.md).

**Export worker:** Use `docker compose --profile worker up` for async report generation.

## Application tier

- Run multiple backend replicas behind NGINX
- Ensure `X-Forwarded-For` / `X-Real-IP` for network attendance validation
- APScheduler nightly jobs: run on a single leader instance or external cron to avoid duplicate emails

## Monitoring

Use Prometheus `/metrics` and Grafana dashboards for API latency, DB pool usage, and recognition errors.
