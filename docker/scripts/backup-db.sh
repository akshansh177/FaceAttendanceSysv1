#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-90}"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

docker compose exec -T mysql mysqldump -u attendance -pattendance attendance > "$BACKUP_DIR/attendance_${DATE}.sql"
echo "Backup saved: $BACKUP_DIR/attendance_${DATE}.sql"

find "$BACKUP_DIR" -name "attendance_*.sql" -mtime +$RETENTION_DAYS -delete
echo "Pruned backups older than $RETENTION_DAYS days"
