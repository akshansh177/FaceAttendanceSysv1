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
