from assetextractor.parsing.typed.common.upgrades import (
    AssetWithHealthUpgrade,
    AssetWithTradeShipUpgrade,
    AssetWithVehicleUpgrade,
)


class ShipBuff(AssetWithHealthUpgrade, AssetWithVehicleUpgrade, AssetWithTradeShipUpgrade, template_names="ShipBuff"):
    """Specialized Asset for 'ShipBuff'."""

    pass
