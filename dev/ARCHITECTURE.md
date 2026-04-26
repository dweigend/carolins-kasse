# Architecture

## Runtime Shape

```text
main.py
  ├─ FrameShell renders paper background, user frame, title, close button, footer
  ├─ SceneManager owns the active pygame scene
  ├─ src/utils/state.py owns current user/session/cart runtime state
  └─ src/utils/database.py persists SQLite data
```

Active scenes:

- `start`: splash screen
- `login`: scans user/admin cards
- `admin`: on-device parent admin
- `menu`: mode selection
- `scan`: shopping and cart
- `picker`: touch product selection
- `recipe`: recipe card and ingredient scanning
- `math_game`: math rewards

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

Current technical debt: `src/utils/database.py` contains schema, dataclasses,
queries, and runtime persistence. Split this in a future dedicated pass.

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
       └─ A4 printable PDFs
```

The Pi remains on the home WiFi. There is no hotspot in v1. Remote admin has no
HTTP login in v1; the intended protection is local network access plus the
physical Admin card flow.

## Setup And Generated Outputs

```text
tools/seed_database.py       -> initializes missing/empty data/kasse.db
tools/generate_barcodes.py   -> writes SVG barcodes from DB contents
tools/generate_printables.py -> writes A4 PDFs under data/print/
```

`tools/seed_database.py` is non-destructive unless called with `--reset`.
Runtime DB changes, generated PDFs, and generated barcode outputs should not be
treated as source-of-truth code changes.

## Module Responsibilities

| Area | Responsibility |
|---|---|
| `src/scenes/` | Scene-specific input/update/render flow |
| `src/components/` | Reusable pygame UI pieces |
| `src/ui/` | Shell, paper texture, shared rendering helpers |
| `src/admin/` | FastAPI app, templates, static CSS |
| `src/utils/database.py` | Current SQLite boundary, to be split later |
| `src/utils/barcodes.py` | Barcode rules and generated SVG paths |
| `src/utils/admin_runtime.py` | Managed FastAPI server start/stop for pygame admin |
| `src/utils/network.py` | Local IP and admin URL helpers |
| `tools/` | Operational scripts for setup, barcodes, printables |

## Refactor Rules

- Keep behavior stable.
- Prefer deleting stale code/docs over wrapping them.
- Extract helpers only when they reduce real complexity.
- For refactors, track the ratio of added vs. removed lines; net-smaller is a useful signal, though not the only goal.
- Keep runtime data out of commits.
