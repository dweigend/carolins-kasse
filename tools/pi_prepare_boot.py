#!/usr/bin/env python3
"""Prepare a Raspberry Pi OS bootfs partition for first-boot installation."""

import argparse
import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_BOOTFS_CANDIDATES = (
    Path("/Volumes/bootfs"),
    Path("/Volumes/boot"),
)

FIRSTBOOT_SCRIPT = """#!/bin/bash
set -euo pipefail

BOOT_DIR="/boot/firmware"
if [ ! -f "${BOOT_DIR}/carolins-pi-bootstrap.sh" ]; then
    BOOT_DIR="/boot"
fi

install -m 0755 "${BOOT_DIR}/carolins-pi-bootstrap.sh" \\
    /usr/local/sbin/carolins-pi-bootstrap.sh
install -m 0644 "${BOOT_DIR}/carolins-install.service" \\
    /etc/systemd/system/carolins-install.service
if [ -f "${BOOT_DIR}/carolins-install.env" ]; then
    install -d -m 0750 /etc/carolins-kasse
    install -m 0640 "${BOOT_DIR}/carolins-install.env" \\
        /etc/carolins-kasse/install.env
fi

systemctl disable --now userconfig.service || true
rm -f /etc/ssh/sshd_config.d/rename_user.conf /run/sshwarn

CMDLINE="${BOOT_DIR}/cmdline.txt"
if [ -f "${CMDLINE}" ]; then
    cp "${CMDLINE}" "${CMDLINE}.carolins.bak"
    sed -i -E 's# ?systemd\\.run=[^ ]+##g; s# ?systemd\\.run_success_action=[^ ]+##g; s# ?systemd\\.unit=kernel-command-line\\.target##g; s#  +# #g' "${CMDLINE}"
fi

rm -f \\
    "${BOOT_DIR}/carolins-firstboot.sh" \\
    "${BOOT_DIR}/carolins-pi-bootstrap.sh" \\
    "${BOOT_DIR}/carolins-install.service" \\
    "${BOOT_DIR}/carolins-install.env"

systemctl daemon-reload
systemctl enable carolins-install.service
"""

CMDLINE_TOKENS = (
    "systemd.run=/boot/firmware/carolins-firstboot.sh",
    "systemd.run_success_action=reboot",
    "systemd.unit=kernel-command-line.target",
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare Raspberry Pi OS bootfs for Carolin's Kasse first boot."
    )
    parser.add_argument(
        "bootfs",
        nargs="?",
        type=Path,
        help="mounted bootfs path, for example /Volumes/bootfs",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing non-Carolin systemd.run first-boot hook",
    )
    parser.add_argument(
        "--repo-url",
        default=os.environ.get("CAROLINS_KASSE_REPO_URL", ""),
        help="optional Git repository URL for the Pi bootstrap checkout",
    )
    parser.add_argument(
        "--repo-ref",
        default=os.environ.get("CAROLINS_KASSE_REPO_REF", ""),
        help="optional remote branch name for the Pi bootstrap checkout",
    )
    return parser.parse_args()


def main() -> int:
    """Prepare the boot partition."""
    args = parse_args()
    bootfs = args.bootfs or find_bootfs()
    if not bootfs:
        print("No bootfs mount found. Pass the path explicitly.")
        return 1

    bootfs = bootfs.expanduser().resolve()
    validation_error = validate_bootfs(bootfs)
    if validation_error:
        print(validation_error)
        return 1

    cmdline_path = bootfs / "cmdline.txt"
    cmdline = cmdline_path.read_text(encoding="utf-8").strip()
    if has_foreign_systemd_run(cmdline) and not args.force:
        print(
            "cmdline.txt already contains a different systemd.run hook. "
            "Re-run with --force only if the Imager customisation has finished."
        )
        return 1

    write_firstboot_files(bootfs, repo_url=args.repo_url, repo_ref=args.repo_ref)
    update_cmdline(cmdline_path)
    print(f"Prepared {bootfs} for Carolin's Kasse first boot.")
    return 0


def find_bootfs() -> Path | None:
    """Return the first known macOS bootfs mount."""
    for candidate in DEFAULT_BOOTFS_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def validate_bootfs(bootfs: Path) -> str | None:
    """Return an error when the mount does not look like Raspberry Pi bootfs."""
    if not bootfs.exists():
        return f"Bootfs path does not exist: {bootfs}"
    if not (bootfs / "cmdline.txt").exists():
        return f"Missing cmdline.txt in {bootfs}"
    if not (bootfs / "config.txt").exists():
        return f"Missing config.txt in {bootfs}"
    return None


def has_foreign_systemd_run(cmdline: str) -> bool:
    """Return True when cmdline contains another first-boot systemd.run hook."""
    for token in cmdline.split():
        if token.startswith("systemd.run=") and token != CMDLINE_TOKENS[0]:
            return True
    return False


def write_firstboot_files(bootfs: Path, *, repo_url: str, repo_ref: str) -> None:
    """Write first-boot installer files to the boot partition."""
    firstboot_path = bootfs / "carolins-firstboot.sh"
    firstboot_path.write_text(FIRSTBOOT_SCRIPT, encoding="utf-8")
    try_chmod(firstboot_path, 0o755)
    shutil.copyfile(
        REPO_ROOT / "tools" / "pi_bootstrap.sh", bootfs / "carolins-pi-bootstrap.sh"
    )
    try_chmod(bootfs / "carolins-pi-bootstrap.sh", 0o755)
    shutil.copyfile(
        REPO_ROOT / "systemd" / "carolins-install.service",
        bootfs / "carolins-install.service",
    )
    write_install_env(bootfs, repo_url=repo_url, repo_ref=repo_ref)


def write_install_env(bootfs: Path, *, repo_url: str, repo_ref: str) -> None:
    """Write optional bootstrap checkout settings for systemd."""
    lines = []
    if repo_url:
        lines.append(f"CAROLINS_KASSE_REPO_URL={quote_systemd_env(repo_url)}")
    if repo_ref:
        lines.append(f"CAROLINS_KASSE_REPO_REF={quote_systemd_env(repo_ref)}")

    install_env_path = bootfs / "carolins-install.env"
    if lines:
        install_env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif install_env_path.exists():
        install_env_path.unlink()


def quote_systemd_env(value: str) -> str:
    """Quote a value for a systemd EnvironmentFile."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def try_chmod(path: Path, mode: int) -> None:
    """Best-effort chmod for FAT boot partitions."""
    try:
        path.chmod(mode)
    except OSError:
        pass


def update_cmdline(cmdline_path: Path) -> None:
    """Append first-boot tokens to cmdline.txt idempotently."""
    tokens = cmdline_path.read_text(encoding="utf-8").strip().split()
    tokens = [token for token in tokens if not token.startswith("systemd.run=")]
    tokens = [
        token
        for token in tokens
        if not token.startswith("systemd.run_success_action=")
        and token != "systemd.unit=kernel-command-line.target"
    ]
    tokens.extend(token for token in CMDLINE_TOKENS if token not in tokens)
    cmdline_path.write_text(" ".join(tokens) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
