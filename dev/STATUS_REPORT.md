# Project Status Report

**Date:** 2026-04-26

## Where The Project Stands

Carolin's Kasse is no longer a prototype skeleton. The core play flow is already present:

- user login via barcode cards
- main menu with shopping, recipe, and math flows
- cart and checkout logic with balance handling
- session and earnings tracking
- a new shell-based UI direction with dedicated scene artwork
- a small FastAPI admin backend for browsing products, users, and recipes

The local worktree also shows a major UI migration already in progress. That means the project is closer to a polish and integration phase than to early foundation work.

## What Looks Done

### Core Game Loop

- `main.py` boots the pygame app and scene manager.
- `src/scenes/` contains the active scene set used by the app flow: `start`, `login`, `menu`, `scan`, `recipe`, `math_game`, `picker`.
- `src/utils/state.py` and `src/utils/database.py` cover user state, sessions, earnings, and transactions.

### Asset and UI Direction

- `src/ui/shell.py` introduces a shared shell around scenes.
- `assets/340er/` and `assets/680er/` reflect the newer asset strategy.
- `src/utils/assets.py` supports runtime scaling and asset lookup for the new structure.
- The login flow uses the fullscreen `karte_scannen` artwork, while the app boot still begins with a short `startbildschirm` title sequence.
- `dev/assets/MATH_GAME_LAYOUT_SPEC.md` now documents a single-asset handoff for the math game redesign.
- The Kassen-UI and Rezept-UI now have asset-based implementations in the worktree.

### Admin Foundation

- `src/admin/server.py` provides read-only list pages for products, users, and recipes.
- Templates already exist in `src/admin/templates/`.
- Barcode conventions now have a single utility module in `src/utils/barcodes.py`.
- The seed and barcode scripts in `tools/` are part of the backend foundation and should be pushed with the next GitHub update.

## What Is Not Finished Yet

### Visual QA

The biggest missing step is a full visual pass through the app after the UI migration:

- scene layout consistency
- product and recipe image rendering
- footer and shell behavior
- touch and barcode interaction in the new layouts
- scan/cart readability for children who cannot read yet

### Admin Area

Phase 7 is only partially started. The current FastAPI admin is useful as a viewer, but not yet as a management tool.

Missing capabilities include:

- create and edit users
- create and edit products
- balance top-ups
- transaction views and statistics
- barcode generation and print workflows in the UI

### Backend Structure

The next backend pass should keep data concerns separated:

- schema/init and seed data
- product, user, recipe, transaction, and earning queries
- barcode generation and printable output
- admin page orchestration
- pygame scene state

Current refactor candidates:

- `src/utils/database.py` mixes schema creation, data models, CRUD, sessions, earnings, and checkout persistence.
- `src/admin/server.py` is still small, but list-page view shaping will grow quickly once forms and POST flows are added.
- `src/utils/state.py` uses module-level globals, which is acceptable for the kiosk loop now, but should not become the admin backend's state source.

### Documentation Consistency

The core tracked docs now describe the backend start more clearly. `dev/ARCHITECTURE.md` should be tracked with the next commit because the repository instructions require it during session start.

### Math Game Asset Delivery

The math game redesign now has reward coin assets wired into the scene:

- transparent `+1` and `+2` coin variants live in `assets/ui/rewards/`
- `MathGameScene` selects one stable reward coin per problem, places it near the equation, and falls back to a drawn badge if assets are missing
- correct answers trigger a sequenced non-text success animation: stars/confetti first, then a small coin transfer into the footer account area, then the reward is credited before the next problem loads
- the main layout still uses dynamic rendering inside the shared `FrameShell`; no separate math-game frame was added

### Cashier UI Asset Prep

The cashier UI has a screenshot-based baseline, a preferred visual direction, and a first implementation:

- reference screenshots live in `/tmp/carolins_kasse_cashier_verification/`
- reference-style mockups live in `/tmp/carolins_kasse_cashier_mockups/`
- implemented screenshots live in `/tmp/carolins_kasse_cashier_implementation/`
- cashier assets live in `assets/ui/cashier/`
- implementation stays inside the existing `ScanScene`/component boundaries and keeps `FrameShell` as the only shell, footer, and balance display
- the first visual-feedback pass fixed footer collisions, overflowing/truncated text behavior, checkout modal spacing, picker tab overlap, and receipt countdown placement
- the second visual-feedback pass added PNG-based panel, row, button, and checkout backgrounds; the empty cart hides the inactive pay button; the checkout receipt now uses two clear booking rows for payer and earner

### Recipe UI Asset Prep

The recipe UI now has a screenshot-based baseline, mockups, and a first asset-based implementation:

- reference screenshots live in `/tmp/carolins_kasse_recipe_verification/`
- recipe mockups live in `/tmp/carolins_kasse_recipe_mockups/`
- implemented screenshots live in `/tmp/carolins_kasse_recipe_implementation/`
- recipe assets live in `assets/ui/recipe/`
- implementation stays inside the existing recipe flow and uses `FrameShell` as the only shell, footer, and balance display
- recipe rows are now image-led with product artwork and large scan status cues instead of small checkbox/text rows
- the visual-feedback polish enlarged the recipe-card scan hint, aligned the panels more consistently, replaced the artifacted green check badge, and moved recipe cost into a compact coin badge
- shared checkout-button rendering now lives in `src/components/icon_pay_button.py` and is reused by scan and recipe scenes

## Recommended Next Steps

1. Run a manual UI smoke test in the pygame app on the real display and note any touch, scanner, or readability regressions.
2. Validate the new cashier and recipe UI on the 1024x600 touch display with scanner and kid-testing feedback; use issues #1 and #2 for observations.
3. Keep Phase 7 in the existing FastAPI admin and add backend forms there.
4. Add a small database migration/seed discipline before adding CRUD, so demo data and runtime data do not drift silently.
5. Split the next implementation cycle into one of these paths:

Path A: Finish UI polish and hardware validation first.
Path B: Expand the FastAPI admin into a true parent-facing management area.
Path C: Build printable barcode output first, then wire it into product/user/recipe CRUD.

## Notes For The Next Session

- The local UI migration and repo workflow cleanup are committed locally; push and visual QA are the next sensible steps after this cleanup commit.
- `AGENTS.md` is now the primary Codex instruction file.
- The previous local runtime/demo change in `data/kasse.db` was saved as `stash@{0}`. Do not treat runtime database drift as source-of-truth without deciding whether to preserve demo history or reset from seed.
- Follow-up issues created for the backend foundation: #3 demo database workflow, #4 database module split, #5 printable barcode workflow.
- If new follow-up work appears during testing, capture it as GitHub issues immediately.
