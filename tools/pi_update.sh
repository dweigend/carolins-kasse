#!/bin/bash
set -euo pipefail

APP_USER="${CAROLINS_KASSE_USER:-kasse}"
APP_DIR="${CAROLINS_KASSE_APP_DIR:-/opt/carolins-kasse}"
DB_PATH="${CAROLINS_KASSE_DB_PATH:-/var/lib/carolins-kasse/kasse.db}"
BACKUP_DIR="${CAROLINS_KASSE_BACKUP_DIR:-/var/backups/carolins-kasse}"
UV_BIN="${CAROLINS_KASSE_UV_BIN:-/usr/local/bin/uv}"

if [ "$(id -u)" -ne 0 ]; then
    echo "Update must run as root."
    exit 1
fi

export CAROLINS_KASSE_DB_PATH="${DB_PATH}"
export CAROLINS_KASSE_BACKUP_DIR="${BACKUP_DIR}"

restart_kiosk() {
    systemctl restart carolins-kasse.service || true
}

trap restart_kiosk EXIT

systemctl stop carolins-kasse.service || true
"${APP_DIR}/tools/pi_backup.sh"

dirty_status="$(runuser -u "${APP_USER}" -- git -C "${APP_DIR}" status --porcelain --untracked-files=no)"
if [ -n "${dirty_status}" ]; then
    echo "Source checkout has local changes. Refusing to update:"
    echo "${dirty_status}"
    exit 1
fi

runuser -u "${APP_USER}" -- git -C "${APP_DIR}" fetch origin
runuser -u "${APP_USER}" -- git -C "${APP_DIR}" pull --ff-only
runuser -u "${APP_USER}" -- bash -lc "cd '${APP_DIR}' && '${UV_BIN}' sync --frozen --no-dev"
runuser -u "${APP_USER}" -- env CAROLINS_KASSE_DB_PATH="${DB_PATH}" bash -lc \
    "cd '${APP_DIR}' && .venv/bin/python -m compileall src tools"

set +e
runuser -u "${APP_USER}" -- env CAROLINS_KASSE_DB_PATH="${DB_PATH}" bash -lc \
    "cd '${APP_DIR}' && .venv/bin/python tools/seed_database.py"
seed_status=$?
set -e
if [ "${seed_status}" -ne 0 ] && [ "${seed_status}" -ne 1 ]; then
    exit "${seed_status}"
fi

runuser -u "${APP_USER}" -- env CAROLINS_KASSE_DB_PATH="${DB_PATH}" bash -lc \
    "cd '${APP_DIR}' && .venv/bin/python tools/generate_barcodes.py"
runuser -u "${APP_USER}" -- env CAROLINS_KASSE_DB_PATH="${DB_PATH}" bash -lc \
    "cd '${APP_DIR}' && .venv/bin/python tools/generate_printables.py"

echo "Update finished at $(date --iso-8601=seconds)"
