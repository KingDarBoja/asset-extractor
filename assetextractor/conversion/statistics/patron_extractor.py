import json
from pathlib import Path
from typing import Dict, List, Type, TypedDict, TypeVar

from assetextractor.parsing.core.asset_factories.asset_pool_named import AssetPoolNamed
from assetextractor.parsing.core.asset_factories.patron import Patron
from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.parsing.core.texts import StandardTextConverter


class PatronItemJSON(TypedDict):
    """Patron output JSON structure."""

    uid: int
    name: str  # Standard.Name
    title: str  # English by default
    description: str  # English by default
    """In-game description."""
    image_url: str


AssetT = TypeVar("AssetT", bound="Asset")


class PatronExtractor:
    """Main orchestrator for extracting patrons from Anno 117 assets."""

    def __init__(self, assets: AssetCache, language: str = "english"):
        """Initialize the patrons extractor.

        Args:
            assets: Asset cache with loaded assets
            language: Language for text localization (default: "english")
        """
        self.assets = assets
        self.language = language
        self.texts = assets.texts

    def _prepare_converter(self):
        """Ensures the shared cache is using this extractor's language."""
        self.assets.texts.converter = StandardTextConverter(self.language)

    def get_typed_assets(self, template_name: str, cls: Type[AssetT]) -> List[AssetT]:
        """Helper to get assets and treat them as a specific subclass."""
        template = self.assets.templates.get(template_name)

        if template is None:
            return []

        base_assets = template.assets

        # Re-wrap or cast them to the specialized class
        return [cls(a.node, self.assets) for a in base_assets]

    def extract_all(self):
        """
        Extract all patron assets using the helper asset factories. Right now
        it only prints.
        """
        self._prepare_converter()

        # 1. Get all specialized patron assets.
        patrons = self.get_typed_assets("Patron", Patron)

        for patron in patrons:
            print(f"\n{'=' * 50}")
            print(f"PATRON: {patron.name} (GUID: {patron.guid})")
            print(f"{'=' * 50}")

            for eff_index, effect_data in enumerate(patron.local_effects):
                print(f"Title:       {effect_data.title}")
                print(f"Description: {effect_data.description}")

                if effect_data.asset:
                    print(f"Asset GUID:  {effect_data.asset.guid}")

                    # Asign to helper const.
                    buffs = effect_data.asset.buffs
                    targets = effect_data.asset.targets

                    # Separator.
                    print(f"{'-' * 50}")
                    print(f"Buffs: {len(targets)}")

                    # Buffs processing
                    for buff_index, buff_asset in enumerate(buffs, 1):
                        print(f"  |- {buff_index} Buff - {buff_asset.name} (GUID: {buff_asset.guid})")
                        match buff_asset:
                            case _:
                                # Default generic asset. Do nothing in the meantime.
                                pass

                        # source_cat_attr = buff_asset.find("Buff.SourceCategory")

                        # # Get source category literal.
                        # if self.assets.properties.ui_text_cache and isinstance(source_cat_attr, Attribute):
                        #     source_cat_literal = source_cat_attr()
                        #     if not isinstance(source_cat_literal, str):
                        #         pass

                        #     ui_cache = self.assets.properties.ui_text_cache
                        #     source_cat_mapping = ui_cache.get_ui_text("BuffCategory", source_cat_literal)
                        #     if source_cat_mapping is not None and source_cat_mapping.text is not None:
                        #         source_cat_localized = source_cat_mapping.text()
                        #         print(
                        #             f"Source Category Literal: {source_cat_literal} - Localized: {source_cat_localized}"
                        #         )
                        #     else:
                        #         print(f"Source Category Literal: {source_cat_literal} - Localized: N/A")

                    # Separator.
                    print(f"{'-' * 50}")
                    print(f"Targets: {len(targets)}")

                    # Targets Processing
                    for target_index, target_asset in enumerate(targets, 1):
                        print(f"  |- {target_index} Target - {target_asset.name} (GUID: {target_asset.guid})")
                        match target_asset:
                            case AssetPoolNamed():
                                # Handle the asset pool here.
                                for pool_index, pool_item in enumerate(target_asset.asset_pool_list, 1):
                                    print(f"  * |- {pool_index} Pool Item: {pool_item.name} (GUID: {pool_item.guid})")

                            case _:
                                # Default generic asset. Do nothing in the meantime.
                                pass

                # Separator.
                print(f"{'-' * 50}")

                # Pretty print the Milestones list using asdict for clean JSON output
                if effect_data.milestones:
                    print("Milestones:  ")
                    for mil_index, mil in enumerate(effect_data.milestones):
                        print(f"  * Milestone {mil_index} - Devotion {mil.devotion} - Buff Scaling {mil.buff_scaling}")
                else:
                    print("Milestones:  None")

                if eff_index < len(patron.local_effects) - 1:
                    print(f"{'-' * 50}")

    def to_json_dict(self) -> Dict[str, PatronItemJSON]:
        """
        Processes the patron map into a flat JSON-ready dictionary
        keyed by patron GUID.
        """
        # Switch the shared cache to THIS extractor's language before processing
        self._prepare_converter()

        # TODO: Finish this.
        export_data: Dict[str, PatronItemJSON] = {}

        return export_data

    def save_to_json(self, file_path: Path | str):
        """Helper to write the exported dictionary to a physical file."""
        data = self.to_json_dict()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Successfully exported {len(data)} ornaments to {file_path}")
