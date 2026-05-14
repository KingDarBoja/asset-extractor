from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, List  # Postpones evaluation of annotations

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.core.attributes import ListAttribute, ReferenceAttribute

# Import AssetCache ONLY for type checking
if TYPE_CHECKING:
    import lxml.etree as et

    from assetextractor.parsing.core.assets import AssetCache
    from assetextractor.parsing.core.texts import Text


class Effect(Asset):
    """Specialized Asset for Patron (Deities) with pre-computed data."""

    def __init__(self, node: et._Element, cache: AssetCache):
        super().__init__(node, cache)

    def _get_text_from_node(self, path: str, fallback: str) -> str:
        """Helper to resolve a Text node path into a localized string."""
        node = self.find(path)

        if node is not None:
            lang = self.cache.texts.converter.language
            text_attr: Text | None = node()
            if text_attr is not None:
                # Return the localized string, fallback to English, then to the provided default
                return text_attr.get(lang) or text_attr.get("english") or fallback  # type: ignore

        return fallback

    @cached_property
    def buffs(self) -> List[Asset]:
        """Return a list of Assets that can be either BuildingBuff, ShipBuff and so on."""
        allowed_template_names = {"BuildingBuff", "ShipBuff"}
        raw_buffs_list = self.find("Effect.Buffs")

        # Define the output buff list.
        # TODO: Explicity provide the correct template classes here (BuildingBuff, ShipBuff, etc).
        out_buffs: List[Asset] = []

        if isinstance(raw_buffs_list, ListAttribute):
            # print(f"This Effect has {len(raw_buffs_list)} buffs.")
            for i, buff_entry in enumerate(raw_buffs_list):  # type: ignore
                # Get the referenced buff asset
                buff_ref = buff_entry.find("GUID")

                buff_asset: Effect | None
                if isinstance(buff_ref, ReferenceAttribute):
                    # Specialize the "LocalEffect" -> "GUID" referenced asset to "Effect".
                    buff_node = self.cache.get(buff_ref.guid)
                    if isinstance(buff_node, Asset):
                        buff_asset = Effect(buff_node.node, self.cache)

                # TODO: Add the class for BuildingBuff instance here.
                if buff_asset and buff_asset.template.name in allowed_template_names:  # type: ignore
                    # print(
                    #     f"Processing Template: {buff_asset.template.name} for the buff {buff_asset.name} (GUID: {buff_asset.guid})"
                    # )

                    # Asign the buff asset to the output buff list.
                    out_buffs.append(buff_asset)

        return out_buffs
