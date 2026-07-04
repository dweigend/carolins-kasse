"""Smoke tests for central barcode rules."""

import unittest

from src.utils.barcodes import (
    PRODUCT_PREFIX,
    USER_PREFIX,
    calculate_ean13_check_digit,
    generate_product_barcode,
    generate_user_barcode,
)


class BarcodeSmokeTests(unittest.TestCase):
    def test_ean13_check_digit_uses_standard_weights(self) -> None:
        self.assertEqual(calculate_ean13_check_digit("400638133393"), "4006381333931")

    def test_internal_user_barcode_matches_admin_card(self) -> None:
        self.assertEqual(generate_user_barcode(4), "2000000000046")

    def test_internal_product_barcode_keeps_prefix_and_length(self) -> None:
        barcode = generate_product_barcode(1)

        self.assertTrue(barcode.startswith(PRODUCT_PREFIX))
        self.assertEqual(len(barcode), 13)
        self.assertTrue(barcode.isdigit())

    def test_invalid_bodies_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_ean13_check_digit("123")

        with self.assertRaises(ValueError):
            calculate_ean13_check_digit(f"{USER_PREFIX}abcdefghi")


if __name__ == "__main__":
    unittest.main()
