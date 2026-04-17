# Project Status Report

**Date:** 2026-04-17

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
- `src/scenes/` contains the active scene set: `start`, `login`, `menu`, `scan`, `recipe`, `math_game`, `picker`.
- `src/utils/state.py` and `src/utils/database.py` cover user state, sessions, earnings, and transactions.

### Asset and UI Direction

- `src/ui/shell.py` introduces a shared shell around scenes.
- `assets/340er/` and `assets/680er/` reflect the newer asset strategy.
- `src/utils/assets.py` supports runtime scaling and asset lookup for the new structure.

### Admin Foundation

- `src/admin/server.py` provides read-only list pages for products, users, and recipes.
- Templates already exist in `src/admin/templates/`.

## What Is Not Finished Yet

### Visual QA

The biggest missing step is a full visual pass through the app after the UI migration:

- scene layout consistency
- product and recipe image rendering
- footer and shell behavior
- touch and barcode interaction in the new layouts

### Admin Area

Phase 7 is only partially started. The current FastAPI admin is useful as a viewer, but not yet as a management tool.

Missing capabilities include:

- create and edit users
- create and edit products
- balance top-ups
- transaction views and statistics
- barcode generation and print workflows in the UI

### Documentation Consistency

Some developer docs still describe older intermediate states. The codebase and the docs should be aligned before the next larger implementation phase.

## Recommended Next Steps

1. Run a manual UI smoke test in the pygame app and note any layout or navigation regressions.
2. Verify the FastAPI admin locally and decide whether Phase 7 should continue there.
3. Clean up stale planning and architecture docs so the current state is obvious to future sessions.
4. Split the next implementation cycle into one of these paths:

Path A: Finish UI polish and hardware validation first.
Path B: Expand the FastAPI admin into a true parent-facing management area.

## Notes For The Next Session

- The local UI migration and repo workflow cleanup are committed together; push and visual QA are the next sensible steps.
- `AGENTS.md` is now the primary Codex instruction file.
- If new follow-up work appears during testing, capture it as GitHub issues immediately.
