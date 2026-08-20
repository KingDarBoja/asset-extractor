from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, List, cast

from assetextractor.parsing.core.assets import Asset

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import ListAttribute


class ConstructionCategory(Asset, template_names="ConstructionCategory"):
    """Specialized Asset for 'ConstructionCategory' with pre-computed data."""

    @cached_property
    def building_assets(self) -> List[Asset]:
        out: List[Asset] = []
        for item in cast("ListAttribute", self.find("ConstructionCategory.BuildingList")):
            asset = item.find_ref("Building")
            if asset is not None:
                out.append(asset)
        return out

    @cached_property
    def localized_title(self) -> str:
        return self.text() if self.text else "No Title"
