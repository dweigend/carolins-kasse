# Carolin's Kasse for Codex

## Communication

- Chat with me in German.
- Write code, file names, commit messages, pull requests, and code comments in English.
- Keep UI text in German.

## Session Start

1. Read `dev/HANDOVER.md`.
2. Read `dev/PLAN.md`.
3. Read `dev/ARCHITECTURE.md` when structure or responsibilities matter.
4. Run `gh issue list --limit 20`.
5. Run `git status --short --branch` before editing files.

## Before Ending

1. Run relevant checks.
2. Update `dev/HANDOVER.md`.
3. Update `dev/PLAN.md` or `dev/ARCHITECTURE.md` only when priorities or structure changed.
4. Create GitHub issues for newly discovered bugs, ideas, decisions, or hardware/kid tests.

## Project Context

- Stack: Python, `pygame-ce`, SQLite, FastAPI, Jinja2.
- Package manager: `uv`.
- Target: Raspberry Pi Zero 2 W with 1024x600 touch display.
- Kiosk entry point: `main.py`.
- Remote admin entry point: `uv run uvicorn src.admin.server:app --reload --port 8080`.

## Structure

```text
src/
├── admin/         # FastAPI admin pages and templates
├── components/    # Reusable pygame UI pieces
├── scenes/        # Scene flow and screen logic
├── ui/            # Shared shell and rendering helpers
└── utils/         # State, database, assets, fonts, layout helpers
assets/            # Product, scene, UI, font assets
data/              # Local SQLite DB and generated barcodes
dev/               # Active docs only: handover, plan, architecture
tools/             # Seed, barcode, print helper scripts
```

## Engineering Rules

- Inspect existing patterns before changing architecture.
- Prefer readable, maintainable code over clever code.
- Reuse project code first, then standard library, then installed dependencies.
- Add new dependencies only when clearly justified.
- Keep business logic, rendering, persistence, and orchestration separated.
- Prefer early returns, explicit names, and small functions.
- Refactors should reduce real complexity; avoid abstraction that only adds lines.

## Python Rules

- Use `uv`, never `pip`.
- Run scripts with `uv run`.
- Use type hints where they improve readability or correctness.
- Add short English docstrings for shared or non-obvious public APIs.
- No `ty` by default; pygame typing is still incomplete.

## Verification

Run at least:

```bash
uv run ruff check src/ tools/
uv run ruff format src/ tools/
uv run python -m compileall src tools
```

When relevant, also run targeted smoke tests for pygame scenes, barcode flows,
admin pages, print generation, and database safety. Manual Pi validation remains
required for scanner, touch, fullscreen behavior, and performance.

## Git Workflow

- Keep unrelated local changes untouched; `data/kasse.db` often has runtime drift.
- Stage explicit files only.
- Commit completed, meaningful units promptly.
- Use concise English commit messages.
- Never mention AI, Codex, Claude, or generated code in commits or PRs.
- Never use destructive git commands unless explicitly requested.

## Issue Workflow

Create GitHub issues immediately for:

- bugs discovered during development
- feature ideas worth preserving
- decisions that need follow-up
- anything to validate with children or real hardware

```bash
gh issue create --title "Bug: Scanner doesn't read barcode" --label "bug"
gh issue create --title "Test: Touch targets on admin screen" --label "needs-testing"
```
