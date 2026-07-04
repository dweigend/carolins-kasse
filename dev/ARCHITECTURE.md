# Architecture

## Runtime Shape

```text
main.py
  ├─ FrameShell renders paper background, user frame, title, close button, footer
  ├─ SceneManager owns the active pygame scene and lazy scene factories
  ├─ src/utils/state.py owns current user/session/cart runtime state
  └─ src/utils/database.py persists SQLite data using focused database helper modules
```

SceneManager calls optional scene lifecycle hooks. `on_enter()` runs when a
scene becomes active. `reset_user_state()` runs on kiosk user changes and shell
logout so scenes can clear user-bound state without losing normal entry state.
It accepts either prebuilt scene instances or factories. Factories are built on
first scene entry and then cached, keeping non-start scenes out of the kiosk
cold path while preserving scene-local state between normal navigation steps.

Active scenes:

- `start`: splash screen
- `login`: scans user/admin cards
- `admin`: on-device parent admin
- `menu`: mode selection
- `scan`: shopping and cart
- `picker`: touch product selection
- `recipe`: recipe card and ingredient scanning
- `math_game`: math rewards

ScanScene can route to PickerScene for touch product selection without losing
the current cart. MathGameScene filters fast scanner-style digit bursts,
including unterminated bursts, so barcode input does not become a math answer.
The kiosk entry point eagerly creates only `StartScene`; login, admin, menu,
scan, picker, recipe, and math scenes are constructed on first use. This keeps
the admin QR stack (`qrcode`/Pillow) and other non-start scene setup outside
`import main` and the first visible splash frame.

## Render Boundary

Scenes render only their content. The shared shell renders around them:

1. `FrameShell.render_background(screen)`
2. `Scene.render(screen)`
3. `FrameShell.render_overlay(screen, current_user, scene_name)`

Scenes in `NO_FRAME_SCENES` (`start`, `login`) do not show the shell overlay.

Target display is fixed at `1024x600`.

## Data Model

SQLite tables:

- `products`: barcode, English asset key, German name, price, category, image path, barcode flag, active flag
- `users`: card ID, name, balance, color, difficulty, admin flag, active flag
- `recipes`: barcode, name, image path, active flag
- `recipe_ingredients`: recipe/product relation with quantity
- `sessions`: login/logout sessions
- `earnings`: math/cashier/time rewards
- `transactions`: purchases with JSON item payload
- `balance_adjustments`: manual admin balance changes

Current technical debt: `src/utils/database.py` still contains schema, checkout,
and transaction boundaries. Row dataclasses and checkout result/error types live in
`src/utils/database_models.py`; product query helpers live in
`src/utils/database_products.py`; recipe query helpers live in
`src/utils/database_recipes.py`; basic user CRUD query helpers live in
`src/utils/database_users.py`; session query helpers live in
`src/utils/database_sessions.py`; earning helpers live in
`src/utils/database_earnings.py`; transaction helpers, including
`save_transaction`, live in `src/utils/database_transactions.py`; balance
adjustment query and write helpers live in
`src/utils/database_balance_adjustments.py`. Public names are still re-exported
or wrapped from `src/utils/database.py` for import compatibility; the public
`process_checkout` and `update_user_balance` wrappers stay there with
`get_db()`, `BEGIN IMMEDIATE`, commit, and rollback.
Continue splitting only in small behavior-preserving slices.

SQLite connections enable foreign key checks and a short busy timeout. Checkout
writes use `BEGIN IMMEDIATE` so the transaction, balance update, earnings or
transaction records, and runtime refresh succeed or fail together. The checkout
API returns `CheckoutResult` for successful commits and `CheckoutError` for
user-facing failure cases. `process_checkout` delegates the transaction row
write to `database_transactions.save_transaction()` inside the same SQLite
transaction.

## Barcode Rules

Internal EAN-13 prefixes:

| Prefix | Meaning |
|---|---|
| `100` | Products |
| `200` | Users |
| `300` | Recipes |

`src/utils/barcodes.py` owns prefix rules, check digit handling, generated SVG
paths, and admin barcode URLs. Generated SVGs live under `data/barcodes/`.

## Admin Architecture

There are two admin surfaces with different jobs:

```text
Admin card scan
  └─ pygame AdminScene
       ├─ shows home-network IP and admin URL QR
       ├─ starts/stops managed FastAPI server process
       ├─ adjusts existing user balances
       └─ shows latest manual balance change

Phone/browser on same WiFi
  └─ FastAPI app at http://<pi-ip>:8080
       ├─ products
       ├─ users
       ├─ recipes
       ├─ barcode downloads
       ├─ CSRF-protected mutating POST routes
       ├─ PIN-protected debug and operations status
       └─ A4 printable PDFs
```

The Pi remains on the home WiFi. There is no hotspot in v1. Remote read pages
stay lightweight for the home network, while mutating browser POST routes require
the locally generated debug PIN/admin session cookie plus a CSRF token.
`/debug/unlock` validates CSRF before accepting a PIN.

Admin templates should pass dynamic barcode modal data through HTML data
attributes rather than inline JavaScript string arguments.

The PIN-protected debug page is the browser-facing operations dashboard. It
reports kiosk service state, systemd availability, install/update/backup
service state, backup timer state, failed units, and bounded log snippets. It
should degrade gracefully when running off-Pi or without systemd access.

## Setup And Generated Outputs

```text
tools/seed_database.py       -> initializes missing/empty data/kasse.db
tools/generate_barcodes.py   -> writes SVG barcodes from DB contents
tools/generate_printables.py -> writes A4 PDFs under data/print/
tools/pi_prepare_boot.py     -> prepares Raspberry Pi bootfs for first install
tools/pi_firstboot.sh        -> bootfs first-boot entrypoint copied by prepare
tools/pi_bootstrap.sh        -> first Pi install into /opt/carolins-kasse
tools/pi_update.sh           -> backup, pull, sync, verify, rollback, restart
tools/pi_backup.sh           -> SQLite backup helper
tools/pi_debug.py            -> read-only SSH diagnostics
```

`tools/seed_database.py` is non-destructive unless called with `--reset`.
Runtime DB changes, generated PDFs, and generated barcode outputs should not be
treated as source-of-truth code changes.

Pi installations set `CAROLINS_KASSE_DB_PATH=/var/lib/carolins-kasse/kasse.db`
so balances and sessions survive Git updates outside the source checkout.
Local development keeps the default `data/kasse.db` path.

`tools/pi_update.sh` records the previous Git commit before pulling. If a
post-pull step fails, including the no-op pull failure path, it resets back to
that commit and restarts the kiosk only after a successful rollback.

Systemd units live under `systemd/`:

- `carolins-kasse.service`: starts the pygame kiosk.
- `carolins-kasse-backup.service` and `.timer`: daily SQLite backups.
- `carolins-kasse-update.service`: manually triggered GitHub update.
- `carolins-install.service`: temporary first-install service.

## Module Responsibilities

| Area | Responsibility |
|---|---|
| `src/scenes/` | Scene-specific input/update/render flow |
| `src/components/` | Reusable pygame UI pieces |
| `src/ui/` | Shell, paper texture, shared rendering helpers |
| `src/admin/` | FastAPI app, templates, static CSS |
| `src/utils/database.py` | Public SQLite API, connection, schema, commit/rollback, checkout, and transaction boundaries |
| `src/utils/database_models.py` | Database row dataclasses, column lists, and checkout result/error types |
| `src/utils/database_products.py` | Product SQL helpers that receive an existing connection and do not commit |
| `src/utils/database_recipes.py` | Recipe SQL helpers that receive an existing connection and do not commit |
| `src/utils/database_users.py` | Basic user CRUD SQL helpers that receive an existing connection and do not commit |
| `src/utils/database_sessions.py` | Session SQL helpers that receive an existing connection and do not commit |
| `src/utils/database_earnings.py` | Earning SQL helpers that receive an existing connection and do not commit |
| `src/utils/database_transactions.py` | Transaction SQL helpers, including `save_transaction`, that receive an existing connection and do not commit |
| `src/utils/database_balance_adjustments.py` | Balance adjustment SQL query/write helpers that receive an existing connection and do not commit |
| `src/utils/barcodes.py` | Barcode rules and generated SVG paths |
| `src/utils/admin_runtime.py` | Managed FastAPI server start/stop for pygame admin |
| `src/utils/network.py` | Local IP and admin URL helpers |
| `src/utils/pi_system.py` | Pi diagnostics, admin PIN validation, system actions |
| `tools/` | Operational scripts for setup, barcodes, printables |
| `tests/` | unittest temp-DB smoke and safety coverage |

## Test Structure

Tests use the Python standard library `unittest` stack and temporary SQLite
databases. They should not touch `data/kasse.db` and should avoid new test
dependencies unless there is a clear payoff. Current coverage focuses on
database smoke behavior, atomic checkout safety, checkout rollback on
transaction-save failure, self-checkout balance refresh, local-day earning
queries, admin POST/session/CSRF safety, Pi update rollback behavior, and debug
status observability.

Pi update rollback tests keep fake system tools and app hooks as executable
shell fixtures under `tests/fixtures/pi_update/`. Python tests should assemble
the fixture environment, run the real script, and assert behavior instead of
embedding shell script bodies in test code.

## Refactor Rules

- Keep behavior stable.
- Prefer deleting stale code/docs over wrapping them.
- Extract helpers only when they reduce real complexity.
- For refactors, track the ratio of added vs. removed lines; net-smaller is a useful signal, though not the only goal.
- Keep runtime data out of commits.
