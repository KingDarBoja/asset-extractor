import json
from pathlib import Path
from typing import Dict, List, Type, TypedDict, TypeVar

from assetextractor.conversion.statistics.icon_processor import IconProcessor
from assetextractor.parsing.core.asset_factories.construction_category import ConstructionCategory
from assetextractor.parsing.core.asset_factories.ornamental_building import OrnamentalBuilding
from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.parsing.core.texts import StandardTextConverter


class ConstructionGroupJSON(TypedDict):
    """Metadata for the construction category."""

    guid: str
    name: str  # From Standard.Name
    localized_name: str  # From Text.OasisId (localized)


class OrnamentItemJSON(TypedDict):
    """Ornament output JSON structure."""

    uid: int
    name: str  # Standard.Name
    title: str  # English by default
    description: str  # English by default
    """In-game description."""
    image_url: str
    """Icon path to the game assets."""
    prestige: int
    """Prestige points granted by building this ornament."""
    cost: int
    """Denarii value."""
    construction_group: ConstructionGroupJSON
    """The construction group this ornament belongs to."""


AssetT = TypeVar("AssetT", bound="Asset")


class OrnamentsExtractor:
    """Main orchestrator for extracting ornaments from Anno 117 assets."""

    def __init__(self, assets: AssetCache, language: str = "english"):
        """Initialize the ornaments extractor.

        Args:
            assets: Asset cache with loaded assets
            language: Language for text localization (default: "english")
        """
        self.assets = assets
        self.language = language

        # This will store: { CategoryGUID: (CategoryMetadata, [Buildings]) }
        self.category_map: Dict[str, tuple[ConstructionGroupJSON, List[OrnamentalBuilding]]] = {}

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

    def _map_construction_categories(self):
        """
        Traverses ConstructionCategories recursively to find and group
        all OrnamentalBuildings under their respective parent groups.
        """
        # 1. Get all specialized top-level categories
        categories = self.get_typed_assets("ConstructionCategory", ConstructionCategory)

        for category in categories:
            ornaments_in_group: List[OrnamentalBuilding] = []

            # 2. Process the buildings inside this category
            # We use a helper to handle the recursive nesting (Categories inside Categories)
            self._collect_ornaments_recursive(category.building_assets, ornaments_in_group)

            if ornaments_in_group:
                # Build the group metadata using the helper logic
                group_info: ConstructionGroupJSON = {
                    "guid": str(category.guid),
                    "name": category.name,
                    "localized_name": category.localized_title,
                }
                self.category_map[str(category.guid)] = (group_info, ornaments_in_group)

    def _collect_ornaments_recursive(self, assets: List[Asset], collection: List[OrnamentalBuilding]):
        """Internal helper to walk down the building list tree."""
        for asset in assets:
            tpl_name = asset.template.name

            if tpl_name == "OrnamentalBuilding":
                # Specialize the generic Asset into an OrnamentalBuilding
                collection.append(OrnamentalBuilding(asset.node, self.assets))

            elif tpl_name == "ConstructionCategory":
                # If we find a sub-category, specialize it to access its building_assets
                sub_category = ConstructionCategory(asset.node, self.assets)
                self._collect_ornaments_recursive(sub_category.building_assets, collection)

    def extract_all(self):
        """Extract all the OrnamentalBuilding assets using the pre-mapped groups."""
        # 1. Perform the mapping/grouping logic
        self._map_construction_categories()

        # 2. Iterate through the unpacked tuple: (group_info_dict, list_of_ornaments)
        for group_guid, (group_info, ornaments) in self.category_map.items():
            print(f"\nGroup: {group_info['localized_name']} (GUID: {group_guid})")

            for ornament in ornaments:
                print(f"  ---- {ornament.name} (GUID: {ornament.guid})")

                # Safely access specialized properties
                if ornament.costs:
                    denarii_cost = ornament.costs[0]
                    print(f"        Cost: {denarii_cost} denarii")

    def to_json_dict(self) -> Dict[str, OrnamentItemJSON]:
        """
        Processes the category map into a flat JSON-ready dictionary
        keyed by ornament GUID.
        """
        # Switch the shared cache to THIS extractor's language before processing
        self._prepare_converter()

        # Ensure the internal map is built
        if not self.category_map:
            self._map_construction_categories()

        export_data: Dict[str, OrnamentItemJSON] = {}

        for group_guid, (group_info, ornaments) in self.category_map.items():  # type: ignore
            for ornament in ornaments:
                # Icon processing
                icon_package = IconProcessor.get_icon_package(ornament)

                # Using pre-computed costs from OrnamentalBuilding class
                cost_value = ornament.costs[0] if ornament.costs else 0

                # Build the OrnamentItemJSON structure
                guid_key = str(ornament.guid)
                json_item: OrnamentItemJSON = {
                    "uid": ornament.guid,
                    "name": ornament.name,
                    "title": ornament.localized_title,
                    "description": ornament.localized_description,
                    "image_url": icon_package["image_url"] or "",
                    "prestige": ornament.prestige,
                    "cost": int(cost_value),
                    "construction_group": group_info,
                }
                export_data[guid_key] = json_item

        return export_data

    def save_to_json(self, file_path: Path | str):
        """Helper to write the exported dictionary to a physical file."""
        data = self.to_json_dict()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Successfully exported {len(data)} ornaments to {file_path}")
