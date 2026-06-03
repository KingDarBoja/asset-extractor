from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, cast

from assetextractor.parsing.typed.common.building import AssetWithBuilding
from assetextractor.parsing.typed.common.cost import AssetWithCosts

if TYPE_CHECKING:
    from assetextractor.parsing.core.texts import Text


class OrnamentalBuilding(
    AssetWithCosts, AssetWithBuilding, template_names=["OrnamentalBuilding", "PolygonObject", "Hedge"]
):
    """
    Specialized Asset for 'OrnamentalBuilding', 'PolygonObject' and 'Hedge' with
    pre-computed data.

    Both 'PolygonObject' and 'Hedge' do not have an 'Ornament' object so handle
    these scenarios with the proper defaults.
    """

    @cached_property
    def prestige(self) -> int:
        return int(cast("int", self.find_value("Ornament.OrnamentUnit") or 0))

    @cached_property
    def localized_title(self) -> str:
        return self.text() if self.text else "No Title"

    @cached_property
    def localized_description(self) -> str:
        info_desc = cast("Text | None", self.find_value("Standard.InfoDescription"))
        std_desc = info_desc() if info_desc else "No Description"
        if self.template.name in {"PolygonObject", "Hedge"}:
            return std_desc
        else:
            orn_desc = cast("Text | None", self.find_value("Ornament.OrnamentDescription"))
            return orn_desc() if orn_desc else std_desc
