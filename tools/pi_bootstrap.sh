#!/bin/bash
set -euo pipefail

APP_USER="${CAROLINS_KASSE_USER:-kasse}"
APP_GROUP="${CAROLINS_KASSE_GROUP:-kasse}"
APP_DIR="${CAROLINS_KASSE_APP_DIR:-/opt/carolins-kasse}"
REPO_URL="${CAROLINS_KASSE_REPO_URL:-https://github.com/dweigend/carolins-kasse.git}"
DB_PATH="${CAROLINS_KASSE_DB_PATH:-/var/lib/carolins-kasse/kasse.db}"
STATE_DIR="${CAROLINS_KASSE_STATE_DIR:-/var/lib/carolins-kasse}"
BACKUP_DIR="${CAROLINS_KASSE_BACKUP_DIR:-/var/backups/carolins-kasse}"
CONFIG_DIR="${CAROLINS_KASSE_CONFIG_DIR:-/etc/carolins-kasse}"
PIN_PATH="${CAROLINS_KASSE_ADMIN_PIN_PATH:-${CONFIG_DIR}/admin-pin}"
LOG_FILE="${STATE_DIR}/install.log"
UV_BIN="${CAROLINS_KASSE_UV_BIN:-/usr/local/bin/uv}"

export DEBIAN_FRONTEND=noninteractive

if [ "$(id -u)" -ne 0 ]; then
    echo "This installer must run as root."
    exit 1
fi

mkdir -p "${STATE_DIR}"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "Starting Carolin's Kasse bootstrap at $(date --iso-8601=seconds)"

ensure_user() {
    if ! id "${APP_USER}" >/dev/null 2>&1; then
        useradd --create-home --shell /bin/bash "${APP_USER}"
    fi
    usermod -aG video,render,input "${APP_USER}" || true
}

install_packages() {
    apt-get update
    local packages=(
        ca-certificates
        curl
        evtest
        git
        kms++-utils
        libdrm2
        libegl1
        libgl1
        libgles2
        openssh-client
        sqlite3
    )

    if apt-get install -y --no-install-recommends "${packages[@]}"; then
        return
    fi

    echo "Bulk package install failed; retrying package-by-package."
    for package_name in "${packages[@]}"; do
        apt-get install -y --no-install-recommends "${package_name}" || true
    done
}

install_uv() {
    if command -v uv >/dev/null 2>&1; then
        return
    fi
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
}

checkout_repo() {
    install -d -m 0755 "$(dirname "${APP_DIR}")"
    if [ ! -d "${APP_DIR}/.git" ]; then
        git clone "${REPO_URL}" "${APP_DIR}"
    else
        git -C "${APP_DIR}" pull --ff-only
    fi
    chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}"
}

sync_python() {
    runuser -u "${APP_USER}" -- bash -lc \
        "cd '${APP_DIR}' && '${UV_BIN}' python install 3.13 && '${UV_BIN}' sync --frozen --no-dev"
}

prepare_runtime_paths() {
    install -d -m 0750 -o "${APP_USER}" -g "${APP_GROUP}" "${STATE_DIR}"
    install -d -m 0750 -o root -g "${APP_GROUP}" "${BACKUP_DIR}"
    install -d -m 0750 -o root -g "${APP_GROUP}" "${CONFIG_DIR}"

    if [ ! -f "${PIN_PATH}" ]; then
        python3 - <<PY
from pathlib import Path
from secrets import randbelow

pin_path = Path("${PIN_PATH}")
pin_path.write_text(f"{randbelow(900000) + 100000}\\n", encoding="utf-8")
PY
        chown root:"${APP_GROUP}" "${PIN_PATH}"
        chmod 0640 "${PIN_PATH}"
    fi
}

initialize_app_data() {
    local seed_status=0
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
}

install_services() {
    install -m 0644 "${APP_DIR}/systemd/"*.service /etc/systemd/system/
    install -m 0644 "${APP_DIR}/systemd/"*.timer /etc/systemd/system/

    cat >/etc/sudoers.d/carolins-kasse <<EOF
${APP_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart carolins-kasse.service
${APP_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl start carolins-kasse-update.service
${APP_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl start carolins-kasse-backup.service
EOF
    chmod 0440 /etc/sudoers.d/carolins-kasse

    systemctl daemon-reload
    systemctl enable carolins-kasse-backup.timer
    systemctl enable carolins-kasse.service
}

finish_install() {
    systemctl disable carolins-install.service || true
    rm -f /etc/systemd/system/carolins-install.service
    systemctl daemon-reload
    systemctl restart carolins-kasse.service
    echo "Bootstrap finished at $(date --iso-8601=seconds)"
}

ensure_user
install_packages
install_uv
checkout_repo
sync_python
prepare_runtime_paths
initialize_app_data
install_services
finish_install
