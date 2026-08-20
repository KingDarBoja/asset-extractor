from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, TypedDict

from assetextractor.conversion.statistics.icon_processor import IconProcessor
from assetextractor.parsing.core.texts import StandardTextConverter
from assetextractor.parsing.typed.map_generator.fertility_pool import FertilityPool
from assetextractor.parsing.typed.map_generator.fertility_set import FertilitySet

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset, AssetCache
    from assetextractor.parsing.typed.economy.fertility import Fertility


# --- Export JSON Types ---


class ResourceSetConditionJSON(TypedDict):
    """Extracted environmental configurations for a fertility set."""

    region: List[str]
    island_type: List[str]
    island_diff: List[str]
    res_amounts: List[str]
    island_size: List[str]


class FertilityOptionJSON(TypedDict):
    """Base payload for an individual fertility option within a slot."""

    guid: str
    name: str
    title: str
    icon_url: str


class FertilitySlotJSON(TypedDict):
    """Metadata representing an ordered slot containing one or more fertility options."""

    index: int
    name: str
    is_pool: bool
    options: List[FertilityOptionJSON]


class FertilitySetJSON(TypedDict):
    """Top-level generation metadata for a Fertility Set."""

    guid: str
    name: str
    condition: ResourceSetConditionJSON
    slots: List[FertilitySlotJSON]


class FertilitySetExtractor:
    """Main orchestrator for extracting 'Fertility Sets' from Anno 117 assets."""

    DEFAULT_PRINT_WIDTH = 100

    def __init__(self, assets: AssetCache, language: str = "english") -> None:
        """Initialize the extractor.

        Parameters
        ----------
        assets : AssetCache
            Asset cache containing all game files and strings.
        language : str, optional
            Language for text localization, by default "english".
        """
        self.assets = assets
        self.language = language
        self.texts = assets.texts
        self.fertility_sets: dict[int, FertilitySet] = {}  # Map of GUID -> FertilitySet
        self.print_width = self.DEFAULT_PRINT_WIDTH

    def _prepare_converter(self) -> None:
        """Ensures the shared cache is using this extractor's language configuration."""
        self.assets.texts.converter = StandardTextConverter(self.language)

    def extract_all(self) -> dict[int, FertilitySet]:
        """Extracts all 'FertilitySet' assets, sorted sequentially by GUID.

        Returns
        -------
        dict[int, FertilitySet]
            A dictionary mapping asset GUIDs to their corresponding sorted FertilitySet instances.
        """
        self._prepare_converter()

        template = self.assets.templates.get("FertilitySet")
        if not template:
            self.fertility_sets = {}
            return {}

        # Filter out valid FertilitySet instances immediately
        valid_assets = (a for a in template.assets if isinstance(a, FertilitySet))

        # Sort the assets by their GUID and construct the ordered dictionary cleanly
        self.fertility_sets = {asset.guid: asset for asset in sorted(valid_assets, key=lambda a: a.guid)}

        return self.fertility_sets

    # --- Printing Methods ---

    def print_fertility_sets(self, guid: int | None = None) -> None:
        """Prints details for stored fertility sets directly from the memory dictionary."""
        if not self.fertility_sets:
            print("No fertility sets loaded in memory. Call extract_all() first.")
            return

        if guid is not None:
            if f_set := self.fertility_sets.get(guid):
                self._print_single_fertility_set(f_set)
            else:
                print(f"FertilitySet with GUID {guid} not found.")
        else:
            for f_set in self.fertility_sets.values():
                self._print_single_fertility_set(f_set)

    def _print_single_fertility_set(self, fert_set: FertilitySet) -> None:
        """Prints formatting for a single 'FertilitySet'."""
        print(f"\n{'=' * self.print_width}")
        print(f"FERTILITY SET: {fert_set.name} (GUID: {fert_set.guid})".center(self.print_width))
        print(f"{'=' * self.print_width}")

        cond = fert_set.resource_set_condition
        print("Generation Conditions:")
        print(f"  Regions:        {', '.join(getattr(e, 'name', str(e)) for e in cond.region)}")
        print(f"  Island Types:   {', '.join(getattr(e, 'name', str(e)) for e in cond.island_type)}")
        print(f"  Difficulties:   {', '.join(getattr(e, 'name', str(e)) for e in cond.island_diff)}")
        print(f"  Res Amounts:    {', '.join(getattr(e, 'name', str(e)) for e in cond.res_amounts)}")
        print(f"  Island Sizes:   {', '.join(getattr(e, 'name', str(e)) for e in cond.island_size)}")
        print(f"{'-' * self.print_width}")

        items = fert_set.fertility_set
        print(f"Contains {len(items)} Fertility Slots:")

        for index, item in enumerate(items):
            if isinstance(item, FertilityPool):
                print(f"\n  [SLOT {index} - POOL] {item.name} (GUID: {item.guid})")
                for fert in item.fertility_pool:
                    self._print_single_fertility(fert)
            else:
                print(f"\n  [SLOT {index} - DIRECT] {item.name} (GUID: {item.guid})")
                self._print_single_fertility(item)

    def _print_single_fertility(self, fert: Fertility) -> None:
        """Prints an individual 'Fertility'."""
        std_name = fert.name
        localized_title = getattr(fert, "localized_title", std_name)
        print(f"      * {localized_title} (GUID: {fert.guid} | {std_name})")

    # --- Export Methods ---

    def to_json_dict(self, web_base_path: str | None = None, flatten: bool = True) -> Dict[str, FertilitySetJSON]:
        """Processes the internal dictionaries directly into a nested JSON payload with ordered slots."""
        self._prepare_converter()

        if not self.fertility_sets:
            self.extract_all()

        export_sets: Dict[str, FertilitySetJSON] = {}

        for set_guid, fert_set in self.fertility_sets.items():
            set_guid_str = str(set_guid)
            cond = fert_set.resource_set_condition

            slots: List[FertilitySlotJSON] = []

            for index, item in enumerate(fert_set.fertility_set):
                if isinstance(item, FertilityPool):
                    options: List[FertilityOptionJSON] = []
                    for fert in item.fertility_pool:
                        fert_icon = IconProcessor.get_icon_package(fert)
                        options.append(
                            {
                                "guid": str(fert.guid),
                                "name": fert.name,
                                "title": fert.text() if fert.text else fert.name,
                                "icon_url": IconProcessor.get_final_url(
                                    raw_path=fert_icon.get("path", ""),
                                    canon_name=fert_icon.get("canon_name", ""),
                                    web_base_path=web_base_path,
                                    flatten=flatten,
                                    default_name=getattr(fert, "canonical_name", fert.name),
                                ),
                            }
                        )

                    slots.append({"index": index, "name": item.name, "is_pool": True, "options": options})

                else:
                    fert_icon = IconProcessor.get_icon_package(item)
                    slots.append(
                        {
                            "index": index,
                            "name": item.name,
                            "is_pool": False,
                            "options": [
                                {
                                    "guid": str(item.guid),
                                    "name": item.name,
                                    "title": item.text() if item.text else item.name,
                                    "icon_url": IconProcessor.get_final_url(
                                        raw_path=fert_icon.get("path", ""),
                                        canon_name=fert_icon.get("canon_name", ""),
                                        web_base_path=web_base_path,
                                        flatten=flatten,
                                        default_name=getattr(item, "canonical_name", item.name),
                                    ),
                                }
                            ],
                        }
                    )

            export_sets[set_guid_str] = {
                "guid": set_guid_str,
                "name": fert_set.name,
                "condition": {
                    "region": [str(e) for e in cond.region],
                    "island_type": [str(e) for e in cond.island_type],
                    "island_diff": [str(e) for e in cond.island_diff],
                    "res_amounts": [str(e) for e in cond.res_amounts],
                    "island_size": [str(e) for e in cond.island_size],
                },
                "slots": slots,
            }

        return export_sets

    def save_to_json(self, file_path: Path | str, web_base_path: str | None = None, flatten: bool = True):
        """Dumps all extracted fertility configurations into a single output JSON file."""
        file_path = Path(file_path)

        data = self.to_json_dict(web_base_path=web_base_path, flatten=flatten)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print(f"Successfully exported fertility data to {file_path}")
        print(f"  - {len(data)} Sets exported")

    def export_all_assets(
        self,
        output_base: Path | str,
        quality: int = 75,
        resize: tuple[int, int] | None = (128, 128),
        flatten: bool = False,
    ):
        """Iterates through all resolved underlying fertilities and exports their icons."""
        output_path = Path(output_base)
        standard_assets: List[Asset] = []
        visited_asset: set[int] = set()

        if not self.fertility_sets:
            self.extract_all()

        # Gather distinct 'Fertility' assets down the tree
        for fert_set in self.fertility_sets.values():
            for item in fert_set.fertility_set:
                if isinstance(item, FertilityPool):
                    for fert in item.fertility_pool:
                        if fert.guid not in visited_asset:
                            standard_assets.append(fert)
                            visited_asset.add(fert.guid)
                else:
                    if item.guid not in visited_asset:
                        standard_assets.append(item)
                        visited_asset.add(item.guid)

        print(f"Started exporting {len(standard_assets)} fertility icons...")
        IconProcessor.export_icons(
            assets=standard_assets,
            output_base=output_path,
            flatten=flatten,
            quality=quality,
            resize=resize,
            use_canonical_name=True,
        )
        print(f"Finished exporting {len(standard_assets)} fertility icons...")
