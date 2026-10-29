import unittest
from catalog import Catalog


class CatalogContractTests(unittest.TestCase):
    def test_offline_keeps_previous_catalog(self):
        catalog = Catalog()
        catalog.refresh(["cedar", "bay"])
        result = catalog.refresh(offline=True)
        self.assertEqual(("cedar", "bay"), result.items)
        self.assertTrue(result.stale)

    def test_offline_without_cache_is_an_explicit_error(self):
        with self.assertRaises(ConnectionError):
            Catalog().refresh(offline=True)

    def test_recovery_replaces_stale_data(self):
        catalog = Catalog()
        catalog.refresh(["cedar"])
        catalog.refresh(offline=True)
        result = catalog.refresh(["bay"])
        self.assertEqual(("bay",), result.items)
        self.assertFalse(result.stale)

    def test_repeated_reservation_has_one_reference(self):
        catalog = Catalog()
        catalog.refresh(["cedar"])
        first = catalog.reserve("cedar")
        self.assertEqual(first, catalog.reserve("cedar"))
        self.assertEqual(1, len(catalog.bookings))

    def test_unknown_item_cannot_be_reserved(self):
        catalog = Catalog()
        with self.assertRaises(ValueError):
            catalog.reserve("unknown")
        self.assertEqual({}, catalog.bookings)
