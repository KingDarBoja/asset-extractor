from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, cast

from assetextractor.parsing.typed.common.building import AssetWithBuilding
from assetextractor.parsing.typed.common.cost import AssetWithCosts

if TYPE_CHECKING:
    from assetextractor.parsing.core.texts import Text


class OrnamentalBuilding(AssetWithCosts, AssetWithBuilding, template_names=["OrnamentalBuilding", "PolygonObject"]):
    """Specialized Asset for 'OrnamentalBuilding' and 'PolygonObject' with pre-computed data."""

    @cached_property
    def prestige(self) -> int:
        return int(cast("int", self.find_value("Ornament.OrnamentUnit") or 0))

    @cached_property
    def localized_title(self) -> str:
        return self.text() if self.text else "No Title"

    @cached_property
    def localized_description(self) -> str:
        text = cast("Text | None", self.find_value("Ornament.OrnamentDescription"))
        return text() if text else "No Description"
