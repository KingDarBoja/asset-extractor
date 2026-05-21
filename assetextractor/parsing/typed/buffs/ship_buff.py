from assetextractor.parsing.typed.common.upgrades import (
    AssetWithHealthUpgrade,
    AssetWithMaintenanceUpgrade,
    AssetWithMovementUpgrade,
    AssetWithTradeShipUpgrade,
    AssetWithUnitUpgrade,
    AssetWithVehicleUpgrade,
)


class ShipBuff(
    AssetWithHealthUpgrade,
    AssetWithVehicleUpgrade,
    AssetWithTradeShipUpgrade,
    AssetWithMovementUpgrade,
    AssetWithMaintenanceUpgrade,
    AssetWithUnitUpgrade,
    template_names="ShipBuff",
):
    """Specialized Asset for 'ShipBuff'."""

    pass
