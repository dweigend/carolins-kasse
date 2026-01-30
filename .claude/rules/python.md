# Python Stack Rules

## Package Management

- **ALWAYS** use `uv` (never pip!)
- Add dependencies: `uv add <package>`
- Run scripts: `uv run python <script>`

## Code Quality

```bash
# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Both
uv run ruff check src/ && uv run ruff format src/
```

## Style

- Python 3.12+
- Type hints on all functions
- Docstrings for public functions (English)
- Max line length: 88 (ruff default)

## Pygame Specifics

- No type stubs available → skip ty for now
- Manual testing instead of unit tests
- Use `pygame.SCALED` for resolution independence

## Common Patterns

```python
# Early returns
def process_input(event: pygame.event.Event) -> bool:
    if event.type != pygame.KEYDOWN:
        return False
    # ... handle keydown

# Type hints
def load_product(barcode: str) -> Product | None:
    ...

# Constants at module level
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
```
