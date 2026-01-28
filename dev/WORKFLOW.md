# Development Workflow

## Session Flow

```
START → Read Plan/Architecture/Handover → Reflect → Code → Issues → Handover → END
```

## 🎯 GitHub Issues = Standard

**During work, immediately create issues for:**
- Bugs discovered
- Ideas that pop up
- Questions needing answers
- Things to test with kids

```bash
gh issue create --title "..." --label "bug"
gh issue create --title "..." --label "enhancement"
gh issue create --title "..." --label "needs-testing"
```

**Don't interrupt your flow!** Note it as issue, continue working.

## Before Ending Session

1. All changes committed
2. `dev/HANDOVER.md` updated
3. `dev/ARCHITECTURE.md` updated if structure changed
4. New issues created for discovered work

## Commit Convention

```
feat: ✨ New feature
fix: 🐛 Bug fix
refactor: ♻️ Code restructure
docs: 📝 Documentation
chore: 🔧 Maintenance
```

## Testing

- No unit tests (pygame is hard to test)
- Manual testing on Mac (windowed)
- Real testing on Pi with kids
- Create `needs-testing` issues for kid-testing
