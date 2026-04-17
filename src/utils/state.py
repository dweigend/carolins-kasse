"""Simple shared state between scenes."""

from datetime import datetime

from src.utils.database import (
    Earning,
    Product,
    User,
    add_earning as db_add_earning,
    end_session as db_end_session,
    get_session_earnings,
    get_today_earnings_summary,
    get_user,
    start_session as db_start_session,
)

# Product selected in PickerScene, to be added to cart in ScanScene
selected_product: Product | None = None

# Currently logged-in cashier (Kassiererin)
current_user: User | None = None

# Current session tracking
session_id: int | None = None
session_start: datetime | None = None

# Time bonus tracking
_last_time_bonus_count: int = 0


def set_selected_product(product: Product | None) -> None:
    """Set the product selected from picker."""
    global selected_product
    selected_product = product


def get_and_clear_selected_product() -> Product | None:
    """Get and clear the selected product (one-time read)."""
    global selected_product
    product = selected_product
    selected_product = None
    return product


# --- User State ---


def set_current_user(user: User | None) -> None:
    """Set the currently logged-in user (cashier)."""
    global current_user
    current_user = user


def get_current_user() -> User | None:
    """Get the currently logged-in user."""
    return current_user


def refresh_current_user() -> User | None:
    """Refresh user from DB (to get updated balance)."""
    global current_user
    if current_user:
        current_user = get_user(current_user.card_id)
    return current_user


def logout() -> None:
    """Log out the current user and end session."""
    global current_user, session_id, session_start, _last_time_bonus_count
    if session_id:
        db_end_session(session_id)
    current_user = None
    session_id = None
    session_start = None
    _last_time_bonus_count = 0


# --- Session Tracking ---


def start_session(user: User) -> int:
    """Start a new work session for user, return session ID."""
    global current_user, session_id, session_start, _last_time_bonus_count
    current_user = user
    session_id = db_start_session(user.card_id)
    session_start = datetime.now()
    _last_time_bonus_count = 0
    return session_id


def get_session_id() -> int | None:
    """Get current session ID."""
    return session_id


def get_session_start() -> datetime | None:
    """Get session start time."""
    return session_start


def add_earning(source: str, amount: int, description: str | None = None) -> None:
    """Add an earning to current session and update user balance.

    Args:
        source: 'math', 'cashier', or 'time'
        amount: Taler earned
        description: Optional description (e.g., "3 Aufgaben gelöst")
    """
    global current_user
    if not session_id or not current_user:
        return

    db_add_earning(session_id, current_user.card_id, source, amount, description)
    # Refresh user to get updated balance
    refresh_current_user()


def get_current_session_earnings() -> list[Earning]:
    """Get all earnings from current session."""
    if not session_id:
        return []
    return get_session_earnings(session_id)


def get_today_summary() -> dict[str, int]:
    """Get today's earnings summary for current user.

    Returns dict like: {'math': 10, 'cashier': 2, 'time': 1}
    """
    if not current_user:
        return {}
    return get_today_earnings_summary(current_user.card_id)


# --- Global Time Bonus ---

# Import here to avoid circular dependency at module level
from src.constants import EARNING_TIME_SECONDS  # noqa: E402


def check_time_bonus() -> int | None:
    """Check if time bonus is due. Call this in every Scene.update().

    Returns:
        Amount of Taler earned if bonus was awarded, None otherwise.
    """
    global _last_time_bonus_count

    if not session_id or not session_start:
        return None

    elapsed = (datetime.now() - session_start).total_seconds()
    current_bonus_count = int(elapsed // EARNING_TIME_SECONDS)

    if current_bonus_count > _last_time_bonus_count:
        _last_time_bonus_count = current_bonus_count
        minutes = EARNING_TIME_SECONDS // 60
        add_earning("time", 1, f"{minutes} Min Anwesenheit")
        return 1

    return None
