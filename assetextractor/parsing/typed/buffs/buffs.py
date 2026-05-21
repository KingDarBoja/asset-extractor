from __future__ import annotations

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.typed.common.upgrades import (
    AssetWithBuildingUpgrade,
    AssetWithFactoryUpgrade,
    AssetWithResidenceUpgrade,
)


class BuildingBuff(
    AssetWithBuildingUpgrade, AssetWithResidenceUpgrade, AssetWithFactoryUpgrade, template_names="BuildingBuff"
):
    """Specialized Asset for 'BuildingBuff'."""

    pass


class MetaBuff(Asset, template_names="MetaBuff"):
    """Specialized Asset for 'MetaBuff'."""

    pass


class TroopBuff(Asset, template_names="TroopBuff"):
    """Specialized Asset for 'TroopBuff'."""

    pass


class WarehouseBuff(Asset, template_names="WarehouseBuff"):
    """Specialized Asset for 'WarehouseBuff'."""

    pass


class DefenseBuildingBuff(Asset, template_names="DefenseBuildingBuff"):
    """Specialized Asset for 'DefenseBuildingBuff'."""

    pass
