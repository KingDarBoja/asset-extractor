from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, List, Union  # Postpones evaluation of annotations

from assetextractor.parsing.core.asset_factories.production_field import ProductionField
from assetextractor.parsing.core.asset_factories.residence_building import ResidenceBuilding
from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.core.attributes import ListAttribute, ReferenceAttribute

# Import AssetCache ONLY for type checking
if TYPE_CHECKING:
    import lxml.etree as et

    from assetextractor.parsing.core.assets import AssetCache
    from assetextractor.parsing.core.common import NamedElement
    from assetextractor.parsing.core.texts import Text


class AssetPoolNamed(Asset):
    """Specialized Asset for Patron (Deities) with pre-computed data."""

    def __init__(self, node: et._Element, cache: AssetCache):
        super().__init__(node, cache)

    def _get_text_from_node(self, elm: NamedElement[Any], path: str, fallback: str) -> str:
        """Helper to resolve a Text node path into a localized string."""
        node = elm.find(path)

        if node is not None:
            lang = self.cache.texts.converter.language
            text_attr: Text | None = node()
            if text_attr is not None:
                # Return the localized string, fallback to English, then to the provided default
                return text_attr.get(lang) or text_attr.get("english") or fallback  # type: ignore

        return fallback

    @cached_property
    def asset_pool_list(self) -> List[Union[Asset, AssetPoolNamed, ResidenceBuilding, ProductionField]]:
        """
        Return a list of Assets that can be either 'Production', 'LandUnit',
        other 'AssetPoolNamed' (subgroups) and so on.
        """
        raw_asset_list = self.find("AssetPool.AssetList")
        out_asset_list: List[Union[Asset, ResidenceBuilding, ProductionField]] = []

        # print(f"|- Processing Asset Pool: {self.name} (GUID: {self.guid})...")

        if isinstance(raw_asset_list, ListAttribute):
            # print(f"|- Asset Pool has {len(raw_asset_list)} assets.")
            for asset_entry in raw_asset_list:
                # Get the referenced asset
                linked_asset_ref = asset_entry.find("Asset")

                if linked_asset_ref is not None and isinstance(linked_asset_ref, ReferenceAttribute):
                    linked_asset = self.cache.get(linked_asset_ref.guid)
                    if isinstance(linked_asset, Asset):
                        tpl_name = linked_asset.template.name
                        # print(f"|-- Asset {tpl_name} (GUID: {linked_asset.guid})")

                        # TODO: Add all the Asset sub-classes per template name to
                        # have specialized instantiation of linked assets.
                        match tpl_name:
                            case "Production Field":
                                out_asset_list.append(ProductionField(linked_asset.node, self.cache))
                            case "ResidenceBuilding":
                                out_asset_list.append(ResidenceBuilding(linked_asset.node, self.cache))
                            case "AssetPoolNamed":
                                # Dynamically use self.__class__ to avoid circular imports at runtime
                                pool_class = self.__class__
                                out_asset_list.append(pool_class(linked_asset.node, self.cache))
                            case _:
                                # Default generic asset.
                                out_asset_list.append(linked_asset)

        return out_asset_list
