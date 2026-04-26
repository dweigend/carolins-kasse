#!/bin/bash
set -euo pipefail

DB_PATH="${CAROLINS_KASSE_DB_PATH:-/var/lib/carolins-kasse/kasse.db}"
BACKUP_DIR="${CAROLINS_KASSE_BACKUP_DIR:-/var/backups/carolins-kasse}"
KEEP_BACKUPS="${CAROLINS_KASSE_KEEP_BACKUPS:-30}"

if [ ! -f "${DB_PATH}" ]; then
    echo "Database not found: ${DB_PATH}"
    exit 0
fi

install -d -m 0750 "${BACKUP_DIR}"
timestamp="$(date +%Y%m%d-%H%M%S)"
backup_path="${BACKUP_DIR}/kasse-${timestamp}.db"

sqlite3 "${DB_PATH}" ".backup '${backup_path}'"
chmod 0640 "${backup_path}"
echo "Created backup: ${backup_path}"

mapfile -t backups < <(find "${BACKUP_DIR}" -maxdepth 1 -name 'kasse-*.db' -type f | sort)
remove_count=$((${#backups[@]} - KEEP_BACKUPS))
if [ "${remove_count}" -gt 0 ]; then
    printf '%s\n' "${backups[@]:0:${remove_count}}" | xargs rm -f
fi
