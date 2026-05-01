# Session Handover

**Last Updated:** 2026-05-01 11:25 CEST

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
- USB hub bring-up is active: Raspberry Pi Zero 2 W plus SEENGREAT Pi USB HUB Rev1.1 must be tested with SSH over WiFi so the Pi USB data port stays free.
- Local-only debug memory lives under ignored `dev/local-debug/` for reports, scripts, logs, keys, secrets, and downloaded OS images.
- Fresh Raspberry Pi OS Lite 64-bit was flashed successfully on 2026-04-29 and the Pi is reachable over WiFi SSH as `kasse@carolins-kasse.local` / `192.168.1.139`.
- First-boot validation failed late: the Pi cloned GitHub `master` at `aa76175`, which lacks the local `systemd/` files from `codex/pi-firstboot-installer`, so `carolins-install.service` failed before installing `carolins-kasse.service`.
- The first-boot user group setup also failed on missing `lpadmin`, leaving `kasse` without sudo. Track and fix in issue #9.
- USB baseline on the Pi: host mode is active via `dtoverlay=dwc2,dr_mode=host`, `vcgencmd get_throttled` reports `0x0`, `lsusb` shows only the root hub, and boot dmesg contains `usb 1-1 ... error -71` descriptor failures.
- SEENGREAT hub works as a standalone Mac USB hub and exposes downstream HID/CP2102 devices there, so the hub chip and Mac-side cable path are basically functional.
- Latest Pi-side retest with the shield in Pi mode: the Pi sees a high-speed device on `usb 1-1`, but descriptor reads repeatedly fail with `error -71`, followed by `device not accepting address` and disconnect. Afterward `lsusb` still shows only the root hub and `throttled=0x0`.
- The current Pi has `/opt/carolins-kasse` checked out on `codex/pi-firstboot-installer` and a manual kiosk process running over SSH as `kasse` with PID `2453`; log path: `/home/kasse/carolins-debug/manual-kiosk.log`. This is a temporary workaround, not a systemd-managed install.

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
- SEENGREAT hub behavior is now narrowed: standalone Mac hub mode works, but Pi hub mode fails enumeration with `error -71`. Validate Pi direct OTG without shield next; if direct OTG works, the shield's Pi-mode data path/Pogo/switch path is the likely blocker.
- The current Pi is usable over SSH but not fully installed: no kiosk systemd service exists yet, and `kasse` cannot run sudo. A manual kiosk process is running, but rebooting this Pi will not return to the kiosk until the installer/service issue is fixed by reflash or bootfs recovery.

## Next Best Steps

1. Flash Raspberry Pi OS Lite 64-bit and validate the automated first-boot setup.
2. Fix issue #9 so first-boot installs from the intended ref/files and handles optional Linux groups safely.
3. Run Pi direct OTG without shield using a simple HID device; this is the next discriminator after Mac hub success and Pi-mode `error -71`.
4. Run full kiosk smoke on the real Pi: Admin card, child cards, scanner, touch, checkout, recipe, math, debug PIN, update, and remote admin QR.
5. Add observations to issues #1, #2, #7, and #8.
6. Add read-only transaction and earnings views before more write-heavy CRUD.
7. Split `src/utils/database.py` in a separate refactor pass when adding the next admin data path.
