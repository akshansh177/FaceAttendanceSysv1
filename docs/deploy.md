# Production Deployment

## Prerequisites

- Docker and Docker Compose
- Domain name with DNS pointing to your server
- TLS certificates (Let's Encrypt recommended)

## Deploy

**MySQL:** Use an existing MySQL 8 server (recommended). The Compose file does **not** start MySQL in `dev`/`prod` profiles.

```bash
# CloudPanel / MySQL on same host (recommended — avoids host.docker.internal timeout)
chmod +x scripts/server-setup-env.sh scripts/server-deploy.sh
./scripts/server-setup-env.sh --force --cloudpanel
docker compose -f docker-compose.yml -f docker-compose.cloudpanel.yml --profile prod up -d --build
docker compose -f docker-compose.yml -f docker-compose.cloudpanel.yml exec backend alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.cloudpanel.yml exec backend python -m app.seed

# Or one-shot: ./scripts/server-deploy.sh
```

**Non-CloudPanel** (MySQL accepts TCP from Docker bridge):

```bash
./scripts/server-setup-env.sh --force
docker compose --profile prod up -d --build
```

Recognition Docker image uses a multi-stage build with `g++` for InsightFace. **DeepFace is not installed by default** (avoids a 600MB+ TensorFlow download). Kiosk and enrollment work via InsightFace. For portal gray-zone DeepFace verify, set recognition `dockerfile: Dockerfile.deepface` in `docker-compose.yml` and rebuild.

If `docker compose build` still shows `Dockerfile: 369B`, `deepface` on line 8, or `g++ failed`, the server has **old files** (git pull blocked). From repo root:

```bash
git stash push -m local -u docker-compose.yml   # if pull was rejected
git pull origin main
chmod +x scripts/server-fix-docker-build.sh
./scripts/server-fix-docker-build.sh
```

Or download fixed files only: `curl` lines in `scripts/server-fix-docker-build.sh`, then `docker compose build --no-cache recognition`.

Optional Compose MySQL only: `docker compose --profile mysql-docker up -d mysql`

Services:

| Service | Port | Description |
|---------|------|-------------|
| NGINX | 80, 443 | Reverse proxy |
| Frontend | 6001 (internal) | Next.js |
| Backend | 6002 (internal) | FastAPI |
| Recognition | 6003 (internal) | Face service |
| Prometheus | internal only | Metrics (no host port — avoids conflicts) |
| Grafana | internal only | Dashboards |

## TLS with Let's Encrypt

1. Place certificates in `docker/nginx/certs/fullchain.pem` and `privkey.pem`
2. Update `docker/nginx/nginx.conf` server_name to your domain
3. Reload NGINX: `docker compose exec nginx nginx -s reload`

## Database

V2 uses **MySQL 8** on your server (external). Set credentials in **root `.env`** and **`apps/backend/.env`**:

| Variable | Example |
|----------|---------|
| `MYSQL_DATABASE` | `attendanceacspl` |
| `MYSQL_USER` | `acspluserattendance` |
| `MYSQL_PASSWORD` | plain password (for Docker MySQL init) |
| `DATABASE_URL` | `mysql+aiomysql://USER:URL_ENCODED_PASS@localhost:3306/DB` |
| `DATABASE_URL_SYNC` | `mysql+pymysql://USER:URL_ENCODED_PASS@localhost:3306/DB` |

**Local API** (`uvicorn` from `apps/backend`): edit **`apps/backend/.env`** with the same `DATABASE_URL` lines (host `localhost`).

**Docker API** (containers): set `DATABASE_URL_DOCKER` / `DATABASE_URL_SYNC_DOCKER` in **repo root `.env`**.

**CloudPanel (same server as MySQL):** use `docker-compose.cloudpanel.yml` so backend uses **host network** and `localhost:3306`. Run `./scripts/server-setup-env.sh --force --cloudpanel`. Requires host Redis on `127.0.0.1:6379` (CloudPanel default).

**Other hosts:** use `host.docker.internal` in `*_DOCKER` URLs; MySQL must listen on `0.0.0.0` or the Docker bridge IP, not only `127.0.0.1`.

If you see `Can't connect to MySQL server on 'host.docker.internal'` or timeout on `172.17.0.1:3306`, switch to the CloudPanel compose override above.

If backend logs show `Could not parse SQLAlchemy URL from string ''`, run `./scripts/server-setup-env.sh` or add `DATABASE_URL_DOCKER` to root `.env`, then recreate backend.

If Redis fails with `address already in use` on port 6379, the compose Redis service no longer binds host port 6379 (uses internal network only). Run `docker compose --profile prod up -d redis`.

**Seed / migrations** (always inside Docker, not host `python3`):

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

**No MySQL container:** `docker compose` `dev`/`prod` profiles only start redis, backend, recognition, etc.

URL-encode special characters in passwords inside connection URLs (`#` → `%23`, `@` → `%40`).

Connection strings:

- Async API: `mysql+aiomysql://user:pass@mysql:3306/dbname`
- Alembic: `mysql+pymysql://...` (uses `DATABASE_URL_SYNC` from env)

For high load, add a MySQL read replica and route report queries to it via a separate `DATABASE_URL_READ` (application support as needed).

## Backups

Daily database backup (mysqldump on host, not via mysql container):

```bash
mysqldump -h localhost -u acspluserattendance -p attendanceacspl > backups/attendanceacspl_$(date +%Y%m%d).sql
```

Or use `./docker/scripts/backup-db.sh` only if you run the optional `mysql-docker` profile.

Retention: 90 days (configure in script). Weekly full volume snapshot recommended.

## Restore

```bash
./docker/scripts/restore-db.sh backups/attendance_YYYYMMDD_HHMMSS.sql
```

## Monitoring

- Prometheus: http://your-host:9090
- Grafana: http://your-host:3001 (default admin/admin — change immediately)
- Health: `GET /health` on backend and recognition services

## Public kiosk

- Expose `/kiosk` on the frontend (no auth).
- Provision each device in **Kiosks** admin; store API key on the device only.
- Optional: restrict NGINX `location /api/kiosk` to office VLAN.
- Recognition service must expose `POST /liveness-check` (port 6003).

## Rate limits

Login: 10/min per identifier. Kiosk recognize: 60/min per IP+device. Tune in backend `rate_limit.py`.
