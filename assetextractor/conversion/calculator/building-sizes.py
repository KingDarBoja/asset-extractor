import json
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from lxml import etree

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.parsing.core.attributes import Attribute, FileNameAttribute, ListAttribute
from assetextractor.parsing.core.common import Group
from assetextractor.parsing.core.templates import Template


class ErrorCategory(Enum):
    """Categories for size extraction errors."""

    IFO_NOT_FOUND = "IFO_NOT_FOUND"
    IFO_PARSE_ERROR = "IFO_PARSE_ERROR"
    NO_SIZE_DATA = "NO_SIZE_DATA"


@dataclass
class SizeExtractionError:
    """Represents an error during building size extraction."""

    guid: int
    name: str
    category: ErrorCategory
    details: str


class NpEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, np.integer):
            return int(o.item())
        if isinstance(o, np.floating):
            return float(o.item())
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super(NpEncoder, self).default(o)


class Converter:
    def __init__(self, cache: AssetCache):
        self.assets = cache
        self.building_sizes: dict[int, tuple[int, int]] = {}
        self.errors: list[SizeExtractionError] = []

    @staticmethod
    def get_size_from_filename(filename: str) -> tuple[int, int] | None:
        """
        Extract building size from filename pattern.

        Looks for patterns like '04x04', '10x20', '1x1', etc. in the filename.

        Args:
            filename: The filename to parse

        Returns:
            Tuple of (width, height) or None if pattern not found
        """
        # Match patterns like 04x04, 10x20, 1x1, etc.
        match = re.search(r"(\d+)x(\d+)", filename)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return (width, height)
        return None

    @staticmethod
    def get_size_from_asset_name(asset_name: str) -> tuple[int, int] | None:
        """
        Extract building size from asset name.

        Looks for patterns like '1x1', '2x2', etc. in the asset name.
        Common in ornaments like "Ornament Celtic Statue 1x1 Obelisk".

        Args:
            asset_name: The asset name to parse

        Returns:
            Tuple of (width, height) or None if pattern not found
        """
        # Match patterns like 1x1, 2x2, etc. in asset names
        match = re.search(r"(\d+)x(\d+)", asset_name)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return (width, height)
        return None

    @staticmethod
    def get_custom_size_for_special_buildings(asset: Asset) -> tuple[int, int] | None:
        """
        Get hardcoded size for special building types that don't parse well from IFO.

        Args:
            asset: The asset to check

        Returns:
            Tuple of (width, height) if this is a special building, None otherwise
        """
        template_name = asset.template.name

        # Gates are always 1x3
        if template_name == "MilitaryGate":
            return (1, 3)

        return None

    @staticmethod
    def is_modular_infrastructure(asset: Asset) -> bool:
        """
        Check if asset is modular infrastructure (walls, aqueducts, fields).

        These buildings don't have traditional sizes and should default to 1x1.

        Args:
            asset: The asset to check

        Returns:
            True if the asset is modular infrastructure
        """
        if asset.name is None:
            return False

        name_lower = asset.name.lower()
        template_name = asset.template.name

        # Check for modular building types
        modular_keywords = ["wall", "aqueduct", "field"]
        modular_templates = ["Wall", "Aqueduct", "Field", "MilitaryWall"]

        # Check name
        for keyword in modular_keywords:
            if keyword in name_lower:
                return True

        # Check template
        return template_name in modular_templates

    @staticmethod
    def get_building_size_from_ifo(ifo_path: str | Path) -> tuple[int, int] | None:
        """
        Calculate building size from .ifo file using multiple fallback strategies.

        Tries in order:
        1. BuildBlocker/Position corners (4+ corners)
        2. BoundingBox/Extents (xf/zf dimensions)
        3. Other IFO files in same folder (for gates with separate door files)
        4. Filename pattern (e.g., '04x04')

        Args:
            ifo_path: Path to the .ifo file

        Returns:
            Tuple of (width, height) in grid cells, or None if calculation failed
        """
        try:
            ifo_tree = etree.parse(ifo_path)

            # Strategy 1: BuildBlocker/Position corners
            corners: list[list[float]] = []
            for corner_elem in ifo_tree.findall(".//BuildBlocker/Position"):
                xf_elem = corner_elem.find("xf")
                zf_elem = corner_elem.find("zf")

                if xf_elem is not None and xf_elem.text and zf_elem is not None and zf_elem.text:
                    corners.append([float(xf_elem.text), float(zf_elem.text)])

            if len(corners) >= 4:
                # Convert to numpy array and transpose to separate x and z coordinates
                corners_array = np.array(corners).T  # Shape: (2, n_corners)

                # For buildings with multiple blockers (e.g., mines), use only the first blocker
                # which typically has 4 corners, skip the rest
                if len(corners_array[0]) >= 8:
                    # Calculate diagonals to determine which blocker is the main one
                    diag0 = np.linalg.norm(
                        np.max(corners_array[:, 0:4], axis=1) - np.min(corners_array[:, 0:4], axis=1)
                    )
                    diag1 = np.linalg.norm(
                        np.max(corners_array[:, 4:8], axis=1) - np.min(corners_array[:, 4:8], axis=1)
                    )

                    # Use the smaller blocker (typically 0.1 tolerance)
                    if diag1 > diag0 + 0.1:
                        corners_array = corners_array[:, 0:4]

                # Calculate size as the difference between max and min coordinates
                size_raw = np.max(corners_array, axis=1) - np.min(corners_array, axis=1)
                size = np.array([round(val) for val in size_raw])

                # Return as [x, z] order (no reversal)
                return tuple(size)

            # Strategy 2: BoundingBox/Extents
            bounding_box = ifo_tree.find(".//BoundingBox/Extents")
            if bounding_box is not None:
                xf_elem = bounding_box.find("xf")
                zf_elem = bounding_box.find("zf")

                if xf_elem is not None and xf_elem.text and zf_elem is not None and zf_elem.text:
                    width = round(float(xf_elem.text))
                    height = round(float(zf_elem.text))

                    # BoundingBox values are in physical units (meters), not grid cells
                    # If either dimension is 0, the values are too small and we need fallbacks
                    if width == 0 or height == 0:
                        # Don't return yet, fall through to filename pattern extraction
                        pass
                    else:
                        return (width, height)

            # Strategy 3: Filename pattern
            filename = Path(ifo_path).name
            size_from_filename = Converter.get_size_from_filename(filename)
            if size_from_filename is not None:
                return size_from_filename

            raise ValueError("No size data found in IFO file")

        except Exception as e:
            print(f"Error parsing IFO file {ifo_path}: {e}")
            return None

    @staticmethod
    def get_building_size_from_ifo_folder(folder_path: Path) -> tuple[int, int] | None:
        """
        Calculate building size from a folder containing multiple .ifo files.

        This is used for modular buildings like walls and aqueducts that have
        multiple IFO files for different configurations. The largest size is returned.

        Args:
            folder_path: Path to folder containing .ifo files

        Returns:
            Tuple of (width, height) for the largest IFO, or None if no valid files found
        """
        if not folder_path.exists() or not folder_path.is_dir():
            return None

        # Get all .ifo files excluding preview files
        ifo_files = [f for f in folder_path.glob("*.ifo") if "preview" not in f.name.lower()]

        if not ifo_files:
            return None

        max_size = None
        max_area = 0

        # Parse each IFO and find the largest
        for ifo_file in ifo_files:
            size = Converter.get_building_size_from_ifo(ifo_file)
            if size is not None:
                area = size[0] * size[1]
                if area > max_area:
                    max_area = area
                    max_size = size

        return max_size

    @staticmethod
    def should_exclude_asset(asset: Asset) -> tuple[bool, str]:
        """
        Determine if an asset should be excluded from processing.

        Args:
            asset: The asset to check

        Returns:
            Tuple of (should_exclude, reason)
        """
        # Check if name is None or empty
        if asset.name is None or asset.name == "":
            return (True, "Name is None or empty")

        # Convert name to lowercase for case-insensitive checks
        name_lower = asset.name.lower()

        # Check for various debug/test keywords (case-insensitive)
        exclusion_keywords = ["test", "dummy", "preview", "placeholder", "todelete", "press_version", "debug"]

        for keyword in exclusion_keywords:
            if keyword in name_lower:
                return (True, f"Contains '{keyword}'")

        # Check for MeshGraphHealthDummy template
        if asset.template.name == "MeshGraphHealthDummy":
            return (True, "Template is MeshGraphHealthDummy")

        return (False, "")

    @staticmethod
    def get_building_ifo_path(asset: Asset) -> Path | None:
        """
        Resolve the IFO file path for a building asset.

        Checks multiple sources in priority order:
        1. Object.Variations[0].Filename (standard buildings)
        2. MeshGraphStyle.AdditionalConfigs[0].ConfigFile (gates, hedges)
        3. Wall.TileSetCfgFolder / Aqueduct.TileSetCfgFolder (modular structures)
        4. MeshGraphEdgeSelection.HitBoxReferenceCfg (reference buildings)
        5. Polygon.Path (fallback glob)

        Args:
            asset: The building Asset object

        Returns:
            Path to the .ifo file or folder, or None if not found
        """
        # Priority 1: Object.Variations[0].Filename (standard buildings)
        variations = asset.find("Object.Variations")
        if isinstance(variations, ListAttribute) and len(variations) > 0:
            first_variation = variations[0]
            if first_variation is not None:
                filename_attr = first_variation.find("Filename")
                if isinstance(filename_attr, FileNameAttribute):
                    filename = str(filename_attr).replace(".cfg", ".ifo").replace("Filename: ", "")
                    ifo_path = Path(filename)
                    # Only return if file exists, otherwise fall through to next priority
                    if ifo_path.exists():
                        return ifo_path

        # Priority 2: MeshGraphStyle.AdditionalConfigs[0].ConfigFile (gates, hedges)
        additional_configs = asset.find("MeshGraphStyle.AdditionalConfigs")
        if isinstance(additional_configs, ListAttribute) and len(additional_configs) > 0:
            first_config = additional_configs[0]
            if first_config is not None:
                config_file_attr = first_config.find("ConfigFile")
                if isinstance(config_file_attr, FileNameAttribute):
                    config_file_value = config_file_attr()
                    if config_file_value is not None:
                        config_path = Path(str(config_file_value).replace(".cfg", ".ifo"))
                        # Only return if file exists, otherwise fall through to next priority
                        if config_path.exists():
                            return config_path

        # Priority 3: Wall.TileSetCfgFolder / Aqueduct.TileSetCfgFolder (modular structures)
        tileset_folder = asset.find("Wall.TileSetCfgFolder")
        if tileset_folder is None:
            tileset_folder = asset.find("Aqueduct.TileSetCfgFolder")
        if isinstance(tileset_folder, Attribute):
            folder_value = tileset_folder()
            if folder_value is not None:
                folder_path = Path(str(folder_value))
                if folder_path.exists() and folder_path.is_dir():
                    return folder_path

        # Priority 4: MeshGraphEdgeSelection.HitBoxReferenceCfg (reference buildings)
        hitbox_ref = asset.find("MeshGraphEdgeSelection.HitBoxReferenceCfg")
        if isinstance(hitbox_ref, Attribute):
            hitbox_value = hitbox_ref()
            if hitbox_value is not None:
                ref_path = Path(str(hitbox_value).replace(".cfg", ".ifo"))
                # Only return if file exists, otherwise fall through to next priority
                if ref_path.exists():
                    return ref_path

        # Priority 5: Polygon.Path (fallback glob)
        polygons_path_attr = asset.find("Polygon.Path")
        if not isinstance(polygons_path_attr, Attribute):
            return None

        polygons_path_value = polygons_path_attr()
        if polygons_path_value is None:
            return None

        polygons_path: Path
        if str(polygons_path_value).endswith("modules"):
            polygons_path = Path(str(polygons_path_value).removesuffix("modules"))
        else:
            polygons_path = Path(str(polygons_path_value))

        polygon_files = sorted(polygons_path.glob("*.ifo"))
        for polygon_file in polygon_files:
            return polygon_file

        return None

    def process_assets(self, assets: list[Asset]) -> None:
        for asset in assets:
            # Check if asset should be excluded
            should_exclude, _ = self.should_exclude_asset(asset)
            if should_exclude:
                continue

            # Check for custom hardcoded sizes first (e.g., gates)
            building_size = self.get_custom_size_for_special_buildings(asset)
            if building_size is not None:
                self.building_sizes[asset.guid] = building_size
                continue

            ifo_path = self.get_building_ifo_path(asset)
            error_category = None
            error_details = ""

            if ifo_path is None:
                error_category = ErrorCategory.IFO_NOT_FOUND
                error_details = "No IFO path found in asset"
            else:
                try:
                    if ifo_path.is_dir():
                        # Handle folder paths (modular buildings)
                        building_size = self.get_building_size_from_ifo_folder(ifo_path)
                        if building_size is None:
                            error_category = ErrorCategory.NO_SIZE_DATA
                            error_details = f"Folder exists but no valid IFO files found: {ifo_path}"
                    else:
                        # Handle file paths
                        building_size = self.get_building_size_from_ifo(ifo_path)
                        if building_size is None:
                            error_category = ErrorCategory.IFO_PARSE_ERROR
                            error_details = f"Failed to parse IFO file: {ifo_path}"
                except Exception as e:
                    error_category = ErrorCategory.IFO_PARSE_ERROR
                    error_details = f"Exception during parsing: {e!s}"

            # If still no size, try extracting from asset name (e.g., "Ornament 1x1")
            if building_size is None and asset.name:
                building_size = self.get_size_from_asset_name(asset.name)
                if building_size is not None:
                    # Successfully extracted from name, clear error
                    error_category = None
                    error_details = ""

            if building_size is not None:
                self.building_sizes[asset.guid] = building_size
            else:
                # Default to 1x1
                self.building_sizes[asset.guid] = (1, 1)

                # For modular infrastructure (walls, aqueducts, fields), silently accept 1x1
                # Don't track as error or print message
                if self.is_modular_infrastructure(asset):
                    continue

                # Track the error for non-infrastructure buildings
                if error_category is not None:
                    error = SizeExtractionError(
                        guid=asset.guid, name=asset.name or "Unknown", category=error_category, details=error_details
                    )
                    self.errors.append(error)
                    print(f"Asset ID {asset.guid} ({asset.name}): Size could not be determined")

    def print_error_summary(self):
        """Print categorized error summary."""
        if not self.errors:
            print("\nNo errors encountered!")
            return

        print("\n" + "=" * 80)
        print("ERROR SUMMARY BY CATEGORY")
        print("=" * 80)

        # Count errors by category
        error_counts: dict[str, int] = {}
        for error in self.errors:
            category = error.category.value
            error_counts[category] = error_counts.get(category, 0) + 1

        print(f"\nTotal errors: {len(self.errors)}")
        for category, count in sorted(error_counts.items()):
            print(f"  {category}: {count}")

        # Print first few errors from each category
        for category in ErrorCategory:
            category_errors = [e for e in self.errors if e.category == category]
            if category_errors:
                print(f"\n{category.value} ({len(category_errors)} errors):")
                for error in category_errors[:5]:
                    print(f"  - {error.guid} ({error.name})")
                if len(category_errors) > 5:
                    print(f"  ... and {len(category_errors) - 5} more")

    def run(self) -> None:
        buildings_group = self.assets.templates.groups.get("Objects")
        if buildings_group is None:
            return

        buildings = buildings_group.get("Buildings")
        if buildings is None:
            return

        # Buildings can be either a Template or a Group containing Templates
        if isinstance(buildings, Template):
            self.process_assets(buildings.assets)
        elif isinstance(buildings, Group):
            # It's a group, iterate over its elements
            for element in buildings.elements.values():
                if isinstance(element, Template):
                    self.process_assets(element.assets)

        # Print error summary
        self.print_error_summary()

        os.makedirs("./results/planner", exist_ok=True)
        with open("./results/planner/building-sizes.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.building_sizes, ensure_ascii=False, indent=2, sort_keys=True, cls=NpEncoder))


if __name__ == "__main__":
    config = Config.from_json("config.json")
    cache = AssetCache.load(config)
    converter = Converter(cache)
    converter.run()
