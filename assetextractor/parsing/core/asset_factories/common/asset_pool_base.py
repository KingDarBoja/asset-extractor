from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, List, Union

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.core.attributes import ListAttribute, ReferenceAttribute

if TYPE_CHECKING:
    # import lxml.etree as et

    from assetextractor.parsing.core.asset_factories.production_field import ProductionField
    from assetextractor.parsing.core.asset_factories.residence_building import ResidenceBuilding


class AssetPoolBase(Asset):
    """Common logic for all AssetPool types."""

    @property
    def asset_list_path(self) -> str:
        """Subclasses must override this with their specific XML path."""
        raise NotImplementedError

    @cached_property
    def asset_pool_list(self) -> List[Union[Asset, "AssetPoolBase", "ProductionField", "ResidenceBuilding"]]:
        from assetextractor.parsing.core.asset_factories.asset_pool import AssetPool
        from assetextractor.parsing.core.asset_factories.asset_pool_named import AssetPoolNamed
        from assetextractor.parsing.core.asset_factories.production_field import ProductionField
        from assetextractor.parsing.core.asset_factories.residence_building import ResidenceBuilding

        raw_asset_list = self.find(self.asset_list_path)
        out_asset_list: List[Union[Asset, "AssetPoolBase", "ProductionField", "ResidenceBuilding"]] = []

        if isinstance(raw_asset_list, ListAttribute):
            for asset_entry in raw_asset_list:
                linked_asset_ref = asset_entry.find("Asset")

                if isinstance(linked_asset_ref, ReferenceAttribute):
                    linked_asset = self.cache.get(linked_asset_ref.guid)
                    if isinstance(linked_asset, Asset):
                        tpl_name = linked_asset.template.name

                        match tpl_name:
                            case "Production Field":
                                out_asset_list.append(ProductionField(linked_asset.node, self.cache))
                            case "ResidenceBuilding":
                                out_asset_list.append(ResidenceBuilding(linked_asset.node, self.cache))
                            case "AssetPool":
                                out_asset_list.append(AssetPool(linked_asset.node, self.cache))
                            case "AssetPoolNamed":
                                out_asset_list.append(AssetPoolNamed(linked_asset.node, self.cache))
                            case _:
                                out_asset_list.append(linked_asset)
        return out_asset_list
