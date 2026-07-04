#!/bin/bash
set -euo pipefail

BOOT_DIR="/boot/firmware"
if [ ! -f "${BOOT_DIR}/carolins-pi-bootstrap.sh" ]; then
    BOOT_DIR="/boot"
fi

install -m 0755 "${BOOT_DIR}/carolins-pi-bootstrap.sh" \
    /usr/local/sbin/carolins-pi-bootstrap.sh
install -m 0644 "${BOOT_DIR}/carolins-install.service" \
    /etc/systemd/system/carolins-install.service
if [ -f "${BOOT_DIR}/carolins-install.env" ]; then
    install -d -m 0750 /etc/carolins-kasse
    install -m 0640 "${BOOT_DIR}/carolins-install.env" \
        /etc/carolins-kasse/install.env
fi

systemctl disable --now userconfig.service || true
systemctl mask userconfig.service || true
rm -f /etc/ssh/sshd_config.d/rename_user.conf /run/sshwarn

CMDLINE="${BOOT_DIR}/cmdline.txt"
if [ -f "${CMDLINE}" ]; then
    cp "${CMDLINE}" "${CMDLINE}.carolins.bak"
    sed -i -E 's# ?systemd\.run=[^ ]+##g; s# ?systemd\.run_success_action=[^ ]+##g; s# ?systemd\.unit=kernel-command-line\.target##g; s#  +# #g' "${CMDLINE}"
fi

rm -f \
    "${BOOT_DIR}/carolins-firstboot.sh" \
    "${BOOT_DIR}/carolins-pi-bootstrap.sh" \
    "${BOOT_DIR}/carolins-install.service" \
    "${BOOT_DIR}/carolins-install.env"

systemctl daemon-reload
systemctl enable carolins-install.service
