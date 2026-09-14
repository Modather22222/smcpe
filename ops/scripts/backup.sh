#!/bin/bash
set -e
DATE=$(date +%Y%m%d-%H%M)
DB_PATH=${DB_PATH:-/home/projects/smcpe/backend/db/smcpe.db}
BACKUP_DIR=/home/projects/smcpe/backups
TMP_DB=/tmp/smcpe-$DATE.db

mkdir -p "$BACKUP_DIR"
if [ ! -f "$DB_PATH" ]; then
  echo "DB not found at $DB_PATH, skipping backup"
  exit 0
fi
echo "Backing up $DB_PATH -> $TMP_DB"
sqlite3 "$DB_PATH" ".backup $TMP_DB"
tar czf "$BACKUP_DIR/smcpe-$DATE.tgz" -C /tmp "smcpe-$DATE.db" 2>/dev/null || tar czf "$BACKUP_DIR/smcpe-$DATE.tgz" "$TMP_DB"
# Also include flat files if exist
if [ -d /home/projects/smcpe/backend/data/runs ]; then
  tar czf "$BACKUP_DIR/smcpe-runs-$DATE.tgz" -C /home/projects/smcpe/backend data/runs 2>/dev/null || true
fi
find "$BACKUP_DIR" -name "smcpe-*.tgz" -mtime +7 -delete 2>/dev/null || true
echo "Backup done: $BACKUP_DIR/smcpe-$DATE.tgz"
ls -lh "$BACKUP_DIR" | tail -5
