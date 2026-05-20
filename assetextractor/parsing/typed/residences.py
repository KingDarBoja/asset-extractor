from __future__ import annotations

from assetextractor.parsing.typed.common.building import AssetWithBuilding
from assetextractor.parsing.typed.common.cost import AssetWithCosts


class ResidenceBuilding(AssetWithCosts, AssetWithBuilding, template_names="ResidenceBuilding"):
    """Specialized Asset for 'ResidenceBuilding' with pre-computed data."""

    pass
