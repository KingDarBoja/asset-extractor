from __future__ import annotations

from assetextractor.parsing.typed.common.cost import AssetWithCosts
from assetextractor.parsing.typed.common.maintenance import AssetWithMaintenance


class LandUnit(AssetWithCosts, AssetWithMaintenance, template_names="LandUnit"):
    """
    Specialized Asset for 'LandUnit' with pre-computed data.

    Examples:
        - GUID: 37475 -> Troop Roman Auxilia.
    """

    pass
