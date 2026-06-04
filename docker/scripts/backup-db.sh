#!/bin/bash
set -euo pipefail

# Backup external MySQL (run on the host where mysqldump is installed).
# For optional Compose MySQL: docker compose --profile mysql-docker exec ...

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-90}"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

DB_HOST="${MYSQL_HOST:-localhost}"
DB_USER="${MYSQL_USER:-acspluserattendance}"
DB_NAME="${MYSQL_DATABASE:-attendanceacspl}"

if docker compose ps mysql 2>/dev/null | grep -q "Up"; then
  DB_PASS="${MYSQL_PASSWORD:-changeme}"
  docker compose exec -T mysql mysqldump -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}_${DATE}.sql"
else
  echo "Using host mysqldump against ${DB_HOST}..."
  mysqldump -h "$DB_HOST" -u "$DB_USER" -p "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}_${DATE}.sql"
fi

echo "Backup saved: $BACKUP_DIR/${DB_NAME}_${DATE}.sql"
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql" -mtime +$RETENTION_DAYS -delete
echo "Pruned backups older than $RETENTION_DAYS days"
