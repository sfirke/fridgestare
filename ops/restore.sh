#!/usr/bin/env bash
# Restore a Fridgestare database dump produced by ops/backup.sh.
#
#   ./ops/restore.sh backups/fridgestare-20260824T030000Z.sql.gz
#
# This overwrites the current contents of the database. It stops the backend first so
# the app cannot write to a half-restored schema.
set -euo pipefail

ARCHIVE="${1:-}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

if [[ -z "$ARCHIVE" || ! -f "$ARCHIVE" ]]; then
  echo "Usage: $0 <backup.sql.gz>" >&2
  exit 1
fi
if [[ ! -f .env ]]; then
  echo "No .env in $(pwd); run this from the deployment directory." >&2
  exit 1
fi

read -r -p "This overwrites the live database from $ARCHIVE. Type 'restore' to continue: " CONFIRM
if [[ "$CONFIRM" != "restore" ]]; then
  echo "Aborted."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

DATABASE="${MARIADB_DATABASE:-fridgestare}"
USERNAME="${MARIADB_USER:-fridgestare}"

docker compose -f "$COMPOSE_FILE" stop backend
gunzip -c "$ARCHIVE" \
  | docker compose -f "$COMPOSE_FILE" exec -T db \
      mariadb --user="$USERNAME" --password="$MARIADB_PASSWORD" "$DATABASE"
docker compose -f "$COMPOSE_FILE" start backend

echo "Restored $ARCHIVE. The backend runs migrations on start, so check its logs:"
echo "  docker compose -f $COMPOSE_FILE logs -f backend"
