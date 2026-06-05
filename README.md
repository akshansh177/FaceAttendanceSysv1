# Face Attendance Management System

Self-hosted employee attendance platform with face recognition, shift management, reporting, and analytics.

## Stack

- **Frontend:** Next.js 15, TypeScript, Tailwind, ShadCN UI, TanStack Query
- **Backend:** FastAPI, MySQL 8, Redis
- **Recognition:** InsightFace (primary)
- **Deploy:** Docker Compose on CloudPanel (host Nginx/Redis/MySQL)

## Quick start (development)

```bash
cp .env.example .env
# Edit DATABASE_URL in apps/backend/.env for your MySQL server

# Backend
cd apps/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 6002

# Recognition
cd apps/recognition-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 6003

# Frontend (http://localhost:6001)
cd apps/frontend
npm install && npm run dev
```

Default admin: `admin@company.com` / `Admin123!`

## Production (CloudPanel)

Only 4 Docker containers — host provides MySQL, Redis, Nginx.

```bash
# Edit apps/backend/.env with production DB credentials
chmod +x scripts/server-deploy.sh scripts/compose-prod.sh
./scripts/server-deploy.sh
```

See [docs/deploy.md](docs/deploy.md) for vhost config, backups, and details.

## Project structure

```
apps/frontend            Next.js UI
apps/backend             FastAPI API + attendance engine
apps/recognition-service Face detection & embeddings
docker/                  CloudPanel vhost example
docs/                    Deployment guides
```
