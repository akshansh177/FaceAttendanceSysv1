# Production Deployment (aaPanel)

## Prerequisites

- Docker and Docker Compose installed on the server
- **aaPanel** with MySQL 8, Redis, and Nginx (install Redis from aaPanel **App Store** if missing)
- Domain pointing to server with SSL via aaPanel

Typical aaPanel paths: site files `/www/wwwroot/your-domain`, project e.g. `/www/wwwroot/FaceAttendanceSysv1`.

## Deploy

```bash
cd /www/wwwroot/FaceAttendanceSysv1

# Edit apps/backend/.env with your MySQL credentials
chmod +x scripts/server-deploy.sh
./scripts/server-deploy.sh
```

Or step by step:

```bash
docker compose down --remove-orphans
docker image prune -f
docker compose up -d --build

sleep 10
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

## Containers (4 total)

| Service | Bind | Description |
|---------|------|-------------|
| frontend | `127.0.0.1:6001` | Next.js — aaPanel Nginx proxies `/` here |
| backend | host network `:6002` | FastAPI API |
| recognition | `127.0.0.1:6003` | Face detection (internal) |
| backend-worker | host network | Background jobs |

**Not in Docker:** MySQL, Redis, Nginx — provided by aaPanel on the host.

## aaPanel Nginx reverse proxy

1. **Website** → select your site → **Settings** → **Configuration** (Conf)
2. Add proxy rules from `docker/aapanel/vhost.conf.example`:
   - `/` → `http://127.0.0.1:6001` (frontend)
   - `/api/` → `http://127.0.0.1:6002` (backend)
3. Set `client_max_body_size 50M` and `proxy_read_timeout 300s` (needed for face enrollment uploads)
4. **SSL** → Let's Encrypt → apply certificate
5. Copy the same `location` blocks into the `:443` server block
6. Save and reload Nginx

**Alternative in aaPanel:** Site → **Reverse Proxy** → add two rules:
- Path `/api` → `http://127.0.0.1:6002`
- Path `/` → `http://127.0.0.1:6001`

## Environment

Edit `apps/backend/.env` only. Docker reads it via `env_file`.

| Variable | Example |
|----------|---------|
| `DATABASE_URL` | `mysql+aiomysql://USER:PASS@localhost:3306/DB` |
| `DATABASE_URL_SYNC` | `mysql+pymysql://USER:PASS@localhost:3306/DB` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | `https://attendance.akshansh.site` |

URL-encode special characters in passwords (`#` → `%23`, `@` → `%40`).

**Frontend API URL:** In repo root `.env`, set `NEXT_PUBLIC_API_URL=` (empty). Rebuild frontend after changing:

```bash
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

Use aaPanel **Database** → Backup, or:

```bash
mysqldump -h localhost -u USER -p DBNAME > backups/db_$(date +%Y%m%d).sql
```

## Updating

```bash
cd /www/wwwroot/FaceAttendanceSysv1
./scripts/server-deploy.sh
```

## Face enrollment 500 / 503

Face enrollment calls the **recognition** container on `127.0.0.1:6003`:

```bash
docker compose ps
curl -s http://127.0.0.1:6003/health
docker compose logs recognition --tail 50
docker compose logs backend --tail 50
free -h
```

Rebuild recognition (pre-bakes model, lower memory):

```bash
docker compose build --no-cache recognition
docker compose up -d recognition
curl -s http://127.0.0.1:6003/health   # should show "model":"insightface"
```

If Alembic fails on `%23` in password:

```bash
chmod +x scripts/server-fix-migrations.sh
./scripts/server-fix-migrations.sh
```
