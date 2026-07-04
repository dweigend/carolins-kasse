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

previous_commit=""
rollback_on_failure=0

git_for_app() {
    runuser -u "${APP_USER}" -- git -C "${APP_DIR}" "$@"
}

run_uv_sync() {
    runuser -u "${APP_USER}" -- bash -c \
        'cd "$1" && "$2" sync --frozen --no-dev' \
        bash "${APP_DIR}" "${UV_BIN}"
}

run_app_python() {
    runuser -u "${APP_USER}" -- env CAROLINS_KASSE_DB_PATH="${DB_PATH}" bash -c \
        'cd "$1" && shift && .venv/bin/python "$@"' \
        bash "${APP_DIR}" "$@"
}

restart_kiosk() {
    echo "Restarting kiosk service."
    if systemctl restart carolins-kasse.service; then
        echo "Kiosk service restart requested."
    else
        echo "Kiosk service restart failed; check systemctl status carolins-kasse.service." >&2
    fi
}

rollback_checkout() {
    local current_commit

    if [ -z "${previous_commit}" ]; then
        echo "No previous commit was recorded; leaving kiosk stopped for manual recovery." >&2
        return 1
    fi

    current_commit="$(git_for_app rev-parse HEAD 2>/dev/null || true)"
    if [ "${current_commit}" = "${previous_commit}" ]; then
        echo "Checkout is already at ${previous_commit}; resetting source checkout to discard post-pull changes."
    else
        echo "Rolling back source checkout from ${current_commit:-unknown} to ${previous_commit}."
    fi

    if git_for_app reset --hard "${previous_commit}"; then
        echo "Rollback completed."
        return 0
    fi

    echo "Rollback command failed." >&2
    return 1
}

cleanup() {
    local exit_status=$?
    local rollback_status

    trap - EXIT
    set +e

    if [ "${exit_status}" -ne 0 ] && [ "${rollback_on_failure}" -eq 1 ]; then
        rollback_checkout
        rollback_status=$?
        if [ "${rollback_status}" -ne 0 ]; then
            echo "Leaving kiosk service stopped so it does not start a half-validated checkout." >&2
            exit "${exit_status}"
        fi
    fi

    restart_kiosk
    exit "${exit_status}"
}

trap cleanup EXIT

echo "Stopping kiosk service for update."
systemctl stop carolins-kasse.service || true
echo "Creating database backup before update."
"${APP_DIR}/tools/pi_backup.sh"

dirty_status="$(git_for_app status --porcelain --untracked-files=no)"
if [ -n "${dirty_status}" ]; then
    echo "Source checkout has local changes. Refusing to update:"
    echo "${dirty_status}"
    exit 1
fi

previous_commit="$(git_for_app rev-parse HEAD)"
echo "Current checkout before update: ${previous_commit}"

git_for_app fetch origin
rollback_on_failure=1
git_for_app pull --ff-only
updated_commit="$(git_for_app rev-parse HEAD)"
echo "Checkout after pull: ${updated_commit}"

run_uv_sync
run_app_python -m compileall src tools

set +e
run_app_python tools/seed_database.py
seed_status=$?
set -e
if [ "${seed_status}" -ne 0 ] && [ "${seed_status}" -ne 1 ]; then
    exit "${seed_status}"
fi

run_app_python tools/generate_barcodes.py
run_app_python tools/generate_printables.py

rollback_on_failure=0
echo "Update finished at $(date --iso-8601=seconds)"
