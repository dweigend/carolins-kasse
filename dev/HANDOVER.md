# Session Handover

**Last Updated:** 2026-04-26 11:10 CEST

## Current State

- Core kiosk flows are implemented: login, menu, shopping/scan, picker, checkout, recipe mode, math mode, sessions, earnings, transactions, and balances.
- The shell-based 1024x600 UI is in place. Cashier and recipe UIs have had local screenshot/smoke validation, but still need real Pi/touch/scanner/kid testing.
- FastAPI remote admin is usable on the home network for products, users, recipes, balances, barcode downloads, and A4 print PDFs.
- Pygame admin mode opens with Admin card `2000000000046` and provides server status/QR, balance controls, account overview, and notes.
- Database setup is KISS: one local `data/kasse.db`, fixed Carolin/Annelie initial setup, non-destructive seed script by default.
- `data/kasse.db` may contain local runtime changes and should not be committed accidentally.

## Recent Completed Work

- Added non-destructive `tools/seed_database.py` workflow and central barcode rules in `src/utils/barcodes.py`.
- Added FastAPI admin write flows, balance history, minimal edits, SVG barcode links, and A4 print generation.
- Added on-device Pygame admin mode and refactored its rendering helpers.
- Merged User and Konten into one Pygame admin tab with safer bottom spacing.
- Cleaned active documentation down to `AGENTS.md`, `README.md`, `dev/HANDOVER.md`, `dev/PLAN.md`, and `dev/ARCHITECTURE.md`.

## Verification Run Recently

- `uv run ruff check src/ tools/`
- `uv run ruff format src/ tools/`
- `uv run python -m compileall src tools`
- AdminScene smoke against a temporary DB: tabs render, buttons register, `+1` changes balance correctly.
- Remote admin smoke: managed server starts, `/users` returns 200, stop terminates the managed process.
- Seed safety smoke: setup refuses to overwrite existing runtime data unless `--reset` is passed.

## Open GitHub Issues

- #1 Validate cashier UI with kids on touch display
- #2 Validate recipe UI with kids on touch display
- #4 Split database module for admin backend

Closed in this phase:

- #3 Demo database workflow
- #5 Printable barcode workflow
- #6 On-device Pygame admin mode

## Known Risks

- `src/utils/database.py` is still the largest mixed-responsibility module. Split it only when the next write path makes the boundary obvious.
- Hardware behavior is not fully validated: scanner timing, touch target precision, fullscreen rendering, Pi performance, and child comprehension still need real tests.
- Remote admin has no web login by design. Access is protected by local/home-network context and the Admin card flow, not by HTTP auth.
- Generated runtime outputs (`data/print/*.pdf`, barcode files, local DB changes) must stay separate from source changes.

## Next Best Steps

1. Run full kiosk smoke on the real Pi: Admin card, child cards, scanner, touch, checkout, recipe, math, and remote admin QR.
2. Add observations to issues #1 and #2.
3. Add read-only transaction and earnings views before more write-heavy CRUD.
4. Split `src/utils/database.py` in a separate refactor pass when adding the next admin data path.
5. Keep future refactors net-slim where possible: fewer lines or clearly less complexity at unchanged behavior.
