from assetextractor.parsing.typed.common.upgrades import (
    AssetWithBuildingUpgrade,
    AssetWithFactoryUpgrade,
    AssetWithHealthUpgrade,
    AssetWithMaintenanceUpgrade,
    AssetWithResidenceUpgrade,
)


class BuildingBuff(
    AssetWithBuildingUpgrade,
    AssetWithResidenceUpgrade,
    AssetWithFactoryUpgrade,
    AssetWithHealthUpgrade,
    AssetWithMaintenanceUpgrade,
    template_names="BuildingBuff",
):
    """Specialized Asset for 'BuildingBuff'."""

    pass
