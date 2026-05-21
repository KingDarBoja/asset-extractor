from assetextractor.parsing.typed.common.upgrades import (
    AssetWithHealthUpgrade,
    AssetWithMaintenanceUpgrade,
    AssetWithUnitUpgrade,
)


class DefenseBuildingBuff(
    AssetWithUnitUpgrade, AssetWithMaintenanceUpgrade, AssetWithHealthUpgrade, template_names="DefenseBuildingBuff"
):
    """Specialized Asset for 'DefenseBuildingBuff'."""

    pass
