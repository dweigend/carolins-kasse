"""Shopping cart for the scan scene."""

from dataclasses import dataclass

from src.utils.database import Product


@dataclass
class CartItem:
    """A product in the shopping cart with quantity."""

    product: Product
    quantity: int = 1

    @property
    def subtotal(self) -> float:
        """Calculate subtotal for this item."""
        return self.product.price * self.quantity


class Cart:
    """Shopping cart that holds products.

    Products are keyed by barcode. Adding the same product
    increases quantity instead of creating duplicates.
    """

    def __init__(self) -> None:
        """Initialize empty cart."""
        self._items: dict[str, CartItem] = {}

    def add(self, product: Product, quantity: int = 1) -> None:
        """Add a product to the cart.

        If product already exists, increases quantity.

        Args:
            product: Product to add
            quantity: Amount to add (default 1)
        """
        if product.barcode in self._items:
            self._items[product.barcode].quantity += quantity
        else:
            self._items[product.barcode] = CartItem(product, quantity)

    def remove(self, barcode: str) -> None:
        """Remove a product from the cart entirely.

        Args:
            barcode: Barcode of product to remove
        """
        self._items.pop(barcode, None)

    def update_quantity(self, barcode: str, delta: int) -> None:
        """Change quantity of a product.

        If quantity becomes 0 or less, removes the item.

        Args:
            barcode: Product barcode
            delta: Amount to add (can be negative)
        """
        if barcode not in self._items:
            return

        item = self._items[barcode]
        item.quantity += delta

        if item.quantity <= 0:
            del self._items[barcode]

    def set_quantity(self, barcode: str, quantity: int) -> None:
        """Set exact quantity of a product.

        Args:
            barcode: Product barcode
            quantity: New quantity (removes if <= 0)
        """
        if barcode not in self._items:
            return

        if quantity <= 0:
            del self._items[barcode]
        else:
            self._items[barcode].quantity = quantity

    def clear(self) -> None:
        """Remove all items from cart."""
        self._items.clear()

    @property
    def items(self) -> list[CartItem]:
        """Get all items in the cart.

        Returns:
            List of CartItems, ordered by when they were added
        """
        return list(self._items.values())

    @property
    def total(self) -> float:
        """Calculate total price of all items.

        Returns:
            Sum of all item subtotals
        """
        return sum(item.subtotal for item in self._items.values())

    @property
    def item_count(self) -> int:
        """Get total number of items (counting quantities).

        Returns:
            Sum of all quantities
        """
        return sum(item.quantity for item in self._items.values())

    @property
    def is_empty(self) -> bool:
        """Check if cart has no items."""
        return len(self._items) == 0

    def __len__(self) -> int:
        """Get number of unique products in cart."""
        return len(self._items)
