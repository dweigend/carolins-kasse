# Development Workflow

## Session Flow

```text
START
  ↓
Read AGENTS.md
  ↓
Read dev/HANDOVER.md + dev/PLAN.md
  ↓
Check gh issue list
  ↓
Check git status
  ↓
Implement + verify
  ↓
Update dev/HANDOVER.md (+ dev/STATUS_REPORT.md if priorities changed)
  ↓
END
```

## Codex Source of Truth

- `AGENTS.md` is the primary assistant instruction file for this repository.
- Keep project workflow instructions in `AGENTS.md` and `dev/` docs, not in tool-specific config folders.
- If process rules change, update `AGENTS.md` first.

## GitHub Issues = Standard

Create issues immediately for:

- bugs discovered during development
- ideas worth preserving
- questions that need a later decision
- anything that should be validated with kids on real hardware

```bash
gh issue create --title "Bug: Scanner doesn't read barcode" --label "bug"
gh issue create --title "Idea: Sound on login" --label "enhancement"
gh issue create --title "Test: Touch vs Numpad for picker" --label "needs-testing"
```

## Before Ending a Session

1. Run the relevant checks.
2. Update `dev/HANDOVER.md`.
3. Update `dev/ARCHITECTURE.md` if structure changed.
4. Update `dev/STATUS_REPORT.md` if the practical project status or priorities changed.
5. Create issues for newly discovered follow-up work.

## Git Workflow

### Commit Format

```text
type: emoji description
```

| Type | Emoji | Use |
|------|-------|-----|
| feat | ✨ | New feature |
| fix | 🐛 | Bug fix |
| refactor | ♻️ | Restructure |
| docs | 📝 | Documentation |
| chore | 🔧 | Maintenance |
| checkpoint | 📍 | Snapshot before big changes |
| assets | 🎨 | Asset changes |

### Issue Labels

| Label | Use |
|-------|-----|
| `bug` | Something broken |
| `enhancement` | Feature idea |
| `needs-testing` | Test with kids |
| `question` | Decision needed |

## Testing

- No unit tests by default; pygame flows are verified manually.
- Linting is mandatory.
- Manual testing on Mac is fine for layout and scene flow.
- Real validation on Raspberry Pi remains important for touch, scanner, performance, and fullscreen behavior.
