# Face Attendance Management System

Self-hosted employee attendance platform with face recognition, shift management, reporting, and analytics.

## Stack

- **Frontend:** Next.js 15, TypeScript, Tailwind, ShadCN UI, TanStack Query
- **Backend:** FastAPI, MySQL 8, Redis
- **Recognition:** InsightFace (primary), DeepFace (fallback)
- **Deploy:** Docker Compose, NGINX, Prometheus, Grafana

## Quick start (development)

Requires **Python 3.9+** locally (3.12 in Docker). Run commands from the repo root unless noted.

```bash
cp .env.example .env
docker compose --profile dev up -d mysql redis

# Backend (run from apps/backend)
cd apps/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 6002

# Recognition (optional for face features)
cd apps/recognition-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 6003

# Frontend (http://localhost:6001)
cd apps/frontend
npm install
npm run dev
```

Default admin: `admin@company.com` / `Admin123!`

## V3 features

- **Public kiosk** at `/kiosk` with liveness, voice feedback, auto check-in/out
- Kiosk management, API keys, live HR feed
- Attendance methods and enterprise policies
- Expanded employee portal (calendar, profile, export)

## V2 features

- MySQL 8, job roles, locations, attendance validation modes, corrections, role dashboards

See [docs/upgrade-v3-kiosk.md](docs/upgrade-v3-kiosk.md), [docs/upgrade.md](docs/upgrade.md), and [docs/v2-migration.md](docs/v2-migration.md).

## Production

```bash
docker compose --profile prod up -d
```

See [docs/deploy.md](docs/deploy.md) for TLS, backups, and monitoring.

## Project structure

```
apps/frontend          Next.js UI
apps/backend           FastAPI API + attendance engine
apps/recognition-service  Face detection & embeddings
packages/shared        Shared TypeScript types
docker/                NGINX, Prometheus, Grafana configs
docs/                  Deployment, V2 migration, scaling
```
