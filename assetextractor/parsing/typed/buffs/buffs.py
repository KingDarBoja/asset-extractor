from __future__ import annotations

from assetextractor.parsing.core.assets import Asset


class MetaBuff(Asset, template_names="MetaBuff"):
    """Specialized Asset for 'MetaBuff'."""

    pass


class TroopBuff(Asset, template_names="TroopBuff"):
    """Specialized Asset for 'TroopBuff'."""

    pass


class WarehouseBuff(Asset, template_names="WarehouseBuff"):
    """Specialized Asset for 'WarehouseBuff'."""

    pass
