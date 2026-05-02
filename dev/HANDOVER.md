# Session Handover

**Last Updated:** 2026-05-02 10:06 CEST

## Current State

- Core kiosk flows are implemented: login, menu, shopping/scan, picker, checkout, recipe mode, math mode, sessions, earnings, transactions, and balances.
- The shell-based 1024x600 UI is in place. Cashier and recipe UIs have had local screenshot/smoke validation, but still need real Pi/touch/scanner/kid testing.
- FastAPI remote admin is usable on the home network for products, users, recipes, balances, barcode downloads, and A4 print PDFs.
- Pygame admin mode opens with Admin card `2000000000046` and provides server status/QR, balance controls, account overview, and notes.
- Database setup is KISS: one local `data/kasse.db`, fixed Carolin/Annelie initial setup, non-destructive seed script by default.
- Raspberry Pi first-boot setup is automated with `tools/pi_prepare_boot.py`, `tools/pi_bootstrap.sh`, systemd units, and `docs/PI_SETUP.md`.
- Pi runtime DB can live outside the checkout via `CAROLINS_KASSE_DB_PATH`, with `/var/lib/carolins-kasse/kasse.db` used by the systemd units.
- Browser admin has a PIN-protected `/debug` page for status, logs, backups, restart, and update actions.
- `data/kasse.db` may contain local runtime changes and should not be committed accidentally.
- USB hub bring-up is active: Raspberry Pi Zero 2 W plus SEENGREAT Pi USB HUB Rev1.1 must be tested with SSH over WiFi so the single Pi USB data bus can be isolated.
- Local-only debug memory lives under ignored `dev/local-debug/` for reports, scripts, logs, keys, secrets, and downloaded OS images.
- Fresh Raspberry Pi OS Lite 64-bit was flashed successfully on 2026-04-29 and the Pi is reachable over WiFi SSH as `kasse@carolins-kasse.local` / `192.168.1.139`.
- First-boot validation failed late: the Pi cloned GitHub `master` at `aa76175`, which lacks the local `systemd/` files from `codex/pi-firstboot-installer`, so `carolins-install.service` failed before installing `carolins-kasse.service`.
- The first-boot user group setup also failed on missing `lpadmin`, leaving `kasse` without sudo. Track and fix in issue #9.
- USB baseline on the Pi: host mode is active via `dtoverlay=dwc2,dr_mode=host`, `vcgencmd get_throttled` reports `0x0`, `lsusb` shows only the root hub, and boot dmesg contains `usb 1-1 ... error -71` descriptor failures.
- SEENGREAT hub works as a standalone Mac USB hub and exposes downstream HID/CP2102 devices there, so the hub chip and Mac-side cable path are basically functional.
- The corrected SEENGREAT topology is validated: leave the Pi micro-USB data port empty, keep the shield in `SW1=0`, `SW2=1`, and attach touch, scanner, and number pad downstream of the shield. `lsusb` now shows the QinHeng hub, QDTECH MPI7002 touch, M4 YX scanner, and SIGMACHIP number pad.
- Touch is now working again through the shield. Keep the current cabling/ports as the known-good setup. The app also normalizes SDL finger events into mouse events so touch-only SDL paths still drive the existing UI.
- The Pi still has an incomplete first-boot install. `carolins-install.service` is failed, `kasse` is not in sudoers, root SSH is unavailable, and the SSH banner still reports the Raspberry Pi new-user warning. This cannot be fixed in-place without root access or SD-card recovery.
- The current Pi has `/opt/carolins-kasse` checked out on `codex/pi-firstboot-installer` at local commit `400bf06`, while the remote branch was rewritten. A manual kiosk process is running over SSH as `kasse` with PID `1885`; log path: `/home/kasse/carolins-debug/manual-kiosk.log`. This is a temporary test workaround, not a systemd-managed install.
- User-level helper scripts for this temporary Pi state live at `/home/kasse/carolins-debug/start-kiosk.sh` and `/home/kasse/carolins-debug/status-kiosk.sh`.
- The SD card is back in the Mac as `/dev/disk5` with `bootfs` on `/dev/disk5s1`. Full reflash is prepared but not yet written because this Codex session has no active macOS sudo ticket.
- Local ignored flash helper `dev/local-debug/scripts/flash_carolins_kasse_sd.sh` has been updated to mask `userconfig.service` during first boot, matching `tools/pi_prepare_boot.py`.

## Recent Completed Work

- Added non-destructive `tools/seed_database.py` workflow and central barcode rules in `src/utils/barcodes.py`.
- Added FastAPI admin write flows, balance history, minimal edits, SVG barcode links, and A4 print generation.
- Added on-device Pygame admin mode and refactored its rendering helpers.
- Merged User and Konten into one Pygame admin tab with safer bottom spacing.
- Cleaned active documentation down to `AGENTS.md`, `README.md`, `dev/HANDOVER.md`, `dev/PLAN.md`, and `dev/ARCHITECTURE.md`.
- Removed unused `src/utils/layout.py` Phase 6 stubs and replaced scene barcode prefix strings with central constants.
- Added automated Raspberry Pi Lite first-boot installation path, update/backup scripts, systemd units, and setup documentation.
- Added USB hub debugging notes and local-only SD-card/headless setup memory for the current hardware bring-up.
- Flashed the fresh Pi OS Lite SD card, confirmed SSH access, captured first-boot failure details, and documented USB baseline observations in issues #7, #8, and #9.
- Updated the Pi setup path after first hardware validation: `carolins-install.service` reads `/etc/carolins-kasse/install.env`, `tools/pi_prepare_boot.py` can write `--repo-ref`, and bootstrap group setup now skips missing optional groups instead of failing the whole `usermod` call.
- Validated the USB shield topology after moving all USB devices to the SEENGREAT shield and leaving the Pi micro-USB data port unused.
- Confirmed the touch display works after cabling/port correction and added SDL finger-event normalization in `main.py`.
- Prepared the next clean SD-card flash path on 2026-05-02: verified `/dev/disk5`, verified Raspberry Pi OS image SHA256, patched the local flash helper, and confirmed a dry-run bootfs contains `systemctl mask userconfig.service`, `CAROLINS_KASSE_REPO_REF=codex/pi-firstboot-installer`, and the `systemd.run` first-boot hook.

## Verification Run Recently

- `uv run ruff check src/ tools/`
- `uv run ruff format src/ tools/`
- `uv run python -m compileall src tools`
- AdminScene smoke against a temporary DB: tabs render, buttons register, `+1` changes balance correctly.
- Remote admin smoke: managed server starts, `/users` returns 200, stop terminates the managed process.
- Seed safety smoke: setup refuses to overwrite existing runtime data unless `--reset` is passed.

Run after the Pi setup implementation:

- `uv run ruff check src/ tools/`
- `uv run ruff format src/ tools/`
- `uv run python -m compileall src tools`
- `uv run python tools/pi_prepare_boot.py <temporary bootfs fixture>`
- FastAPI admin smoke including `/debug`

## Open GitHub Issues

- #1 Validate cashier UI with kids on touch display
- #2 Validate recipe UI with kids on touch display
- #4 Split database module for admin backend
- #7 Validate automated Raspberry Pi first-boot setup
- #8 Validate Pi Zero USB hub and OTG host path

Closed in this phase:

- #3 Demo database workflow
- #5 Printable barcode workflow
- #6 On-device Pygame admin mode

## Known Risks

- `src/utils/database.py` is still the largest mixed-responsibility module. Split it only when the next write path makes the boundary obvious.
- Hardware behavior is not fully validated: scanner timing, touch target precision, fullscreen rendering, Pi performance, and child comprehension still need real tests.
- Remote admin product/user/recipe pages still have no web login by design. Debug/update actions are protected by the generated local setup PIN.
- Generated runtime outputs (`data/print/*.pdf`, barcode files, local DB changes) must stay separate from source changes.
- The first-boot installer still needs validation on a freshly flashed Raspberry Pi OS Lite 64-bit Trixie image.
- SEENGREAT hub behavior is validated with the corrected topology. The Pi Zero 2 W has one USB data bus, so using the Pi micro-USB data port and the shield pogo-pin upstream at the same time causes descriptor failures.
- The current Pi is usable over SSH and the kiosk is running manually, but it is not fully installed: no kiosk systemd service exists yet, `carolins-install.service` is failed, and `kasse` cannot run sudo. Rebooting this Pi will not reliably return to the kiosk until the installer/service issue is fixed by reflash or root/SD-card recovery.

## Next Best Steps

1. In a Mac Terminal with admin rights, run `dev/local-debug/scripts/flash_carolins_kasse_sd.sh write /dev/disk5 --yes` from the repo root.
2. After the script ejects the SD card, boot the Pi with the validated shield topology: `SW1=0`, `SW2=1`, power through shield USB-C, all USB peripherals on the shield, Pi micro-USB data port empty.
3. Validate the automated first-boot setup over WiFi SSH: `carolins-kasse.service` active, `userconfig.service` masked, no Raspberry Pi rename-user prompt, `throttled=0x0`, and all shield USB devices visible.
4. Run full kiosk smoke on the real Pi: touch start/login, child cards, scanner product labels, number pad input, checkout, Admin card, recipe cards, math mode, debug PIN, update, and remote admin QR.
5. Add observations to issues #1, #2, #7, and #8.
6. Add read-only transaction and earnings views before more write-heavy CRUD.
7. Split `src/utils/database.py` in a separate refactor pass when adding the next admin data path.
