"""Haversine distance calculation utility."""
from __future__ import annotations

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance (in km) between two points
    on earth using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (in decimal degrees).
        lat2, lon2: Latitude and longitude of point 2 (in decimal degrees).

    Returns:
        Distance in kilometres.
    """
    R = 6371.0  # Earth radius in km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
