# Carolin's Kasse 🛒

A playful self-service checkout for kids' toy shop running on Raspberry Pi Zero.

## Author

- **Email**: david.weigend@gmail.com
- **GitHub**: [dweigend](https://github.com/dweigend)
- **Website**: [weigend.studio](https://weigend.studio)

## Quick Reference

| Aspect | Details |
|--------|---------|
| **Stack** | Python 3.12 + pygame + sqlite3 |
| **Package Manager** | uv (NOT pip!) |
| **Display** | 1024x600 (Elecrow 7" IPS touch) |
| **Target** | Raspberry Pi Zero 2 W |
| **Power** | Anker 20K 87W (~20h runtime) |

## 🎯 GitHub Issues First!

**Every problem, idea, bug → immediately create a GitHub Issue!**

```bash
gh issue create --title "Bug: Scanner doesn't read barcode" --label "bug"
gh issue create --title "Idea: Sound on login" --label "enhancement"
gh issue create --title "Test: Touch vs Numpad for picker" --label "needs-testing"
```

**Why?** Stay focused on current task. Nothing gets lost. Each issue = potential session.

## Language Conventions

| Area | Language | Example |
|------|----------|---------|
| Code | English | `def scan_product():` |
| Variables | English | `user_balance` |
| Comments | English | `# Check barcode` |
| Git commits | English | `feat: ✨ add recipe mode` |
| **UI texts** | **German** | "Hallo Carolin!" |
| **Products** | **German** | "Milch", "Eier" |
| **Errors** | **German** | "Guthaben reicht nicht!" |

## Commands

```bash
# Run app
uv run python main.py

# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

## Project Structure

```
src/
├── scenes/          # Screen states (login, menu, scan, etc.)
├── components/      # Reusable UI elements
└── utils/           # Helpers (input, database, etc.)
assets/
├── products/        # Product images
├── sounds/          # Audio files
└── fonts/           # Custom fonts
data/                # SQLite database
dev/                 # Documentation
ui/                  # UI mockups (reference)
```

## Session Workflow

1. Read `dev/HANDOVER.md` first
2. Check GitHub Issues for context
3. Work on task
4. Update `dev/HANDOVER.md` before ending

## Input Methods

- **Barcode Scanner**: Products & user cards
- **Numpad**: Menu navigation, quantities, math games
- **Touch**: Complex selections (product picker)

## Notes

- No unit tests initially (pygame is hard to test, manual testing instead)
- No ty initially (pygame lacks type stubs)
- Dev on Mac: windowed mode; on Pi: KMSDRM fullscreen
