"""A small original behavioral example, independent of Android or client systems."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Snapshot:
    items: tuple[str, ...]
    stale: bool


class Catalog:
    def __init__(self):
        self.items = ()
        self.bookings = {}

    def refresh(self, items=None, offline=False):
        if offline:
            if not self.items:
                raise ConnectionError("No saved catalog")
            return Snapshot(self.items, stale=True)
        if items is None:
            raise ValueError("A successful source must provide a catalog")
        self.items = tuple(items)
        return Snapshot(self.items, stale=False)

    def reserve(self, identifier):
        if identifier not in self.items:
            raise ValueError("Unknown demo item")
        return self.bookings.setdefault(identifier, f"DEMO-{identifier.upper()}")
