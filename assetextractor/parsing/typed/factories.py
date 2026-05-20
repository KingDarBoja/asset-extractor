"""
Grouped Asset sub-classes by their parent categories.

These comes from 'Objects' -> 'Buildings' -> 'Factories'
"""

from __future__ import annotations

from assetextractor.parsing.typed.common.building import AssetWithBuilding
from assetextractor.parsing.typed.common.cost import AssetWithCosts
from assetextractor.parsing.typed.common.factory_base import AssetWithFactoryBase
from assetextractor.parsing.typed.common.maintenance import AssetWithMaintenance


class AssetFactoryBase(AssetWithCosts, AssetWithMaintenance, AssetWithBuilding, AssetWithFactoryBase):
    """
    Base group for assets categorized under 'Objects' -> 'Buildings' -> 'Factories'.

    This class consolidates the core characteristics shared by all factory-type
    buildings, combining cost tracking, maintenance overhead, and fundamental
    building properties. It serves as the primary base class for specialized
    factory asset implementations.
    """

    pass


class Monument(AssetFactoryBase, template_names="Monument"):
    """
    Specialized Asset for 'Monument' with pre-computed data.

    Examples:
        - GUID: 36912 -> Monument Colosseum Phase 2.
    """

    pass


class Production(AssetFactoryBase, template_names="Production"):
    """
    Specialized Asset for 'Production' with pre-computed data.

    Examples:
        - GUID: 3174 -> Production Food Roman Bread.
    """

    pass


class ProductionArea(AssetFactoryBase, template_names="Production Area"):
    """
    Specialized Asset for 'Production Area' with pre-computed data.

    Examples:
        - GUID: 5975 -> Production Meadow Celtic Dartmoor Ponies.
        - GUID: 31752 -> Production Forest Roman Resin.
    """

    pass


class ProductionField(AssetFactoryBase, template_names="Production Field"):
    """
    Specialized Asset for 'Production Field' with pre-computed data.

    Examples:
        - GUID: 2693 -> Production Field Roman Wheat.
    """

    pass


class ProductionMarsh(AssetFactoryBase, template_names="Production Marsh"):
    """
    Specialized Asset for 'Production Marsh' with pre-computed data.

    Examples:
        - GUID: 5477 -> Production Ingredient Roman Celtic Bird Tongues.
    """

    pass


class ProductionMarshArea(AssetFactoryBase, template_names="Production Marsh Area"):
    """
    Specialized Asset for 'Production Marsh Area' with pre-computed data.

    Examples:
        - GUID: 5299 -> Production Marsh Roman Celtic Eels.
    """

    pass


class ProductionMarshPasture(AssetFactoryBase, template_names="Production Marsh Pasture"):
    """
    Specialized Asset for 'Production Marsh Pasture' with pre-computed data.

    Examples:
        - GUID: 5849 -> Production Marsh Celtic Reed.
    """

    pass


class SlotFactoryBuilding7(AssetFactoryBase, template_names="SlotFactoryBuilding7"):
    """
    Specialized Asset for 'SlotFactoryBuilding7' with pre-computed data.

    Examples:
        - GUID: 3075 -> Production Ingredient Roman Flour.
    """

    pass


class ProductionModuleSilo(AssetFactoryBase, template_names="ProductionModuleSilo"):
    """
    Specialized Asset for 'ProductionModuleSilo' with pre-computed data.

    Examples:
        - GUID: 77954 -> Module Silo Roman.
    """

    pass
