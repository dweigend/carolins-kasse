# Session Handover

**Last Updated:** 2026-07-04 CEST

## Current State

- Core kiosk flows are implemented: login, menu, shopping/scan, picker, checkout, recipe mode, math mode, sessions, earnings, transactions, and balances.
- SceneManager now supports optional `on_enter()` and `reset_user_state()`
  lifecycle hooks. Login changes and shell logout reset user-bound scene state
  between kiosk users without wiping normal in-scene state on ordinary scene
  entry.
- The shell-based 1024x600 UI is in place. Cashier and recipe UIs have had local screenshot/smoke validation, but still need real Pi/touch/scanner/kid testing.
- FastAPI remote admin is usable on the home network for products, users, recipes, balances, barcode downloads, and A4 print PDFs.
- Pygame admin mode opens with Admin card `2000000000046` and provides server status/QR, balance controls, account overview, and notes.
- Database setup is KISS: one local `data/kasse.db`, fixed Carolin/Annelie initial setup, non-destructive seed script by default.
- Raspberry Pi first-boot setup is automated with `tools/pi_prepare_boot.py`, `tools/pi_bootstrap.sh`, systemd units, and `docs/PI_SETUP.md`.
- Pi runtime DB can live outside the checkout via `CAROLINS_KASSE_DB_PATH`, with `/var/lib/carolins-kasse/kasse.db` used by the systemd units.
- Browser admin has a PIN-protected admin session for mutating POST routes. The
  existing debug PIN cookie/session is paired with CSRF tokens, including
  `/debug/unlock` before PIN acceptance.
- Browser admin barcode modals avoid inline JavaScript string arguments and pass
  barcode data through HTML data attributes.
- Checkout and balance writes are atomic: SQLite connections enable foreign
  keys and a busy timeout, checkout runs inside `BEGIN IMMEDIATE`, and callers
  get `CheckoutResult` or `CheckoutError` instead of partial updates.
- Self-checkout refreshes runtime state after a successful checkout so the
  displayed balance matches the committed database state.
- A unittest-based temp-DB and lifecycle smoke suite now covers database
  safety, admin security flows, atomic checkout, and user-state scene resets
  without adding dependencies. The current suite has 21 passing tests.
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
- The SD card was fully reflashed on 2026-05-02 through a Terminal sudo flow. The flash log reports `3229614080 bytes transferred`, bootfs preparation completed, and `/dev/disk5` was ejected.
- Local ignored flash helper `dev/local-debug/scripts/flash_carolins_kasse_sd.sh` has been updated to mask `userconfig.service` during first boot, matching `tools/pi_prepare_boot.py`.
- The fresh Pi is reachable over SSH at `carolins-kasse.local` / `192.168.1.139`. First-boot user setup worked; `kasse` is in `sudo`, `input`, `render`, `gpio`, `i2c`, and `spi`.
- The installer completed its real work but hit the systemd start timeout at the final service-start step. Manual recovery via SSH started `carolins-kasse.service`; it is now `active` and `enabled`, `userconfig.service` is `masked`, and no failed units remain.

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
- Reflashed the SD card on 2026-05-02 after verifying `/dev/disk5`, the Raspberry Pi OS image SHA256, the local flash helper patch, and a dry-run bootfs containing `systemctl mask userconfig.service`, `CAROLINS_KASSE_REPO_REF=codex/pi-firstboot-installer`, and the `systemd.run` first-boot hook.
- Validated the freshly flashed Pi over SSH and manually started the kiosk service after the installer timed out at the final start step.
- Added temp-DB unittest smoke coverage under `tests/` for database behavior and
  admin safety without touching the runtime DB.
- Protected admin mutating POST routes with the existing debug PIN/admin session
  plus CSRF tokens, and made `/debug/unlock` validate CSRF before accepting a
  PIN.
- Reworked admin barcode modal wiring to use data attributes instead of inline
  JavaScript string arguments.
- Made checkout updates atomic with SQLite foreign keys, per-connection busy
  timeouts, `BEGIN IMMEDIATE`, `CheckoutResult`/`CheckoutError`, and
  self-checkout runtime refresh.
- Added regression coverage for atomic checkout, foreign key enforcement, and
  self-checkout balance refresh.
- Added SceneManager lifecycle handling for #12: scene entry can refresh local
  state through `on_enter()`, while login changes and shell logout call
  `reset_user_state()` to clear user-bound scene state.
- Updated ScanScene, RecipeScene, and MathGameScene behavior around user-state
  resets: scan keeps its normal picker/cart flow on ordinary entry, recipe
  clears selections/scans/completion/checkout state on user reset, and math
  refreshes for the current user/difficulty without per-frame resets.
- Added `tests/test_scene_lifecycle.py`; the full unittest suite now has 21
  passing tests.
- Review pass found no P0-P3 findings for the current #12 work. PickerScene
  reachability remains tracked separately as #18.

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

Run on 2026-07-04 CEST after the admin safety, data integrity, temp-DB test,
and scene-lifecycle work:

- `uv run ruff check src/ tools/ tests/`
- `PYTHONPYCACHEPREFIX=/tmp/carolins_kasse_compileall uv run python -m compileall -q src tools tests main.py`
- `uv run python -m unittest discover -s tests` (21 tests)
- `git diff --check`

## Open GitHub Issues

Covered by the current branch commits and ready to close after review/merge:

- #10 Protect admin write routes from unauthenticated POSTs
- #11 Make checkout and balance updates atomic
- #14 Refresh displayed balance after self-checkout
- #15 Render admin barcode modal data without inline JavaScript strings
- #16 Enforce SQLite foreign key constraints
- #21 Add temp-DB regression smoke suite
- #12 Reset scene state between kiosk users

Next active kiosk correctness issues:

- #13 Track recipe ingredient quantities instead of binary scans
- #17 Prevent inactive recipe ingredients from blocking completion
- #18 Make PickerScene reachable from the kiosk flow
- #19 Ignore barcode scanner input in math mode
- #20 Award recipe bonus after successful recipe checkout

Highest-priority Pi operations follow-ups:

- #22 Cache fonts and scaled assets for Pi Zero runtime
- #23 Add rollback safety to Pi update script
- #24 Show install, update, and backup status on debug page

Still open for validation or later structure work:

- #1 Validate cashier UI with kids on touch display
- #2 Validate recipe UI with kids on touch display
- #4 Split database module for admin backend
- #7 Validate automated Raspberry Pi first-boot setup
- #8 Validate Pi Zero USB hub and OTG host path
- #9 Pi first-boot installer fails before installing services

## Known Risks

- `src/utils/database.py` is still the largest mixed-responsibility module. Split it only when the next write path makes the boundary obvious.
- Hardware behavior is not fully validated: scanner timing, touch target precision, fullscreen rendering, Pi performance, and child comprehension still need real tests.
- Remote admin is still intended for the home WiFi. Mutating POST routes require
  the debug PIN/admin session cookie plus CSRF, while the read surface remains
  intentionally lightweight.
- Generated runtime outputs (`data/print/*.pdf`, barcode files, local DB changes) must stay separate from source changes.
- The first-boot installer needs one more clean validation after the timeout fix: the current fresh install succeeded after manual service start, but `carolins-install.service` timed out just before the final kiosk start completed.
- SEENGREAT hub behavior is validated with the corrected topology. The Pi Zero 2 W has one USB data bus, so using the Pi micro-USB data port and the shield pogo-pin upstream at the same time causes descriptor failures.
- The current Pi is usable over SSH and the kiosk is running manually, but it is not fully installed: no kiosk systemd service exists yet, `carolins-install.service` is failed, and `kasse` cannot run sudo. Rebooting this Pi will not reliably return to the kiosk until the installer/service issue is fixed by reflash or root/SD-card recovery.

## Next Best Steps

1. Close or update #10, #11, #12, #14, #15, #16, and #21 after the current branch is reviewed or merged.
2. Fix the next kiosk correctness bugs: recipe quantities (#13), inactive recipe ingredients (#17), PickerScene reachability (#18), scanner input in math mode (#19), and recipe bonus timing (#20).
3. Improve Pi operations: update rollback safety (#23), debug observability (#24), and Pi Zero runtime performance (#22).
4. Run full kiosk smoke on the real Pi: touch start/login, child cards, scanner product labels, number pad input, checkout, Admin card, recipe cards, math mode, debug PIN, update, and remote admin QR.
5. Add observations to issues #1, #2, #7, and #8.
6. Add read-only transaction and earnings views before more write-heavy CRUD.
7. Split `src/utils/database.py` in a separate refactor pass when adding the next admin data path.
