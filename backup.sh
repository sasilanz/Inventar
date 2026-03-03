#!/bin/bash
# InventarDB Backup – DB + Medien
# Läuft via Cron, behält die letzten 14 Backups

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
TARGET="$BACKUP_DIR/$TIMESTAMP"
KEEP=14

mkdir -p "$TARGET"

# 1. PostgreSQL Dump
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T db \
    pg_dump -U inventardb inventardb > "$TARGET/inventardb.sql"

# 2. Medien
docker compose -f "$SCRIPT_DIR/docker-compose.yml" cp \
    app:/app/app/media "$TARGET/media"

# 3. Alte Backups löschen (mehr als $KEEP behalten)
ls -1dt "$BACKUP_DIR"/*/  | tail -n +$((KEEP + 1)) | xargs -r rm -rf

echo "[$TIMESTAMP] Backup OK → $TARGET"
