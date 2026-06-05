# Production Deployment (CloudPanel)

## Prerequisites

- Docker and Docker Compose
- CloudPanel with MySQL 8, Redis, and Nginx already running
- Domain pointing to server with SSL via CloudPanel

## Deploy

```bash
git clone <repo> && cd FaceAttendanceSystem

# Edit apps/backend/.env with your MySQL credentials
# Then:
chmod +x scripts/server-deploy.sh scripts/compose-prod.sh
./scripts/server-deploy.sh
```

Or step by step:

```bash
docker compose down --remove-orphans
docker image prune -f
docker compose up -d --build

# Wait ~10s for backend to start
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

## Containers (4 total)

| Service | Bind | Description |
|---------|------|-------------|
| frontend | `127.0.0.1:6001` | Next.js — CloudPanel proxies `/` here |
| backend | host network `:6002` | FastAPI API |
| recognition | `127.0.0.1:6003` | Face detection (internal) |
| backend-worker | host network | Background jobs (cron, exports) |

**Not in Docker:** MySQL, Redis, Nginx — all provided by CloudPanel host.

## CloudPanel Nginx Vhost

Copy the proxy rules from `docker/cloudpanel/vhost.conf.example` into your site's Nginx config:

- `/` → `http://127.0.0.1:6001` (frontend)
- `/api/` → `http://127.0.0.1:6002` (backend)

## Environment

Edit `apps/backend/.env` only. Docker reads it directly via `env_file`.

| Variable | Example |
|----------|---------|
| `DATABASE_URL` | `mysql+aiomysql://USER:PASS@localhost:3306/DB` |
| `DATABASE_URL_SYNC` | `mysql+pymysql://USER:PASS@localhost:3306/DB` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | `https://your-domain.com` |

URL-encode special characters in passwords (`#` → `%23`, `@` → `%40`). This is required in `DATABASE_URL` / `DATABASE_URL_SYNC`.

The compose file overrides `REDIS_URL` and `RECOGNITION_SERVICE_URL` to `127.0.0.1` for host-network containers.

**Frontend API URL:** In repo root `.env`, set `NEXT_PUBLIC_API_URL=` (empty). Do **not** use comma-separated values or `localhost` in production — rebuild frontend after changing:

```bash
# Fix root .env: NEXT_PUBLIC_API_URL=   (empty line, no localhost)
docker compose build --no-cache frontend
docker compose up -d frontend
```

## Migrations & Seeding

Always run inside Docker:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

## Backups

```bash
mysqldump -h localhost -u USER -p DBNAME > backups/db_$(date +%Y%m%d).sql
```

## Updating

```bash
cd /path/to/FaceAttendanceSystem
./scripts/server-deploy.sh
```

This pulls latest code, rebuilds images, runs migrations, and seeds.

## Face enrollment 500 / 503

Face enrollment calls the **recognition** container on `127.0.0.1:6003`. Check:

```bash
docker compose ps
curl -s http://127.0.0.1:6003/health
docker compose logs recognition --tail 50
docker compose logs backend --tail 50
```

If recognition is down or still loading models:

```bash
docker compose up -d recognition
docker compose restart backend
```

First startup may take 1–2 minutes while InsightFace downloads `buffalo_l` weights.

**`curl detect-embed` returns `HTTP 000`:** the recognition container likely **crashed** (OOM on small VPS) or the test image is invalid. Check:

```bash
ls -la /tmp/test.jpg && file /tmp/test.jpg
docker compose ps recognition
docker compose logs recognition --tail 30
free -h
```

Rebuild recognition after pulling latest (pre-bakes model, lower memory `det_size=320`):

```bash
docker compose build --no-cache recognition
docker compose up -d recognition
curl -s http://127.0.0.1:6003/health   # should show "model":"insightface"
```

If `git pull` fails or Alembic errors on `%23` in the password, run:

```bash
chmod +x scripts/server-fix-migrations.sh
./scripts/server-fix-migrations.sh
```

Or manually:

```bash
git stash
git pull origin main
docker compose build --no-cache backend
docker compose up -d backend
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```
