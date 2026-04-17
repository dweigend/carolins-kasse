# Carolin's Kasse for Codex

## Communication

- Chat with me in German.
- Write code, file names, commit messages, pull requests, and code comments in English.

## Repository First

Always inspect the repository before changing anything.

### Session Start

1. Read `dev/HANDOVER.md`.
2. Read `dev/PLAN.md`.
3. Read `dev/ARCHITECTURE.md` if structure or responsibilities matter for the task.
4. Run `gh issue list --limit 20` for project context.
5. Run `git status --short --branch` before editing files.

### Before Ending a Session

1. Run the relevant checks.
2. Update `dev/HANDOVER.md`.
3. Add or update follow-up notes in `dev/STATUS_REPORT.md` if priorities changed.
4. Create GitHub issues for newly discovered bugs, ideas, or kid-testing tasks.

## Core Principles

- Prefer readable, maintainable, well-structured code over clever code.
- Keep solutions simple. Reuse existing project code before introducing new abstractions.
- Preserve the current architecture, design language, and project conventions unless there is a strong reason to change them.
- Do not add dependencies when the standard library or already-installed packages are enough.

## Project Context

- Stack: Python + `pygame-ce` + SQLite + FastAPI admin pages
- Package manager: `uv`
- Target hardware: Raspberry Pi Zero 2 W with 1024x600 touch display
- Primary app entry point: `main.py`
- Admin entry point: `uv run uvicorn src.admin.server:app --reload --port 8080`

## Current Structure

```text
src/
├── admin/         # FastAPI admin pages and templates
├── components/    # Reusable pygame UI pieces
├── scenes/        # Scene flow and screen-specific logic
├── ui/            # Shared shell and rendering helpers
└── utils/         # State, database, assets, fonts, layout helpers
assets/
├── 40er/          # Small icons
├── 50er/          # Small UI assets
├── 340er/         # Product images
└── 680er/         # Scene and recipe artwork
data/              # SQLite DB and generated barcodes
dev/               # Project docs, plans, handover, status report
tools/             # Seed and helper scripts
```

## Implementation Priorities

1. Reuse existing scene, component, or utility patterns.
2. Extend current code paths instead of adding parallel systems.
3. Keep business logic, rendering, and persistence concerns separated.
4. Prefer early returns and explicit names.
5. Keep UI text in German. Keep code and comments in English.

## Python Rules

- Use `uv`, never `pip`.
- Run scripts with `uv run`.
- Keep type hints where they improve clarity and correctness.
- Add short English docstrings for shared or non-obvious public APIs.
- No `ty` by default here; `pygame` typing is still incomplete.

## Verification

Run the repository checks first:

```bash
uv run ruff check src/
uv run ruff format src/
```

When relevant, also run:

```bash
uv run python main.py
uv run uvicorn src.admin.server:app --reload --port 8080
```

Manual testing is expected for pygame flows, especially for scene navigation, touch input, barcode scanning, and layout on the 1024x600 target size.

## Git Workflow

- Keep the tree understandable and avoid touching unrelated user changes.
- Before substantial work, create a safe git checkpoint when the worktree allows it.
- Use concise English commit messages.
- Never mention AI, Codex, Claude, or generated code in commits or pull requests.

## Issue Workflow

Create GitHub issues immediately for:

- bugs discovered during development
- new feature ideas
- decisions that need follow-up
- anything that should be tested with kids on real hardware

Example:

```bash
gh issue create --title "Bug: Scanner doesn't read barcode" --label "bug"
gh issue create --title "Idea: Sound on login" --label "enhancement"
gh issue create --title "Test: Touch vs Numpad for picker" --label "needs-testing"
```
