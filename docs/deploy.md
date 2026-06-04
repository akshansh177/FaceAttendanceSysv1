# Production Deployment

## Prerequisites

- Docker and Docker Compose
- Domain name with DNS pointing to your server
- TLS certificates (Let's Encrypt recommended)

## Deploy

```bash
cp .env.example .env
# Edit secrets: JWT_SECRET, JWT_REFRESH_SECRET, EMBEDDING_ENCRYPTION_KEY

docker compose --profile prod up -d --build
```

Services:

| Service | Port | Description |
|---------|------|-------------|
| NGINX | 80, 443 | Reverse proxy |
| Frontend | 6001 (internal) | Next.js |
| Backend | 6002 (internal) | FastAPI |
| Recognition | 6003 (internal) | Face service |
| Prometheus | 9090 | Metrics |
| Grafana | 3001 | Dashboards |

## TLS with Let's Encrypt

1. Place certificates in `docker/nginx/certs/fullchain.pem` and `privkey.pem`
2. Update `docker/nginx/nginx.conf` server_name to your domain
3. Reload NGINX: `docker compose exec nginx nginx -s reload`

## Database

V2 uses **MySQL 8** (`mysql` service in Docker Compose). Connection strings:

- Async API: `mysql+aiomysql://user:pass@mysql:3306/attendance`
- Alembic: `mysql+pymysql://...`

For high load, add a MySQL read replica and route report queries to it via a separate `DATABASE_URL_READ` (application support as needed).

## Backups

Daily database backup (mysqldump):

```bash
./docker/scripts/backup-db.sh
```

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
