import json
from pathlib import Path
from typing import Dict, List, TypedDict

from assetextractor.conversion.statistics.icon_processor import IconProcessor
from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.parsing.core.texts import StandardTextConverter
from assetextractor.parsing.typed.buildings.ornamental_building import OrnamentalBuilding
from assetextractor.parsing.typed.construction_category import ConstructionCategory

try:
    from IPython.display import HTML, display  # type: ignore
except ImportError:
    display, HTML = None, None  # type: ignore


# --- Export JSON Types ---


class ConstructionGroupJSON(TypedDict):
    """Metadata for the construction category."""

    guid: str
    name: str
    localized_name: str
    icon_url: str


class OrnamentGroupPlacementJSON(TypedDict):
    """Link between an ornament and its construction categories."""

    top_level_guid: str
    construction_group_guid: str


class OrnamentItemJSON(TypedDict):
    """Ornament output JSON structure."""

    uid: int
    name: str
    title: str
    description: str
    icon_url: str
    origin: str
    prestige: int
    cost: int
    construction_groups: List[OrnamentGroupPlacementJSON]


# --- Internal Inverted Extractor Types ---


class CategoryPlacement(TypedDict):
    """Internal tracking for an ornament's category placement."""

    category: ConstructionCategory
    subcategories: List[ConstructionCategory]


class OrnamentExtended(TypedDict):
    """Inverted container pairing an ornament asset with all its mapped groups."""

    asset: OrnamentalBuilding
    categories: Dict[int, CategoryPlacement]  # Keyed by Top Level Category GUID


class OrnamentsExtractor:
    """Orchestrator for extracting ornaments using an inverted ornament-first mapping."""

    DEFAULT_PRINT_WIDTH = 100

    def __init__(self, assets: AssetCache, language: str = "english"):
        self.assets = assets
        self.language = language
        self.print_width = self.DEFAULT_PRINT_WIDTH

        # The primary, inverted in-memory database: { OrnamentGUID -> OrnamentExtended }
        self.ornaments: Dict[int, OrnamentExtended] = {}

    def _prepare_converter(self):
        """Ensures the shared cache is using this extractor's language."""
        self.assets.texts.converter = StandardTextConverter(self.language)

    def _map_construction_categories(self):
        """Traverses ConstructionCategories and populates the inverted self.ornaments registry."""
        self.ornaments.clear()
        template = self.assets.templates.get("ConstructionCategory")
        categories = [a for a in template.assets if isinstance(a, ConstructionCategory)] if template else []

        for top_category in categories:
            # Recursively walk downstream, preserving the top-level parent category context
            self._collect_ornaments_recursive(
                assets=top_category.building_assets, top_category=top_category, current_sub_category=top_category
            )

    def _collect_ornaments_recursive(
        self, assets: List[Asset], top_category: ConstructionCategory, current_sub_category: ConstructionCategory
    ):
        """Walks the category tree, populating the extended ornament map directly."""
        for asset in assets:
            if isinstance(asset, OrnamentalBuilding):
                guid = asset.guid

                # 1. Initialize the ornament item if it hasn't been encountered yet
                if guid not in self.ornaments:
                    self.ornaments[guid] = {"asset": asset, "categories": {}}

                # 2. Initialize the top level group grouping for this ornament
                top_guid = top_category.guid
                if top_guid not in self.ornaments[guid]["categories"]:
                    self.ornaments[guid]["categories"][top_guid] = {"category": top_category, "subcategories": []}

                # 3. Append the immediate sub-category group without duplicates
                sub_list = self.ornaments[guid]["categories"][top_guid]["subcategories"]
                if current_sub_category not in sub_list:
                    sub_list.append(current_sub_category)

            elif isinstance(asset, ConstructionCategory):
                # Pass down the original top_category context alongside the new nested sub-group
                self._collect_ornaments_recursive(asset.building_assets, top_category, asset)

    def extract_all(self) -> Dict[int, OrnamentExtended]:
        """Extracts and maps all ornaments directly to their category hierarchies."""
        self._map_construction_categories()
        return self.ornaments

    # --- Printing Methods ---

    def print_ornaments(self, guid: int | None = None):
        """Prints details for stored ornaments directly from the inverted dictionary."""
        if not self.ornaments:
            print("No ornaments loaded in memory. Call extract_all() first.")
            return

        if guid is not None:
            if extended_entry := self.ornaments.get(guid):
                self._print_single_ornament(extended_entry["asset"])
            else:
                print(f"Ornament with GUID {guid} not found.")
        else:
            for extended_entry in self.ornaments.values():
                self._print_single_ornament(extended_entry["asset"])

    def _print_single_ornament(self, ornament: OrnamentalBuilding) -> None:
        print(f"\n{'=' * self.print_width}")
        print(f"ORNAMENT: {ornament.localized_title} (GUID: {ornament.guid}) ".center(self.print_width))
        print(f"{'=' * self.print_width}")

        std_name = ornament.name
        description = ornament.localized_description

        rendered_side_by_side = False
        if display is not None and HTML is not None:
            icon_data = IconProcessor.get_icon_package(ornament, include_image=True)
            img = icon_data.get("image")
            if img is not None:
                import base64

                b64_data = None
                mime_type = "image/png"

                for attr, mime in [
                    ("_repr_png_", "image/png"),
                    ("_repr_webp_", "image/webp"),
                    ("_repr_jpeg_", "image/jpeg"),
                ]:
                    if hasattr(img, attr):
                        try:
                            raw_bytes = getattr(img, attr)()
                            if raw_bytes:
                                b64_data = base64.b64encode(raw_bytes).decode("utf-8")
                                mime_type = mime
                                break
                        except Exception:
                            pass

                if b64_data:
                    html_content = f"""
                    <div style="display: flex; align-items: flex-start; gap: 16px; margin: 12px 0; font-family: var(--jp-ui-font-family, sans-serif); color: var(--jp-ui-font-color1, #111);">
                        <div style="flex-shrink: 0; width: 64px; height: 64px; border: 1px solid var(--jp-border-color2, #ccc); border-radius: 4px; overflow: hidden; background: #2a2a2a; display: flex; align-items: center; justify-content: center;">
                            <img src="data:{mime_type};base64,{b64_data}" style="width: 64px; height: 64px; object-fit: contain;" />
                        </div>
                        <div style="display: flex; flex-direction: column; justify-content: center; min-height: 64px; line-height: 1.5;">
                            <div><strong style="color: var(--jp-ui-font-color2, #444);">Standard Name:</strong> {std_name}</div>
                            <div style="margin-top: 2px;"><strong style="color: var(--jp-ui-font-color2, #444);">Description:</strong> <span style="font-style: italic; color: var(--jp-ui-font-color3, #666);">{description}</span></div>
                        </div>
                    </div>
                    """
                    display(HTML(html_content))
                    rendered_side_by_side = True

        if not rendered_side_by_side:
            if display is not None:
                icon_data = IconProcessor.get_icon_package(ornament, include_image=True)
                if img := icon_data.get("image"):
                    display(img, metadata={"image/png": {"width": 64, "height": 64}})

            print(f"Standard Name: {std_name}")
            print(f"Description:   {description}")

        print(f"{'-' * self.print_width}")
        print(f"Cost:          {int(ornament.formatted_costs[0].amount) if ornament.costs else 0} denarii")
        print(f"Prestige:      {ornament.prestige}")
        print(f"Unlocked By:   {ornament.origin_hint_ui}")

    # --- Export Methods ---

    def to_json_dict(
        self, web_base_path: str | None = None, flatten: bool = True
    ) -> tuple[Dict[str, OrnamentItemJSON], Dict[str, ConstructionGroupJSON]]:
        """Processes the inverted database directly into separate clean export payloads."""
        self._prepare_converter()

        if not self.ornaments:
            self._map_construction_categories()

        export_ornaments: Dict[str, OrnamentItemJSON] = {}
        export_categories: Dict[str, ConstructionGroupJSON] = {}

        for guid, extended_entry in self.ornaments.items():
            ornament = extended_entry["asset"]
            guid_key = str(guid)

            ornament_icon = IconProcessor.get_icon_package(ornament)
            cost_value = ornament.formatted_costs[0].amount if ornament.costs else 0

            # Map the flat attributes directly onto the primary ornament profile
            export_ornaments[guid_key] = {
                "uid": ornament.guid,
                "name": ornament.name,
                "title": ornament.localized_title,
                "description": ornament.localized_description,
                "origin": ornament.origin_hint_ui,
                "icon_url": IconProcessor.get_final_url(
                    raw_path=ornament_icon["path"],
                    canon_name=ornament_icon["canon_name"],
                    web_base_path=web_base_path,
                    flatten=flatten,
                    default_name=ornament.canonical_name,
                ),
                "prestige": ornament.prestige,
                "cost": cost_value,
                "construction_groups": [],
            }

            # Loop through the pre-aggregated clean category structures
            for top_guid, placement in extended_entry["categories"].items():
                top_info = placement["category"]
                top_guid_str = str(top_guid)

                # Extract top level category metadata
                if top_guid_str not in export_categories:
                    top_icon = IconProcessor.get_icon_package(top_info)
                    export_categories[top_guid_str] = {
                        "guid": top_guid_str,
                        "name": top_info.name,
                        "localized_name": top_info.localized_title,
                        "icon_url": IconProcessor.get_final_url(
                            raw_path=top_icon["path"],
                            canon_name=top_icon["canon_name"],
                            web_base_path=web_base_path,
                            flatten=flatten,
                            default_name=top_info.canonical_name,
                        ),
                    }

                # Extract subcategory metadata and append the explicit configuration mapping
                for sub_info in placement["subcategories"]:
                    sub_guid_str = str(sub_info.guid)

                    if sub_guid_str not in export_categories:
                        sub_icon = IconProcessor.get_icon_package(sub_info)
                        export_categories[sub_guid_str] = {
                            "guid": sub_guid_str,
                            "name": sub_info.name,
                            "localized_name": sub_info.localized_title,
                            "icon_url": IconProcessor.get_final_url(
                                raw_path=sub_icon["path"],
                                canon_name=sub_icon["canon_name"],
                                web_base_path=web_base_path,
                                flatten=flatten,
                                default_name=sub_info.canonical_name,
                            ),
                        }

                    # Add the relationship to the ornament configuration array
                    export_ornaments[guid_key]["construction_groups"].append(
                        {"top_level_guid": top_guid_str, "construction_group_guid": sub_guid_str}
                    )

        return export_ornaments, export_categories

    def save_to_json(
        self,
        file_path: Path | str,
        categories_file_path: Path | str | None = None,
        web_base_path: str | None = None,
        flatten: bool = True,
    ):
        file_path = Path(file_path)
        if categories_file_path is None:
            categories_file_path = file_path.parent / f"categories_{file_path.name}"
        else:
            categories_file_path = Path(categories_file_path)

        ornaments_data, categories_data = self.to_json_dict(web_base_path=web_base_path, flatten=flatten)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(ornaments_data, f, indent=4)
        print(f"Successfully exported {len(ornaments_data)} ornaments to {file_path}")

        with open(categories_file_path, "w", encoding="utf-8") as f:
            json.dump(categories_data, f, indent=4)
        print(f"Successfully exported {len(categories_data)} categories to {categories_file_path}")

    def export_all_assets(
        self,
        output_base: Path | str,
        quality: int = 75,
        resize: tuple[int, int] | None = (128, 128),
        flatten: bool = False,
    ):
        output_path = Path(output_base)
        standard_assets: List[Asset] = []
        visited_asset: set[int] = set()

        if not self.ornaments:
            self._map_construction_categories()

        # Gather file components neatly without processing duplicate assets
        for extended_entry in self.ornaments.values():
            ornament = extended_entry["asset"]
            if ornament.guid not in visited_asset:
                standard_assets.append(ornament)
                visited_asset.add(ornament.guid)

            for placement in extended_entry["categories"].values():
                top_info = placement["category"]
                if top_info.guid not in visited_asset:
                    standard_assets.append(top_info)
                    visited_asset.add(top_info.guid)

                for sub_info in placement["subcategories"]:
                    if sub_info.guid not in visited_asset:
                        standard_assets.append(sub_info)
                        visited_asset.add(sub_info.guid)

        print(f"Started exporting {len(standard_assets)} ornaments icons...")
        IconProcessor.export_icons(
            assets=standard_assets,
            output_base=output_path,
            flatten=flatten,
            quality=quality,
            resize=resize,
            use_canonical_name=True,
        )
        print(f"Finished exporting {len(standard_assets)} ornaments icons...")
