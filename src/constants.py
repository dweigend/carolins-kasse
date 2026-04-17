"""Global constants for Carolin's Kasse."""

# ─── DISPLAY ──────────────────────────────────────────────────
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
FPS = 30

# ─── COLORS: Basic Palette ────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_PINK = (255, 218, 233)

# ─── COLORS: Brand & Semantic ─────────────────────────────────
PRIMARY = (59, 130, 246)  # Blue (headers, links)
SUCCESS = (34, 197, 94)  # Green (confirmation, positives)
DANGER = (239, 68, 68)  # Red (errors, cancel)
WARNING = (245, 158, 11)  # Orange (warnings, alerts)

# ─── COLORS: Brand (User-Specific) ────────────────────────────
# Used for avatar rings, backgrounds, UI elements
ORANGE = (245, 130, 10)
ORANGE_DARK = (212, 100, 8)
RED = (220, 53, 69)
RED_DARK = (180, 35, 50)
BLUE = (66, 135, 245)
BLUE_DARK = (40, 100, 210)

# ─── COLORS: Neutrals ─────────────────────────────────────────
CREAM = (253, 246, 236)  # Paper background texture
GREY_LIGHT = (240, 240, 240)
GREY_MEDIUM = (180, 180, 180)
GREY_DARK = (100, 100, 100)

# ─── COLORS: Background & Text ────────────────────────────────
BG_LIGHT = (240, 240, 245)  # Light background (scenes)
BG_CARD = (255, 255, 255)  # Card/panel background
TEXT_PRIMARY = (30, 30, 30)  # Primary text color
TEXT_SECONDARY = (100, 100, 100)  # Secondary text
TEXT_MUTED = (150, 150, 150)  # Muted/disabled text

# ─── LAYOUT: Old System (kept for compatibility) ───────────────
HEADER_HEIGHT = 80  # Top area height (legacy)
PADDING = 20  # General padding
FRAME_MARGIN = 50  # Frame margin from edges

# ─── LAYOUT: New System (Phase 6.1) ──────────────────────────
HEADER_HEIGHT_NEW = 72  # New UI header height
FRAME_BORDER = 24  # Orange frame border width
FOOTER_HEIGHT = 60  # Bottom area height

# ─── ECONOMY: Activity Earnings ────────────────────────────────
EARNING_MATH: dict[int, int] = {1: 1, 2: 2, 3: 3}  # Easy=1, Medium=2, Hard=3 Taler
EARNING_CASHIER = 5  # 1x Kassieren = 5 Taler
EARNING_RECIPE = 8  # 1x Rezept = 8 Taler
EARNING_TIME_SECONDS = 600  # 10 min = 1 Taler

# ─── ECONOMY: Balance System ──────────────────────────────────
BALANCE_BAR_MAX = 50  # Full bar = 50 Taler

# Balance thresholds (when bar color changes)
BALANCE_THRESHOLD_LOW = 10  # < 10 = red
BALANCE_THRESHOLD_MED = 25  # 10-25 = yellow, > 25 = green

# Balance bar colors
BALANCE_COLOR_LOW = (220, 38, 38)  # Red
BALANCE_COLOR_MED = (234, 179, 8)  # Yellow
BALANCE_COLOR_HIGH = (34, 197, 94)  # Green
BALANCE_COLOR_BG = (229, 231, 235)  # Light gray background

# ─── SHELL: Frame & Avatar Mapping ───────────────────────────
# Maps user colors to frame asset filenames (hintergrund/ directory)
COLOR_TO_FRAME: dict[str | None, str] = {
    "#0066CC": "hintergrund/linie_blau",  # Carolin (Blau)
    "#CC3333": "hintergrund/linie_rot",  # Annelie (Rot)
    "#888888": "hintergrund/linie_blau",  # Gast (fallback to blue)
    "#FFD700": "hintergrund/linie_orange",  # Admin (Gold/Orange)
    None: "hintergrund/linie_blau",  # Default fallback
}

# Avatar image per user name (680er/ directory)
USER_AVATAR: dict[str, str] = {
    "Carolin": "680er/avata_carolin",
    "Annelie": "680er/avata_annelie",
}

# Title text color per frame asset (matches frame color)
FRAME_TITLE_COLOR: dict[str, tuple[int, int, int]] = {
    "hintergrund/linie_blau": BLUE,
    "hintergrund/linie_rot": RED,
    "hintergrund/linie_orange": ORANGE,
}

# ─── SHELL: Layout Constants ────────────────────────────────
SHELL_TITLE_POS = (420, 5)  # Title text position in top notch
SHELL_CLOSE_POS = (960, 20)  # Close button (X) position
SHELL_AVATAR_SIZE = 50  # Small avatar in header
SHELL_AVATAR_POS = (360, 2)  # Avatar position (left of title)
SHELL_MONEY_ICON_X = 385  # Money icon X position in footer
SHELL_MONEY_ICON_Y = SCREEN_HEIGHT - 48  # Money icon Y position
SHELL_PROGRESS_X = 430  # Progress bar X in footer
SHELL_PROGRESS_Y = SCREEN_HEIGHT - 38  # Progress bar Y in footer
SHELL_PROGRESS_W = 170  # Progress bar width
SHELL_PROGRESS_H = 20  # Progress bar height
SHELL_COUNT_X = 605  # Count text X in footer
SHELL_COUNT_Y = SCREEN_HEIGHT - 46  # Count text Y in footer
