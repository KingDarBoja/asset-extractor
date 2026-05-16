"""
Grouped Asset sub-classes by their parent categories.

These comes from 'Objects' -> 'Buildings' -> 'Harbour'
"""

from __future__ import annotations

from assetextractor.parsing.typed.cost import AssetWithCosts
from assetextractor.parsing.typed.maintenance import AssetWithMaintenance


class BuildingHarborGroup(AssetWithCosts, AssetWithMaintenance):
    """Base group for assets categorized under 'Objects' -> 'Buildings' -> 'Harbour'."""

    pass


class RecruitmentBuilding(BuildingHarborGroup, template_names="RecruitmentBuilding"):
    """
    Specialized Asset for 'RecruitmentBuilding' with pre-computed data.

    Examples:
        - GUID: 6054 -> Harbor Shipyard Roman.
    """

    pass


class HarborWarehouse(BuildingHarborGroup, template_names="HarborWarehouse"):
    """
    Specialized Asset for 'HarborWarehouse' with pre-computed data.

    Examples:
        - GUID: 3402 -> Harbor Warehouse Roman 01.
    """

    pass
