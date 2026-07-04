# Session Handover

**Last Updated:** 2026-07-04 CEST

## Current State

- Core kiosk flows are implemented: login, menu, shopping/scan, picker, checkout, recipe mode, math mode, sessions, earnings, transactions, and balances.
- SceneManager now supports optional `on_enter()` and `reset_user_state()`
  lifecycle hooks. Login changes and shell logout reset user-bound scene state
  between kiosk users without wiping normal in-scene state on ordinary scene
  entry.
- SceneManager now also accepts lazy scene factories and caches each scene after
  first construction. `main.py` eagerly creates only `StartScene`; login, admin,
  menu, scan, recipe, math, and picker scenes are constructed on first entry so
  admin QR/qrcode/Pillow work stays out of the kiosk import and first-frame
  path.
- The shell-based 1024x600 UI is in place. Cashier and recipe UIs have had local screenshot/smoke validation, but still need real Pi/touch/scanner/kid testing.
- FastAPI remote admin is usable on the home network for products, users, recipes, balances, barcode downloads, and A4 print PDFs.
- Pygame admin mode opens with Admin card `2000000000046` and provides server status/QR, balance controls, account overview, and notes.
- Database setup is KISS: one local `data/kasse.db`, fixed Carolin/Annelie initial setup, non-destructive seed script by default.
- Raspberry Pi first-boot setup is automated with `tools/pi_prepare_boot.py`, `tools/pi_bootstrap.sh`, systemd units, and `docs/PI_SETUP.md`.
- First-boot bootfs preparation keeps generated bootfs orchestration in Python
  and the boot-time shell entrypoint in `tools/pi_firstboot.sh`;
  `tools/pi_prepare_boot.py` copies that script instead of embedding shell text.
- Pi runtime DB can live outside the checkout via `CAROLINS_KASSE_DB_PATH`, with `/var/lib/carolins-kasse/kasse.db` used by the systemd units.
- The current `codex/pi-ops-safety` branch covers Pi operations issues #23
  and #24. `tools/pi_update.sh` records the previous commit and rolls back
  after post-pull failures, including no-op pull failure paths. The
  PIN-protected debug page now reports service, install/update/backup, timer,
  failed-unit, and log-snippet status while degrading gracefully when Pi or
  systemd access is unavailable.
- `tools/pi_update.sh` now installs the permanent systemd units from
  `systemd/` and runs `systemctl daemon-reload` after successful validation and
  generated-output steps, so kiosk/update/backup unit changes take effect during
  normal Pi updates.
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
  without adding dependencies. It also covers recipe quantities, inactive
  recipe ingredients, picker reachability, math scanner filtering, and recipe
  bonus timing, Pi update rollback safety with shell fixtures, Pi update
  systemd unit installation, debug observability, and keypad keycode input. The
  current suite has 54 passing tests.
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
- Earlier incomplete first-boot/manual-kiosk states were superseded by the fresh
  SD-card install below.
- The SD card was fully reflashed on 2026-05-02 through a Terminal sudo flow. The flash log reports `3229614080 bytes transferred`, bootfs preparation completed, and `/dev/disk5` was ejected.
- Local ignored flash helper `dev/local-debug/scripts/flash_carolins_kasse_sd.sh` has been updated to mask `userconfig.service` during first boot, matching `tools/pi_prepare_boot.py`.
- The fresh Pi is reachable over SSH at `carolins-kasse.local` / `192.168.1.139`. First-boot user setup worked; `kasse` is in `sudo`, `input`, `render`, `gpio`, `i2c`, and `spi`.
- The installer completed its real work but hit the systemd start timeout at the final service-start step. Manual recovery via SSH started `carolins-kasse.service`; it is now `active` and `enabled`, `userconfig.service` is `masked`, and no failed units remain.
- Remote debugging is available over SSH as `kasse@carolins-kasse.local`
  (`192.168.1.139`). The current Pi checkout is `/opt/carolins-kasse` on
  `codex/pi-firstboot-installer` at `fda1394`; the kiosk service is systemd
  managed and active.
- Passwordless sudo is limited to the intended service operations:
  restart `carolins-kasse.service`, start `carolins-kasse-update.service`, and
  start `carolins-kasse-backup.service`.
- Live keypad validation on 2026-07-04 confirmed that the SIGMACHIP keypad is
  visible as `/dev/input/event2` and emits raw Linux events for `KP1`, `KP2`,
  `KP3`, `NUMLOCK`, and `KPENTER`. The local #27 code fix maps empty-unicode
  keypad digit keycodes in shared input, MathGameScene, and Numpad; Pi
  validation of the app path is still pending.
- Local Codex debug helpers live outside the repo at
  `/Users/davidweigend/.codex/skills/carolins-kasse-debug/`. Its
  `scripts/kasse-debug.sh` helper wraps status, USB, boot, logs, keypad,
  tests, update, restart, and backup workflows.

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
- Added `tests/test_scene_lifecycle.py` during the #12 work; the full unittest
  suite later expanded to 32 passing tests for the kiosk-correctness round.
- Review passes found no P0-P3 findings for `ef654b8` (#12) or `3b8d932`
  (#13/#17/#20).
- Added recipe correctness for #13, #17, and #20: ingredients track required
  quantities, inactive products no longer block recipe completion, and recipe
  bonuses are awarded only after successful checkout.
- Made PickerScene reachable from ScanScene for #18 while preserving the normal
  scan/cart flow.
- Made MathGameScene ignore scanner bursts for #19. The first review of
  `aa81366` found a P2 issue where scanner bursts without Enter could leak
  into math input; `a4ebbf4` now discards unterminated bursts, clears them on
  Backspace/Escape, and keeps normal one- to three-digit math entry covered.
- Added Pi update rollback safety for #23 in `3747108`, with follow-up
  coverage in `d9e6b96` for post-pull rollback, kiosk restart after successful
  rollback, and the no-op pull failure case.
- Expanded PIN-protected debug observability for #24 in `959dbaf`: kiosk
  service, systemd availability, install/update/backup service status, backup
  timer, failed units, and bounded log snippets are visible from the debug
  page; non-Pi/systemd-unavailable environments degrade gracefully.
- Refactored Pi first-boot and update-test shell boundaries in `cd900a2`:
  `tools/pi_firstboot.sh` is now a real shell file, `tools/pi_prepare_boot.py`
  only copies it into the bootfs, and Pi update fakes live as executable shell
  fixtures under `tests/fixtures/pi_update/` while Python tests orchestrate and
  assert behavior.
- Flattened `tests/test_recipe_scene.py` and `tests/test_scene_lifecycle.py`;
  `tests/db_isolation.py` now holds the small temp-DB helpers needed by those
  tests.
- Review status for the Pi/Ops safety round is clean through `cd900a2`, with no
  P0-P3 findings. The current `codex/pi-ops-safety` branch covers #23 and #24
  and is ready to close those issues after merge.
- Local #28 worker removed the kiosk service `network-online.target`
  dependency so the pygame kiosk can start without waiting for NetworkManager
  wait-online; Pi boot-chain validation is still needed.
- Local Pi update worker taught `tools/pi_update.sh` to install the permanent
  kiosk/update/backup systemd units and daemon-reload after successful update
  validation, while excluding the first-boot-only `carolins-install.service`.
- Local #27 worker added shared keyboard digit normalization for top-row and
  keypad digits with empty Unicode, reused by InputManager, MathGameScene, and
  Numpad while preserving math scanner-burst filtering.
- Local #30 worker added lazy scene construction for kiosk startup: scene package
  exports no longer import every scene eagerly, `main.py` registers non-start
  scenes as factories, and SceneManager preserves cached scene instances so
  cart, picker, recipe, and math lifecycle behavior remains intentional.
- Local #29/#22 performance worker removed NumPy from the kiosk paper texture
  cold path, removed the now-unused NumPy dependency, cached central font
  objects by path and size, and added exact-size scaled asset caching for the
  repeated ProductDisplay coin and MathGame reward-coin animation hotspots.

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

Run on 2026-07-04 CEST after the full kiosk-correctness round:

- `uv run ruff check src/ tools/ tests/`
- `PYTHONPYCACHEPREFIX=/tmp/carolins_kasse_compileall uv run python -m compileall -q src tools tests main.py`
- `uv run python -m unittest discover -s tests` (32 tests)
- `git diff --check`

Latest green checks on 2026-07-04 CEST for the Pi/Ops safety round:

- `uv run ruff check src/ tools/ tests/`
- `PYTHONPYCACHEPREFIX=/tmp/carolins_kasse_compileall uv run python -m compileall -q src tools tests main.py`
- `uv run python -m unittest discover -s tests` (39 tests)
- `bash -n tools/pi_bootstrap.sh tools/pi_firstboot.sh tools/pi_update.sh tools/pi_backup.sh`
- `bash -n tests/fixtures/pi_update/app_tools/pi_backup.sh tests/fixtures/pi_update/fake_bin/* tests/fixtures/pi_update/venv_bin/python`
- `git diff --check`

Run on 2026-07-04 CEST for the local #28 systemd quick win:

- `uv run ruff format tests/test_systemd_units.py`
- `uv run python -m unittest tests.test_systemd_units`
- `uv run ruff check src/ tools/ tests/`
- `PYTHONPYCACHEPREFIX=/tmp/carolins_kasse_compileall uv run python -m compileall -q src tools tests main.py`
- `uv run python -m unittest discover -s tests` (40 tests)
- `git diff --check`

Run on 2026-07-04 CEST for the local #27 keypad keycode fix:

- `uv run ruff format src/ tools/ tests/`
- `uv run ruff check src/ tools/ tests/`
- `PYTHONPYCACHEPREFIX=/tmp/carolins_kasse_compileall uv run python -m compileall -q src tools tests main.py`
- `uv run python -m unittest tests.test_kiosk_flow_input` (11 tests)
- `uv run python -m unittest discover -s tests` (44 tests)
- `git diff --check`

Run on 2026-07-04 CEST for the local #30 lazy-scene startup pass:

- `uv run python -m unittest tests.test_scene_lifecycle tests.test_main_lazy_imports` (11 tests)
- `uv run ruff format src/ tools/ tests/ main.py`
- `uv run ruff check src/ tools/ tests/ main.py`
- `PYTHONPYCACHEPREFIX=/tmp/carolins_kasse_compileall uv run python -m compileall -q src tools tests main.py`
- `uv run python -m unittest discover -s tests` (53 tests)
- `git diff --check`

Run on 2026-07-04 CEST for the local #29/#22 rendering performance pass:

- `uv run python -m unittest tests.test_render_caching` (4 tests)
- `uv lock --check`
- `uv run ruff format src/ui/texture.py src/utils/fonts.py src/utils/assets.py src/components/product_display.py src/scenes/math_game.py tests/test_render_caching.py`
- `uv run ruff check src/ tools/ tests/`
- `PYTHONPYCACHEPREFIX=/tmp/carolins_kasse_compileall uv run python -m compileall -q src tools tests main.py`
- `uv run python -m unittest discover -s tests` (53 tests)
- `uv run ruff format --check src/ tools/ tests/`
- `git diff --check`

Run on 2026-07-04 CEST for the Pi update systemd unit installation fix:

- `uv run python -m unittest tests.test_pi_update_script` (5 tests)
- `uv run python -m unittest discover -s tests` (54 tests)
- `uv run ruff format tests/test_pi_update_script.py`
- `uv run ruff check src/ tools/ tests/`
- `uv run ruff format --check src/ tools/ tests/`
- `PYTHONPYCACHEPREFIX=/tmp/carolins_kasse_compileall uv run python -m compileall -q src tools tests main.py`
- `bash -n tools/pi_update.sh tests/fixtures/pi_update/fake_bin/systemctl`
- `git diff --check`

## Open GitHub Issues

Covered by earlier correctness branch commits and ready to close after
review/merge:

- #10 Protect admin write routes from unauthenticated POSTs
- #11 Make checkout and balance updates atomic
- #12 Reset scene state between kiosk users
- #13 Track recipe ingredient quantities instead of binary scans
- #14 Refresh displayed balance after self-checkout
- #15 Render admin barcode modal data without inline JavaScript strings
- #16 Enforce SQLite foreign key constraints
- #17 Prevent inactive recipe ingredients from blocking completion
- #18 Make PickerScene reachable from the kiosk flow
- #19 Ignore barcode scanner input in math mode
- #20 Award recipe bonus after successful recipe checkout
- #21 Add temp-DB regression smoke suite

Covered by the current `codex/pi-ops-safety` branch and ready to close after
review/merge:

- #23 Add rollback safety to Pi update script
- #24 Show install, update, and backup status on debug page

Covered by local performance working tree changes and ready for review/merge:

- #29 Remove NumPy paper texture generation from kiosk cold start
- #30 Lazy-load admin and non-start scenes outside the kiosk cold path

Partially covered by local performance working tree changes; keep open for
follow-up measurement and remaining hotspots:

- #22 Cache fonts and scaled assets for Pi Zero runtime

Highest-priority Pi operations follow-up:

- #27 Accept keypad digit keycodes when unicode text is empty
- #28 Deploy and validate the kiosk unit without `network-online.target` on the
  Pi via the normal update service
- #22 Continue cache work beyond the initial font/ProductDisplay/MathGame pass

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
- The current Pi is systemd managed and reachable over SSH, but the direct IP
  `192.168.1.139` has an old local SSH host-key conflict on the Mac. Use
  `carolins-kasse.local` unless the stale known-host entry is intentionally
  cleaned up.

## Next Best Steps

1. Retest the #27 number pad fix on the Pi with the SIGMACHIP keypad.
2. Measure the #28/#29/#30/#22 startup and rendering changes on the Pi, then
   continue #22 only where timing still shows repeated scale/render cost.
3. Use the local `carolins-kasse-debug` skill for SSH diagnostics, tests, and
   safe Pi service actions.
4. Close or update #23 and #24 after the current branch is merged.
5. Run full kiosk smoke on the real Pi: touch start/login, child cards, scanner
   product labels, number pad input, checkout, Admin card, recipe cards, math
   mode, debug PIN, update, and remote admin QR.
6. Add observations to issues #1, #2, #7, #8, and #9.
