from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, TypedDict, cast

from assetextractor.conversion.statistics.icon_processor import IconProcessor
from assetextractor.parsing.core.texts import StandardTextConverter
from assetextractor.parsing.typed.item import Item, ItemWithBoost

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset, AssetCache


@dataclass
class SpecialistCollection:
    """Container for categorized and sorted game assets."""

    items: Dict[int, Item] = field(default_factory=lambda: cast("Dict[int, Item]", {}))
    items_with_boost: Dict[int, ItemWithBoost] = field(default_factory=lambda: cast("Dict[int, ItemWithBoost]", {}))


class SpecialistItemJSON(TypedDict):
    """Specialist output JSON structure."""

    pass


class SpecialistExtractor:
    """Main orchestrator for extracting items from Anno 117 assets."""

    # Dynamic format variable controlling visual separation lines globally
    DEFAULT_PRINT_WIDTH = 100

    def __init__(self, assets: AssetCache, language: str = "english"):
        """Initialize the specialists extractor.

        Args:
            assets: Asset cache with loaded assets
            language: Language for text localization (default: "english")
        """
        self.assets = assets
        self.language = language
        self.texts = assets.texts
        self.specialists = SpecialistCollection()
        self.print_width = self.DEFAULT_PRINT_WIDTH

    def _prepare_converter(self):
        """Ensures the shared cache is using this extractor's language."""
        self.assets.texts.converter = StandardTextConverter(self.language)

    def extract_all(self) -> SpecialistCollection:
        """
        Extracts all 'Item' and 'ItemWithBoost' assets, separates them,
        and saves them sorted by GUID into self.specialists.

        Returns:
            SpecialistCollection: The populated dataclass instance.
        """
        self._prepare_converter()

        tpl_item = self.assets.templates.get("Item")
        tpl_item_boost = self.assets.templates.get("ItemWithBoost")

        # If neither template exists, reset and return empty structure
        if not tpl_item and not tpl_item_boost:
            self.specialists = SpecialistCollection()
            return self.specialists

        # Gather assets from available templates safely
        all_assets: List[Asset] = []
        if tpl_item:
            all_assets.extend(tpl_item.assets)
        if tpl_item_boost:
            all_assets.extend(tpl_item_boost.assets)

        # Separate and map raw assets by type
        raw_items: Dict[int, Item] = {}
        raw_boosts: Dict[int, ItemWithBoost] = {}

        for a in all_assets:
            match a.template.name:
                case "ItemWithBoost":
                    raw_boosts[a.guid] = cast("ItemWithBoost", a)
                case "Item":
                    raw_items[a.guid] = cast("Item", a)
                case _:
                    pass

        # Sort by GUID and lock the order into the respective dictionaries
        sorted_items = {guid: raw_items[guid] for guid in sorted(raw_items.keys())}
        sorted_boosts = {guid: raw_boosts[guid] for guid in sorted(raw_boosts.keys())}

        # Instantiate and save to self.specialists
        self.specialists = SpecialistCollection(items=sorted_items, items_with_boost=sorted_boosts)

        return self.specialists

    # --- Printing Methods ---

    def print_specialists(self, guid: int | None = None):
        """
        Prints details for stored specialists.

        Args:
            guid: If provided, only prints that specific specialist.
                  If None, prints all stored specialists.
        """
        if not self.specialists.items and not self.specialists.items_with_boost:
            print("No specialists loaded in memory. Call extract_all() first.")
            return

        # Combine both dictionaries and print them sorted by key
        all_specialists = {**self.specialists.items, **self.specialists.items_with_boost}
        if guid is not None:
            if specialist := all_specialists.get(guid):
                self._print_single_specialist(specialist)
            else:
                print(f"Specialist with GUID {guid} not found in current results.")
        else:
            for guid in sorted(all_specialists.keys()):
                self._print_single_specialist(all_specialists[guid])

    def _print_single_specialist(self, item: Item):
        """Internal helper to format and print the properties of a single specialist."""
        is_boost = isinstance(item, ItemWithBoost)
        type_label = "SPECIALIST (WITH BOOST)" if is_boost else "SPECIALIST"

        print(f"\n{'=' * self.print_width}")
        print(f"{type_label}: {item.item_standard_info.title} (GUID: {item.guid}) ".center(self.print_width))
        print(f"{'=' * self.print_width}")

        print(f"Standard Name: {item.item_standard_info.std_name}")
        print(f"Description:   {item.item_standard_info.description}")
        print(f"{'-' * self.print_width}")

        info = item.item_info
        print(f"Allocation:    {info.allocation.value if hasattr(info.allocation, 'value') else info.allocation}")
        print(f"Rarity:        {info.rarity.value if hasattr(info.rarity, 'value') else info.rarity}")
        print(f"Niche:         {info.niche.value if hasattr(info.niche, 'value') else info.niche}")
        print(f"Trade Price:   {info.trade_price}")
        print(f"Origin:        {info.origin.value if hasattr(info.origin, 'value') else info.origin}")

        # Specialists don't use the localized chain matching structure of Patrons,
        # so we pass an empty dict safely to comply with AssetWithEffect's print signature.
        item.print_buffs(item.buffs)
        item.print_targets(item.targets, {})

        print(f"{'=' * self.print_width}")

    # --- Export Methods ---

    def to_json_dict(self, web_base_path: str | None = None, flatten: bool = True) -> Dict[str, SpecialistItemJSON]:
        return {}

    def save_to_json(self, file_path: Path | str, web_base_path: str | None = None, flatten: bool = True):
        """
        Helper to write the exported dictionary to a physical file.

        Args:
            file_path: Where to save the actual .json file.
            web_base_path: The URL prefix to use for images inside the JSON.
            flatten: If True, uses canon_name. If False, uses the full
                mirrored relative path.
        """
        data = self.to_json_dict(web_base_path=web_base_path, flatten=flatten)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Successfully exported {len(data)} patrons to {file_path}")

    def export_all_assets(
        self,
        output_base: Path | str,
        quality: int = 75,
        resize: tuple[int, int] | None = (128, 128),
        flatten: bool = False,
    ) -> None:
        """
        Exports all item-related assets.

        Args:
            output_base: The base physical directory where icons will be exported.
            quality: Compression ratio parameter for WebP (1-100). Default is 75.
            resize: Sizing dimension tuple. Default is (128, 128).
            flatten: True to save directly under output_base, False to preserve hierarchy.
        """
        output_path = Path(output_base)
        standard_assets: List[Asset] = []

        for specialist in self.specialists.items.values():
            standard_assets.append(specialist)
        for specialist in self.specialists.items_with_boost.values():
            standard_assets.append(specialist)

        # Batch export all standard icons at 128x128
        print(f"Exporting {len(standard_assets)} specialist icons...")
        IconProcessor.export_icons(
            assets=standard_assets,
            output_base=output_path,
            flatten=flatten,
            quality=quality,
            resize=resize,
            use_canonical_name=True,
        )
