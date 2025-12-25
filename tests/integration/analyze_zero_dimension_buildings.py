"""
Analyze buildings with zero dimensions in building-sizes.json.

This test identifies buildings where width or height is 0, which indicates
an error in size extraction. Buildings that are not player-placeable should
return None as size, not (0, 0) or (x, 0) or (0, y).
"""

import json
from collections import defaultdict
from pathlib import Path

import pytest

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


def load_building_sizes():
    """Load the building-sizes.json file."""
    json_path = Path("building-sizes.json")
    if not json_path.exists():
        pytest.skip("building-sizes.json not found")

    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def test_analyze_zero_dimension_buildings(assets: AssetCache):
    """Analyze buildings with zero dimensions and group by template."""
    # Load building sizes
    building_sizes = load_building_sizes()

    # Find all buildings with at least one dimension = 0
    zero_dimension_guids = []
    for guid_str, size in building_sizes.items():
        guid = int(guid_str)
        width, height = size

        if width == 0 or height == 0:
            zero_dimension_guids.append(guid)

    if not zero_dimension_guids:
        print("\nSUCCESS: No buildings with zero dimensions found!")
        print("\nAll buildings now have valid sizes (both dimensions > 0).")
        return

    print(f"\n{'=' * 80}")
    print(f"BUILDINGS WITH ZERO DIMENSIONS: {len(zero_dimension_guids)} total")
    print(f"{'=' * 80}\n")

    # Group by template
    by_template = defaultdict(list)

    for guid in zero_dimension_guids:
        asset = assets.elements.get(guid)
        if asset:
            template_name = asset.template.name
            by_template[template_name].append(asset)
        else:
            by_template["UNKNOWN"].append(guid)

    # Print summary by template
    for template_name in sorted(by_template.keys()):
        assets_list = by_template[template_name]
        print(f"\n{template_name}: {len(assets_list)} buildings")
        print("-" * 80)

        for asset in assets_list[:10]:  # Show first 10
            if isinstance(asset, int):
                print(f"  GUID {asset}: (not found in assets)")
                continue

            # Get the size from JSON
            width, height = building_sizes[str(asset.guid)]

            # Get asset name
            name = asset.name if asset.name else "Unknown"

            # Get English text if available
            english_name = "N/A"
            if asset.text and "english" in asset.text.values:
                english_name = asset.text.values["english"]

            # Determine how size was extracted
            import importlib.util
            import sys
            from pathlib import Path as PathLib

            spec = importlib.util.spec_from_file_location(
                "building_sizes", PathLib("assetextractor/conversion/calculator/building-sizes.py")
            )
            building_sizes_module = importlib.util.module_from_spec(spec)
            sys.modules["building_sizes"] = building_sizes_module
            spec.loader.exec_module(building_sizes_module)
            Converter = building_sizes_module.Converter

            ifo_path = Converter.get_building_ifo_path(asset)
            size_method = "Unknown"

            if ifo_path is None:
                size_method = "No IFO path found"
            elif ifo_path.is_dir():
                size_method = f"Folder: {ifo_path.name}"
            else:
                size_method = f"File: {ifo_path.name}"

            # Check if has BoundingBox
            has_bounding_box = "No"
            has_build_blocker = "No"

            if ifo_path and ifo_path.exists() and ifo_path.is_file():
                try:
                    from lxml import etree

                    ifo_tree = etree.parse(ifo_path)
                    if ifo_tree.find(".//BoundingBox/Extents") is not None:
                        has_bounding_box = "Yes"
                    if ifo_tree.findall(".//BuildBlocker/Position"):
                        has_build_blocker = "Yes"
                except:
                    pass

            # Replace problematic characters
            english_name_safe = english_name.encode('ascii', 'replace').decode('ascii')
            name_safe = name.encode('ascii', 'replace').decode('ascii')

            print(
                f"  {asset.guid:6d} | {width}x{height} | {name_safe[:40]:40s} | {english_name_safe[:25]:25s} | {size_method[:30]:30s} | BB:{has_bounding_box} | BL:{has_build_blocker}"
            )

        if len(assets_list) > 10:
            print(f"  ... and {len(assets_list) - 10} more")

    # Write detailed report
    report_path = Path("tests/integration/building_size_investigation_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Buildings with Zero Dimensions Investigation Report\n\n")
        f.write(f"Total buildings with zero dimensions: {len(zero_dimension_guids)}\n\n")

        for template_name in sorted(by_template.keys()):
            assets_list = by_template[template_name]
            f.write(f"\n## {template_name}: {len(assets_list)} buildings\n\n")

            f.write("| GUID | Size | Internal Name | English Name | IFO Source | BoundingBox | BuildBlocker |\n")
            f.write("|------|------|---------------|--------------|------------|-------------|-------------|\n")

            for asset in assets_list:
                if isinstance(asset, int):
                    f.write(f"| {asset} | N/A | UNKNOWN | UNKNOWN | N/A | N/A | N/A |\n")
                    continue

                width, height = building_sizes[str(asset.guid)]
                name = asset.name if asset.name else "Unknown"
                english_name = "N/A"
                if asset.text and "english" in asset.text.values:
                    english_name = asset.text.values["english"]

                import importlib.util
                import sys
                from pathlib import Path as PathLib

                spec = importlib.util.spec_from_file_location(
                    "building_sizes", PathLib("assetextractor/conversion/calculator/building-sizes.py")
                )
                building_sizes_module = importlib.util.module_from_spec(spec)
                sys.modules["building_sizes"] = building_sizes_module
                spec.loader.exec_module(building_sizes_module)
                Converter = building_sizes_module.Converter

                ifo_path = Converter.get_building_ifo_path(asset)
                size_method = "Unknown"

                if ifo_path is None:
                    size_method = "No IFO path"
                elif ifo_path.is_dir():
                    size_method = f"Folder: {ifo_path.name}"
                else:
                    size_method = f"File: {ifo_path.name}"

                has_bounding_box = "No"
                has_build_blocker = "No"

                if ifo_path and ifo_path.exists() and ifo_path.is_file():
                    try:
                        from lxml import etree

                        ifo_tree = etree.parse(ifo_path)
                        if ifo_tree.find(".//BoundingBox/Extents") is not None:
                            has_bounding_box = "Yes"
                        if ifo_tree.findall(".//BuildBlocker/Position"):
                            has_build_blocker = "Yes"
                    except:
                        pass

                f.write(
                    f"| {asset.guid} | {width}x{height} | {name} | {english_name} | {size_method} | {has_bounding_box} | {has_build_blocker} |\n"
                )

    print(f"\n\nDetailed report written to: {report_path}")
    print("\nNext steps:")
    print("1. Review the report to identify patterns")
    print("2. Check BoundingBox values for buildings with (0, y) or (x, 0)")
    print("3. Update building-sizes.py to handle these cases correctly")


if __name__ == "__main__":
    config = Config.from_json("config.json")
    assets = AssetCache.load(config)
    test_analyze_zero_dimension_buildings(assets)
