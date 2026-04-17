"""Earnings utility functions.

Centralized salary/bonus logic for the economy system.
"""

from src.constants import EARNING_CASHIER, EARNING_RECIPE
from src.utils import state


def award_cashier_salary(customer_name: str) -> tuple[int, str | None]:
    """Award salary to logged-in cashier for checkout.

    Args:
        customer_name: Name of the customer who was checked out

    Returns:
        (amount, cashier_name) - Amount earned and cashier name, or (0, None)
    """
    cashier = state.get_current_user()
    if not cashier:
        return 0, None

    state.add_earning("cashier", EARNING_CASHIER, f"Kassiert für {customer_name}")
    return EARNING_CASHIER, cashier.name


def award_recipe_bonus(recipe_name: str) -> tuple[int, str | None]:
    """Award bonus to logged-in user for completing recipe.

    Args:
        recipe_name: Name of the completed recipe

    Returns:
        (amount, user_name) - Amount earned and user name, or (0, None)
    """
    user = state.get_current_user()
    if not user:
        return 0, None

    state.add_earning("recipe", EARNING_RECIPE, f"Rezept: {recipe_name}")
    return EARNING_RECIPE, user.name
