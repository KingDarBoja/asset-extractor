import json
from pathlib import Path
from typing import Dict, List, TypedDict

from assetextractor.conversion.statistics.icon_processor import IconProcessor
from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.parsing.core.texts import StandardTextConverter
from assetextractor.parsing.typed.buildings.ornamental_building import OrnamentalBuilding
from assetextractor.parsing.typed.construction_category import ConstructionCategory

# Safely import IPython's display for Jupyter Notebook integration
try:
    from IPython.display import HTML, display  # type: ignore
except ImportError:
    display, HTML = None, None  # type: ignore


class ConstructionGroupJSON(TypedDict):
    """Metadata for the construction category."""

    guid: str
    name: str  # From Standard.Name
    localized_name: str  # From Text.OasisId (localized)
    icon_url: str


class OrnamentItemJSON(TypedDict):
    """Ornament output JSON structure."""

    uid: int
    name: str  # Standard.Name
    title: str  # English by default
    description: str  # English by default
    """In-game description."""
    icon_url: str
    """Icon path to the game assets."""
    origin: str
    """If this ornament is unlocked by a DLC, twitch drop, etc. Defaults to
    'Base'."""
    prestige: int
    """Prestige points granted by building this ornament."""
    cost: int
    """Denarii value."""
    construction_group: ConstructionGroupJSON
    """The immediate parent construction group this ornament belongs to."""
    top_level_group: ConstructionGroupJSON
    """The root construction group of the construction group."""


class OrnamentsExtractor:
    """Main orchestrator for extracting ornaments from Anno 117 assets."""

    # Dynamic format variable controlling visual separation lines globally
    DEFAULT_PRINT_WIDTH = 100

    def __init__(self, assets: AssetCache, language: str = "english"):
        """Initialize the ornaments extractor.

        Args:
            assets: Asset cache with loaded assets
            language: Language for text localization (default: "english")
        """
        self.assets = assets
        self.language = language
        self.print_width = self.DEFAULT_PRINT_WIDTH

        self.ornaments: Dict[int, OrnamentalBuilding] = {}  # Stores results after extract_all()
        # Updated map to store: { TopGUID: (TopMetadata, [(Ornament, SubGroupMetadata)]) }
        self.category_map: Dict[
            str, tuple[ConstructionCategory, List[tuple[OrnamentalBuilding, ConstructionCategory]]]
        ] = {}

    def _prepare_converter(self):
        """Ensures the shared cache is using this extractor's language."""
        self.assets.texts.converter = StandardTextConverter(self.language)

    def _map_construction_categories(self):
        """
        Traverses 'ConstructionCategories' recursively to find and group all
        'OrnamentalBuilding' assets under their respective parent groups.
        """
        template = self.assets.templates.get("ConstructionCategory")
        categories = [a for a in template.assets if isinstance(a, ConstructionCategory)] if template else []

        for category in categories:
            # We will store pairs: (The Asset, The specific group it was found in)
            ornaments_with_info: List[tuple[OrnamentalBuilding, ConstructionCategory]] = []

            # 2. Process the buildings inside this category
            # We use a helper to handle the recursive nesting (Categories inside Categories).
            # Start recursion, passing the top-level info as the first 'current_group'
            self._collect_ornaments_recursive(category.building_assets, ornaments_with_info, category)

            if ornaments_with_info:
                self.category_map[str(category.guid)] = (category, ornaments_with_info)

    def _collect_ornaments_recursive(
        self,
        assets: List[Asset],
        collection: List[tuple[OrnamentalBuilding, ConstructionCategory]],
        current_group: ConstructionCategory,
    ):
        """Walks the tree, supporting multiple templates and capturing sub-groups."""
        for asset in assets:
            if isinstance(asset, OrnamentalBuilding):
                collection.append((asset, current_group))
            elif isinstance(asset, ConstructionCategory):
                self._collect_ornaments_recursive(asset.building_assets, collection, asset)

    def extract_all(self) -> Dict[int, OrnamentalBuilding]:
        """
        Extract all ornament-like assets using the nested category mapping.
        Handles both OrnamentalBuilding and PolygonObject.
        """
        self._map_construction_categories()

        processed_guids: set[int] = set()  # Tracking set for de-duplication

        # After processing the construction categories, we build the ornaments
        # dictionary as well.
        for _, items in self.category_map.values():
            for ornament, _ in items:
                # SKIP if we have already exported this ornament.
                if ornament.guid in processed_guids:
                    continue

                processed_guids.add(ornament.guid)
                self.ornaments[ornament.guid] = ornament

        return self.ornaments

    # --- Printing Methods ---

    def print_ornaments(self, guid: int | None = None):
        """
        Prints details for stored ornaments.

        Args:
            guid: If provided, only prints that specific ornament.
                  If None, prints all stored ornaments.
        """
        if not self.category_map:
            print("No ornaments loaded in memory. Call extract_all() first.")
            return

        if guid is not None:
            if ornament := self.ornaments.get(guid):
                self._print_single_ornament(ornament)
            else:
                print(f"Ornament with GUID {guid} not found in current results.")
        else:
            for ornament in self.ornaments.values():
                self._print_single_ornament(ornament)

    def _print_single_ornament(self, ornament: OrnamentalBuilding) -> None:
        # Iterate through the Top-Level Groups
        # The map stores: { TopGUID: (TopMetadata, [(Ornament, SubGroupMetadata)]) }
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

                # Extract raw bytes from the object's rich-display representation hooks
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
                    # Dynamic theme-aware side-by-side flexbox layout
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

        # Fallback to normal stacked text/image print if running outside a notebook
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

    def to_json_dict(self, web_base_path: str | None = None, flatten: bool = True) -> Dict[str, OrnamentItemJSON]:
        """
        Processes the category map into a flat JSON-ready dictionary
        keyed by ornament GUID.

        Args:
            web_base_path: Folder prefix (e.g. 'assets/icons/patrons').
            flatten: If True, uses canon_name. If False, uses the full
                mirrored relative path.
        """
        # Switch the shared cache to THIS extractor's language before processing
        self._prepare_converter()

        # Ensure the internal map is built
        if not self.category_map:
            self._map_construction_categories()

        export_data: Dict[str, OrnamentItemJSON] = {}
        processed_guids: set[int] = set()  # Tracking set for de-duplication

        for top_info, items in self.category_map.values():
            for ornament, sub_info in items:
                # SKIP if we have already exported this ornament.
                if ornament.guid in processed_guids:
                    continue

                processed_guids.add(ornament.guid)

                # Icon processing
                ornament_icon = IconProcessor.get_icon_package(ornament)

                # Using pre-computed costs from OrnamentalBuilding class
                cost_value = ornament.formatted_costs[0].amount if ornament.costs else 0

                # Format to ConstructionGroupJSON the top and sub info.
                top_level_group_icon = IconProcessor.get_icon_package(top_info)
                top_level_group_icon_path = IconProcessor.get_final_url(
                    raw_path=top_level_group_icon["path"],
                    canon_name=top_level_group_icon["canon_name"],
                    web_base_path=web_base_path,
                    flatten=flatten,
                    default_name=top_info.canonical_name,
                )
                top_level_group: ConstructionGroupJSON = {
                    "guid": str(top_info.guid),
                    "name": top_info.name,
                    "localized_name": top_info.localized_title,
                    "icon_url": top_level_group_icon_path,
                }

                sub_group_icon = IconProcessor.get_icon_package(sub_info)
                sub_group_icon_path = IconProcessor.get_final_url(
                    raw_path=sub_group_icon["path"],
                    canon_name=sub_group_icon["canon_name"],
                    web_base_path=web_base_path,
                    flatten=flatten,
                    default_name=sub_info.canonical_name,
                )
                sub_group_info: ConstructionGroupJSON = {
                    "guid": str(sub_info.guid),
                    "name": sub_info.name,
                    "localized_name": sub_info.localized_title,
                    "icon_url": sub_group_icon_path,
                }

                # Build the OrnamentItemJSON structure
                guid_key = str(ornament.guid)
                json_item: OrnamentItemJSON = {
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
                    "construction_group": sub_group_info,  # Immediate Parent (e.g., 'Benches')
                    "top_level_group": top_level_group,  # Root Parent (e.g., 'Classic')
                }
                export_data[guid_key] = json_item

        return export_data

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
        print(f"Successfully exported {len(data)} ornaments to {file_path}")

    def export_all_assets(
        self,
        output_base: Path | str,
        quality: int = 75,
        resize: tuple[int, int] | None = (128, 128),
        flatten: bool = False,
    ):
        """
        Exports all ornament-related assets.

        Args:
            output_base: The base physical directory where icons will be exported.
            quality: Compression ratio parameter for WebP (1-100). Default is 75.
            resize: Sizing dimension tuple. Default is (128, 128).
            flatten: True to save directly under output_base, False to preserve hierarchy.
        """
        output_path = Path(output_base)
        standard_assets: List[Asset] = []

        # De-duplication check.
        visited_asset: List[int] = []

        for top_info, items in self.category_map.values():
            if top_info.guid not in visited_asset:
                # 0. Sub-Assets (top construction group icons)
                standard_assets.append(top_info)
                visited_asset.append(top_info.guid)

            for ornament, sub_info in items:
                # 1. Main Ornament Icon
                if ornament.guid not in visited_asset:
                    standard_assets.append(ornament)
                    visited_asset.append(ornament.guid)

                # 2. Sub-Assets (construction group icons)
                if sub_info.guid not in visited_asset:
                    standard_assets.append(sub_info)
                    visited_asset.append(sub_info.guid)

        # Batch export all standard icons at 128x128
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
