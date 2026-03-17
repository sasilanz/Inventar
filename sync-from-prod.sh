#!/bin/bash
# Prod-DB (dietipi) → lokale Test-DB synchronisieren
# Inklusive optionalem Medien-Sync
#
# Usage:
#   ./sync-from-prod.sh          # nur DB
#   ./sync-from-prod.sh --media  # DB + Medien

set -euo pipefail

PROD_HOST="dietipi"
PROD_USER="pi"
PROD_DIR="/home/pi/Inventar"
PROD_DB_CONTAINER="inventardb-db"
PROD_DB_USER="inventardb"
PROD_DB_NAME="inventardb"

LOCAL_DB_CONTAINER="inventardb-db"
SYNC_MEDIA=false

if [[ "${1:-}" == "--media" ]]; then
  SYNC_MEDIA=true
fi

echo "=== Inventar: Prod → Test Sync ==="
echo "Prod: $PROD_HOST ($PROD_DIR)"
echo ""

# 1. DB-Dump von Prod holen
echo "[1/3] DB-Dump von Prod..."
ssh "$PROD_HOST" "docker exec $PROD_DB_CONTAINER pg_dump -U $PROD_DB_USER $PROD_DB_NAME" \
  > /tmp/inventar-prod-dump.sql
echo "      ✓ Dump erhalten ($(du -sh /tmp/inventar-prod-dump.sql | cut -f1))"

# 2. Lokale DB ersetzen
echo "[2/3] Lokale DB ersetzen..."
docker exec -i "$LOCAL_DB_CONTAINER" psql -U "$PROD_DB_USER" -c \
  "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" "$PROD_DB_NAME" > /dev/null
docker exec -i "$LOCAL_DB_CONTAINER" psql -U "$PROD_DB_USER" "$PROD_DB_NAME" \
  < /tmp/inventar-prod-dump.sql > /dev/null
rm /tmp/inventar-prod-dump.sql
echo "      ✓ DB importiert"

# 3. Medien (optional)
if $SYNC_MEDIA; then
  echo "[3/3] Medien synchronisieren..."
  MEDIA_SRC="$PROD_HOST:$PROD_DIR/app/media/"
  MEDIA_DST="/home/asiarch/dev/Inventar/app/media/"
  rsync -az --delete "$MEDIA_SRC" "$MEDIA_DST"
  echo "      ✓ Medien synchronisiert"
else
  echo "[3/3] Medien übersprungen (--media um zu synchronisieren)"
fi

echo ""
echo "=== Sync abgeschlossen ==="
