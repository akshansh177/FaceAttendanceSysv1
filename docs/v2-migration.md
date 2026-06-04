# V2 Migration Guide (V1 PostgreSQL → V2 MySQL)

V2 uses a **fresh MySQL database**. Existing PostgreSQL data is not migrated automatically.

## Steps for developers

1. Stop V1 PostgreSQL containers if running:
   ```bash
   docker compose down
   ```

2. Copy environment:
   ```bash
   cp .env.example .env
   cp apps/backend/.env.example apps/backend/.env  # if present, or edit apps/backend/.env
   ```
   Ensure `DATABASE_URL` and `DATABASE_URL_SYNC` use `mysql+aiomysql` / `mysql+pymysql`.

3. Start MySQL and Redis:
   ```bash
   docker compose --profile dev up -d mysql redis
   ```

4. Run migrations (use **002** only for new installs):
   ```bash
   cd apps/backend
   source .venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   python -m app.seed
   ```

5. Re-enroll face embeddings if needed (embeddings are not DB-portable between engines in dev).

6. Register kiosk devices in **Devices** admin and approve them when using device enforcement.

## Alembic note

- `alembic/versions/001_initial.py` — legacy PostgreSQL schema (deprecated).
- `alembic/versions/002_v2_mysql_initial.py` — full V2 MySQL schema (`down_revision: None`).

On a clean V2 install, only `002` is applied.

## Backup / restore

```bash
./docker/scripts/backup-db.sh
./docker/scripts/restore-db.sh backups/attendance_YYYYMMDD_HHMMSS.sql
```

Uses `mysqldump` / `mysql` against the `mysql` compose service.
