"""
Grouped Asset sub-classes by their parent categories.

These comes from 'Objects' -> 'Buildings'.
"""

from __future__ import annotations

from assetextractor.parsing.typed.common.building import AssetWithBuilding
from assetextractor.parsing.typed.common.cost import AssetWithCosts
from assetextractor.parsing.typed.common.maintenance import AssetWithMaintenance


class AssetBuildingBase(AssetWithCosts, AssetWithMaintenance, AssetWithBuilding):
    """
    Base group for assets categorized under 'Objects' -> 'Buildings'.

    This class consolidates the core characteristics shared by all factory-type
    buildings, combining cost tracking, maintenance overhead, and fundamental
    building properties. It serves as the primary base class for specialized
    factory asset implementations.
    """

    pass
