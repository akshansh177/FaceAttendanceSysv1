# Face Attendance Management System

Self-hosted employee attendance platform with face recognition, shift management, reporting, and analytics.

## Stack

- **Frontend:** Next.js 15, TypeScript, Tailwind, ShadCN UI, TanStack Query
- **Backend:** FastAPI, MySQL 8, Redis
- **Recognition:** InsightFace (primary)
- **Deploy:** Docker Compose on aaPanel (host Nginx/Redis/MySQL)

## Quick start (development)

```bash
# One-time setup (venvs, deps, Redis)
chmod +x scripts/dev-*.sh
./scripts/dev-setup.sh

# Edit apps/backend/.env — set DATABASE_URL for your MySQL
cd apps/backend && source .venv/bin/activate
alembic upgrade head && python -m app.seed
```

Use **3 terminals** (do not use conda base `uvicorn`):

```bash
./scripts/dev-backend.sh      # :6002 — uses apps/backend/.venv
./scripts/dev-recognition.sh  # :6003 — uses apps/recognition-service/.venv
./scripts/dev-frontend.sh     # :6001
```

Optional Redis for background jobs: `docker compose -f docker-compose.dev.yml up -d`

| Service | Port | Directory |
|---------|------|-----------|
| Frontend | 6001 | `apps/frontend` |
| Backend | 6002 | `apps/backend` |
| Recognition | 6003 | `apps/recognition-service` |

Default admin: `admin@company.com` / `Admin123!`

## Production (aaPanel)

Only 4 Docker containers — aaPanel provides MySQL, Redis, and Nginx.

```bash
cd /www/wwwroot/FaceAttendanceSysv1
# Edit apps/backend/.env with production DB credentials
chmod +x scripts/server-deploy.sh
./scripts/server-deploy.sh
```

See [docs/deploy.md](docs/deploy.md) for aaPanel Nginx reverse proxy, SSL, and troubleshooting.

## Project structure

```
apps/frontend            Next.js UI
apps/backend             FastAPI API + attendance engine
apps/recognition-service Face detection & embeddings
docker/aapanel           aaPanel Nginx vhost example
docs/                    Deployment guides
```
