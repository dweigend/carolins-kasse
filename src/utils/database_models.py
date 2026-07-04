"""Database row models and checkout result types."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self


@dataclass
class Product:
    """A product in the shop."""

    barcode: str
    name: str
    name_de: str
    price: float
    category: str
    image_path: str | None = None
    has_barcode: bool = True
    active: bool = True

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Product from database row."""
        return cls(
            barcode=row[0],
            name=row[1],
            name_de=row[2],
            price=row[3],
            category=row[4],
            image_path=row[5],
            has_barcode=bool(row[6]),
            active=bool(row[7]),
        )


@dataclass
class User:
    """A user/customer."""

    card_id: str
    name: str
    balance: float = 10.0
    color: str | None = None
    difficulty: int = 1
    is_admin: bool = False
    active: bool = True

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create User from database row."""
        return cls(
            card_id=row[0],
            name=row[1],
            balance=row[2],
            color=row[3],
            difficulty=row[4],
            is_admin=bool(row[5]),
            active=bool(row[6]),
        )


@dataclass
class Recipe:
    """A recipe card."""

    barcode: str
    name: str
    image_path: str | None = None
    active: bool = True

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Recipe from database row."""
        return cls(
            barcode=row[0],
            name=row[1],
            image_path=row[2],
            active=bool(row[3]),
        )


@dataclass
class RecipeIngredient:
    """An ingredient in a recipe."""

    recipe_barcode: str
    product_barcode: str
    quantity: int = 1


@dataclass
class Session:
    """A work session (login to logout)."""

    id: int
    user_card_id: str
    started_at: datetime
    ended_at: datetime | None = None

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Session from database row."""
        return cls(
            id=row[0],
            user_card_id=row[1],
            started_at=datetime.fromisoformat(row[2]),
            ended_at=datetime.fromisoformat(row[3]) if row[3] else None,
        )


@dataclass
class Earning:
    """An earning entry from an activity."""

    id: int
    session_id: int
    user_card_id: str
    source: str  # 'math', 'cashier', 'time'
    amount: int
    description: str | None
    earned_at: datetime

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Earning from database row."""
        return cls(
            id=row[0],
            session_id=row[1],
            user_card_id=row[2],
            source=row[3],
            amount=row[4],
            description=row[5],
            earned_at=datetime.fromisoformat(row[6]),
        )


@dataclass
class Transaction:
    """A purchase transaction."""

    id: int
    user_card_id: str
    total: int
    items_json: str
    timestamp: datetime

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Transaction from database row."""
        return cls(
            id=row[0],
            user_card_id=row[1],
            total=row[2],
            items_json=row[3],
            timestamp=datetime.fromisoformat(row[4]),
        )


@dataclass
class BalanceAdjustment:
    """A manual admin balance change."""

    id: int
    user_card_id: str
    user_name: str
    old_balance: float
    new_balance: float
    delta: float
    note: str | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create BalanceAdjustment from database row."""
        return cls(
            id=row[0],
            user_card_id=row[1],
            user_name=row[2],
            old_balance=row[3],
            new_balance=row[4],
            delta=row[5],
            note=row[6],
            created_at=datetime.fromisoformat(row[7]),
        )


PRODUCT_COLUMNS = (
    "barcode, name, name_de, price, category, image_path, has_barcode, active"
)
USER_COLUMNS = "card_id, name, balance, color, difficulty, is_admin, active"
RECIPE_COLUMNS = "barcode, name, image_path, active"


class CheckoutError(RuntimeError):
    """Base error for checkout failures that should not write partial data."""


class CheckoutUserNotFoundError(CheckoutError):
    """Raised when checkout is attempted for an unknown or inactive user."""


class InsufficientFundsError(CheckoutError):
    """Raised when the customer balance is lower than the checkout total."""

    def __init__(self, *, available: float, required: int) -> None:
        super().__init__(
            f"Insufficient balance: available {available}, required {required}"
        )
        self.available = available
        self.required = required


@dataclass(frozen=True)
class CheckoutResult:
    """Result of a successful checkout transaction."""

    transaction_id: int
    user: User
