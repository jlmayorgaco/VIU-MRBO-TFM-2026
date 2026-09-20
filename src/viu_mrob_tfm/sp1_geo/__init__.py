"""Geometry-aware SP1 coalition benchmark.

The package separates the decision signal, allocation engine, and atomic
closure while evaluating every method with the same physical certifier.
"""

from .models import (
    ActionCatalog,
    AllocationResult,
    Assignment,
    ContactSlot,
    GeoLoad,
    GeoRobot,
    GeoWorld,
)

__all__ = [
    "ActionCatalog",
    "AllocationResult",
    "Assignment",
    "ContactSlot",
    "GeoLoad",
    "GeoRobot",
    "GeoWorld",
]
