"""Typed catalog transfer models and the small HTTP sync client."""

from dataclasses import asdict
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from src.utils.database import Product, ProductBarcodeAlias

SYNC_PATH = "/api/catalog/sync"
SYNC_TIMEOUT_SECONDS = 15.0
ASSET_KEY_PATTERN = r"^[a-z0-9_]+$"


class CatalogProduct(BaseModel):
    """Serializable product fields shared by local inventory and the Pi."""

    barcode: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120, pattern=ASSET_KEY_PATTERN)
    name_de: str = Field(min_length=1, max_length=120)
    price: float = Field(ge=0)
    category: str = Field(min_length=1, max_length=120)
    image_path: str | None = Field(
        default=None,
        max_length=120,
        pattern=ASSET_KEY_PATTERN,
    )
    has_barcode: bool = True
    active: bool = True

    @classmethod
    def from_database(cls, product: Product) -> "CatalogProduct":
        """Create a transfer model from a database product."""
        return cls(**asdict(product))

    def to_database(self) -> Product:
        """Create a database product from validated transfer fields."""
        return Product(**self.model_dump())


class CatalogAlias(BaseModel):
    """Serializable packaging barcode alias."""

    alias_barcode: str = Field(min_length=1, max_length=128)
    product_barcode: str = Field(min_length=1, max_length=64)

    @classmethod
    def from_database(cls, alias: ProductBarcodeAlias) -> "CatalogAlias":
        """Create a transfer model from a database alias."""
        return cls(**asdict(alias))

    def to_database(self) -> ProductBarcodeAlias:
        """Create a database alias from validated transfer fields."""
        return ProductBarcodeAlias(**self.model_dump())


class CatalogPayload(BaseModel):
    """A complete or selected product catalog transfer."""

    products: list[CatalogProduct]
    aliases: list[CatalogAlias]


class CatalogSyncResult(BaseModel):
    """Result returned after an atomic catalog import."""

    product_count: int = Field(ge=0)
    alias_count: int = Field(ge=0)


class InventorySyncRequest(BaseModel):
    """Local request selecting products to send to one remote Kasse."""

    destination_url: str = Field(min_length=1, max_length=500)
    pin: str = Field(min_length=1, max_length=128)
    product_barcodes: list[str] = Field(min_length=1)


class CatalogSyncClientError(RuntimeError):
    """A safe, user-facing remote catalog sync error."""


def send_catalog(
    destination_url: str,
    pin: str,
    catalog: CatalogPayload,
) -> CatalogSyncResult:
    """Send selected catalog records with a transient PIN using stdlib HTTP."""
    endpoint = _sync_endpoint(destination_url)
    request = Request(
        endpoint,
        data=catalog.model_dump_json().encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Admin-PIN": pin,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=SYNC_TIMEOUT_SECONDS) as response:  # noqa: S310
            response_body = response.read()
    except HTTPError as error:
        raise CatalogSyncClientError(
            f"Die Kasse hat die Synchronisation abgelehnt ({error.code})."
        ) from error
    except (URLError, TimeoutError) as error:
        raise CatalogSyncClientError("Die Kasse ist nicht erreichbar.") from error

    try:
        return CatalogSyncResult.model_validate_json(response_body)
    except ValueError as error:
        raise CatalogSyncClientError(
            "Die Kasse hat eine ungültige Antwort gesendet."
        ) from error


def _sync_endpoint(destination_url: str) -> str:
    parsed = urlsplit(destination_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CatalogSyncClientError("Bitte eine vollständige http(s)-Adresse angeben.")
    return urlunsplit((parsed.scheme, parsed.netloc, SYNC_PATH, "", ""))
