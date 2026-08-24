#!/usr/bin/env bash
# Dump the Fridgestare database to a timestamped gzip file and prune old ones.
#
#   ./ops/backup.sh [destination-directory]
#
# Suitable for cron. From the repository directory on the server:
#   0 3 * * * cd /opt/fridgestare && ./ops/backup.sh >> /var/log/fridgestare-backup.log 2>&1
set -euo pipefail

DESTINATION="${1:-./backups}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

if [[ ! -f .env ]]; then
  echo "No .env in $(pwd); run this from the deployment directory." >&2
  exit 1
fi

# Only the database credentials are needed, and .env holds unquoted values.
set -a
# shellcheck disable=SC1091
source .env
set +a

DATABASE="${MARIADB_DATABASE:-fridgestare}"
USERNAME="${MARIADB_USER:-fridgestare}"

mkdir -p "$DESTINATION"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$DESTINATION/fridgestare-$STAMP.sql.gz"

# --single-transaction keeps the dump consistent without locking the app out.
docker compose -f "$COMPOSE_FILE" exec -T db \
  mariadb-dump --single-transaction --quick \
  --user="$USERNAME" --password="$MARIADB_PASSWORD" "$DATABASE" \
  | gzip > "$TARGET"

# A dump that failed mid-stream still leaves a small gzip file behind, so check it.
if ! gzip -t "$TARGET"; then
  echo "Backup $TARGET is corrupt; removing." >&2
  rm -f "$TARGET"
  exit 1
fi

echo "Wrote $TARGET ($(du -h "$TARGET" | cut -f1))"

find "$DESTINATION" -name 'fridgestare-*.sql.gz' -type f -mtime "+$KEEP_DAYS" -delete
echo "Pruned backups older than $KEEP_DAYS days."
