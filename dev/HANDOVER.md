# Session Handover

**Last Updated:** 2026-04-26 18:10 CEST

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

## Recent Completed Work

- Added non-destructive `tools/seed_database.py` workflow and central barcode rules in `src/utils/barcodes.py`.
- Added FastAPI admin write flows, balance history, minimal edits, SVG barcode links, and A4 print generation.
- Added on-device Pygame admin mode and refactored its rendering helpers.
- Merged User and Konten into one Pygame admin tab with safer bottom spacing.
- Cleaned active documentation down to `AGENTS.md`, `README.md`, `dev/HANDOVER.md`, `dev/PLAN.md`, and `dev/ARCHITECTURE.md`.
- Removed unused `src/utils/layout.py` Phase 6 stubs and replaced scene barcode prefix strings with central constants.
- Added automated Raspberry Pi Lite first-boot installation path, update/backup scripts, systemd units, and setup documentation.

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

## Next Best Steps

1. Flash Raspberry Pi OS Lite 64-bit, run `tools/pi_prepare_boot.py`, and validate the automated first-boot setup.
2. Run full kiosk smoke on the real Pi: Admin card, child cards, scanner, touch, checkout, recipe, math, debug PIN, update, and remote admin QR.
3. Add observations to issues #1, #2, and #7.
4. Add read-only transaction and earnings views before more write-heavy CRUD.
5. Split `src/utils/database.py` in a separate refactor pass when adding the next admin data path.
