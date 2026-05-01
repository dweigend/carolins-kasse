# Carolin's Kasse

A Raspberry Pi toy checkout for Carolin and Annelie: real barcode scanner,
touch display, SQLite balances, shopping, recipes, math rewards, and a small
parent admin area.

## What Works

- Pygame kiosk app for the 1024x600 touch display.
- User card login, session tracking, balances, earnings, and transactions.
- Shopping flow with scanner, touch picker, cart, checkout, and insufficient-funds handling.
- Recipe mode with recipe cards and ingredient scanning.
- Math mode with difficulty per child and Taler rewards.
- FastAPI remote admin for products, users, recipes, barcodes, balances, and A4 print sheets.
- On-device pygame admin mode via Admin card `2000000000046`.

## Hardware

| Part | Model |
|---|---|
| Computer | Raspberry Pi Zero 2 W |
| Display | Elecrow 7" IPS Touch, 1024x600 |
| Power | Anker 20K 87W |
| USB hub under test | SEENGREAT Pi USB HUB Rev1.1 |
| Scanner | USB barcode scanner |
| Input | Touch plus optional USB numpad |
| USB debug kit | Micro-USB OTG adapter, simple USB mouse/keyboard, USB 2.0 stick |

USB topology on the Pi Zero 2 W is intentionally strict: when the SEENGREAT
shield is in Pi Zero hub mode, all USB peripherals must be plugged into the
shield. Do not use the Pi's micro-USB data port at the same time; it is the
same single USB bus as the shield pogo-pin upstream.

## Setup

Local development:

```bash
uv sync
uv run python tools/seed_database.py
uv run python tools/generate_barcodes.py
uv run python main.py
```

`tools/seed_database.py` is non-destructive by default. It keeps the current
Carolin/Annelie setup and refuses to overwrite existing balances, sessions,
earnings, or transactions. Use `--reset` only for an intentional full rebuild.

Raspberry Pi first-boot setup is documented in `docs/PI_SETUP.md`. The automated
path uses Raspberry Pi OS Lite 64-bit, `tools/pi_prepare_boot.py`, and systemd
services to install and start the kiosk after first boot.

For hardware bring-up, keep local-only notes, secrets, logs, and scripts under
`dev/local-debug/`. That directory is intentionally ignored by Git.

## Admin

```bash
# Local browser
uv run uvicorn src.admin.server:app --reload --port 8080

# Phone on the home network
uv run uvicorn src.admin.server:app --host 0.0.0.0 --port 8080

# Printable A4 PDFs
uv run python tools/generate_printables.py
```

At the kiosk, scan the Admin card (`2000000000046`) on the login screen. The
pygame admin mode can start/stop the remote admin server, show a QR code for
`http://<pi-ip>:8080`, and adjust existing user balances quickly.

The browser admin also includes a PIN-protected `/debug` page on Raspberry Pi
installations. It shows service status, logs, backups, SSH details, and can
start backup/update/restart actions.

## Barcode Prefixes

- `100`: products
- `200`: users
- `300`: recipes

## Project Docs

- `AGENTS.md`: repository instructions for Codex work.
- `dev/HANDOVER.md`: current state and next steps.
- `dev/PLAN.md`: active roadmap.
- `dev/ARCHITECTURE.md`: system boundaries and runtime flows.

Historical design drafts were removed from the active docs to keep the repo
lean. Use Git history if an old concept is needed again.
