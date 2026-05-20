from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, cast

from assetextractor.parsing.typed.common.cost import AssetWithCosts
from assetextractor.parsing.typed.common.maintenance import AssetWithMaintenance

if TYPE_CHECKING:
    from assetextractor.parsing.core.texts import Text


class OrnamentalBuilding(AssetWithCosts, AssetWithMaintenance, template_names=["OrnamentalBuilding", "PolygonObject"]):
    """Specialized Asset for Ornamental Buildings with pre-computed data."""

    @cached_property
    def prestige(self) -> int:
        return int(cast("int", self.find_value("Ornament.OrnamentUnit") or 0))

    @cached_property
    def localized_title(self) -> str:
        text = cast("Text | None", self.find_value("Text.OasisId"))
        return text() if text else "No Title"

    @cached_property
    def localized_description(self) -> str:
        text = cast("Text | None", self.find_value("Ornament.OrnamentDescription"))
        return text() if text else "No Description"
