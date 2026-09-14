#!/bin/bash
set -e
BACKUP_DIR=/home/projects/smcpe/backups
LATEST=$(ls -t "$BACKUP_DIR"/smcpe-*.tgz 2>/dev/null | head -1)
if [ -z "$LATEST" ]; then
  echo "No backup found in $BACKUP_DIR"
  exit 1
fi
echo "Restoring from $LATEST"
TMPDIR=$(mktemp -d)
tar xzf "$LATEST" -C "$TMPDIR"
DBFILE=$(find "$TMPDIR" -name "*.db" | head -1)
if [ -z "$DBFILE" ]; then
  echo "No db file in backup"
  exit 1
fi
echo "Integrity check:"
sqlite3 "$DBFILE" "PRAGMA integrity_check;"
echo "Restore test OK: $DBFILE"
ls -lh "$DBFILE"
