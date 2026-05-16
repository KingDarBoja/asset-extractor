from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, List, cast

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.typed.enums import BuildingType, Region

if TYPE_CHECKING:
    from assetextractor.parsing.core.texts import Text


@dataclass(frozen=True)
class Building:
    type: BuildingType
    """Specificy building type from dataset 'BuildingType'. Comes from 'Building.BuildingType'."""
    category_name: str
    """Localized category name. Comes from 'Building.BuildingCategoryName'."""
    associated_regions: List[Region]


class AssetWithBuilding(Asset):
    """Base class for assets that contain a 'Building' object."""

    @cached_property
    def building_info(self) -> Building:
        raw_building_type = self.find_value("Building.BuildingType")
        building_type = cast("BuildingType", raw_building_type) if raw_building_type else BuildingType.OTHER

        raw_cat_name = cast("Text | None", self.find_value("Building.BuildingCategoryName"))
        cat_name = raw_cat_name() if raw_cat_name else "N/A"

        raw_regions = cast("List[Region] | None", self.find_value("Building.AssociatedRegions"))
        regions = raw_regions if raw_regions else []

        return Building(type=building_type, category_name=cat_name, associated_regions=regions)

        # if self.assets.properties.ui_text_cache and isinstance(source_cat_attr, Attribute):
        #     source_cat_literal = source_cat_attr()
        #     if not isinstance(source_cat_literal, str):
        #         pass

        #     ui_cache = self.assets.properties.ui_text_cache
        #     source_cat_mapping = ui_cache.get_ui_text("BuffCategoryType", source_cat_literal)
        #     if source_cat_mapping is not None and source_cat_mapping.text is not None:
        #         source_cat_localized = source_cat_mapping.text()
        #     else:
        #         source_cat_localized = source_cat_literal

        #     print(f"Source Category: {source_cat_localized}")
