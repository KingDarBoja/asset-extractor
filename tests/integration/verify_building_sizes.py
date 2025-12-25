"""
Test case to validate building sizes from conversion/calculator/building-sizes.py.

This test compares the building sizes extracted from IFO files against the expected
sizes from the demo_record_building_calculation.csv file.
"""

import csv
import json
import pytest
import importlib.util
from pathlib import Path
from typing import Any

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.parsing.core.templates import Template


# Paths
CSV_PATH = Path("tests/integration/demo_record_building_calculation.csv")
OUTPUT_JSON_PATH = Path("building-sizes.json")
BUILDING_SIZES_SCRIPT = Path("assetextractor/conversion/calculator/building-sizes.py")


def load_converter_module():
    """Dynamically load the building-sizes module (which has a hyphen in the name)."""
    spec = importlib.util.spec_from_file_location("building_sizes", BUILDING_SIZES_SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {BUILDING_SIZES_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildingSizeDifference:
    """Represents a difference between expected and calculated building size."""

    def __init__(
        self,
        building_name: str,
        guid: int | None,
        expected_size: tuple[int, int],
        calculated_size: tuple[int, int] | None,
    ):
        self.building_name = building_name
        self.guid = guid
        self.expected_size = expected_size
        self.calculated_size = calculated_size

    @property
    def difference_type(self) -> str:
        if self.calculated_size is None:
            return "MISSING"
        elif self.expected_size != self.calculated_size:
            return "MISMATCH"
        return "MATCH"

    def __str__(self):
        if self.calculated_size is None:
            return (
                f"\nBuilding: {self.building_name} (GUID: {self.guid})\n"
                f"  Expected: {self.expected_size}\n"
                f"  Calculated: NOT FOUND"
            )
        else:
            return (
                f"\nBuilding: {self.building_name} (GUID: {self.guid})\n"
                f"  Expected: {self.expected_size}\n"
                f"  Calculated: {self.calculated_size}"
            )

    def __repr__(self):
        return self.__str__()


def load_expected_sizes_from_csv(csv_path: Path) -> dict[str, tuple[int, int]]:
    """
    Load expected building sizes from CSV file.

    Returns:
        Dictionary mapping building names to (width, height) tuples
    """
    expected_sizes = {}

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # The CSV has multiple sections with headers
    # We need to find rows with building data
    # Column indices: "factory name" (0), "short side" (8), "long side" (9)

    for row in rows:
        # Skip empty rows
        if not row or len(row) < 10:
            continue

        # Skip header rows and non-building rows
        factory_name = row[0].strip() if len(row) > 1 else ""
        if not factory_name or factory_name == "":
            continue

        # Extract size values
        try:
            short_side_str = row[8].strip() if len(row) > 8 else ""
            long_side_str = row[9].strip() if len(row) > 9 else ""

            # Skip rows without size data
            if not short_side_str or not long_side_str:
                continue

            # Parse as integers
            short_side = int(short_side_str)
            long_side = int(long_side_str)

            # Store as (width, height) - assuming short_side is width, long_side is height
            expected_sizes[factory_name] = (short_side, long_side)

        except (ValueError, IndexError):
            # Skip rows with invalid data
            continue

    return expected_sizes


def find_building_guid_by_name(assets: AssetCache, building_name: str) -> int | None:
    """
    Find the GUID of a building by its English name.

    Args:
        assets: The asset cache
        building_name: The English name of the building

    Returns:
        The GUID if found, None otherwise
    """
    # Search through building templates
    objects_group = assets.templates.groups.get("Objects")
    if objects_group is None or "Buildings" not in objects_group.subgroups:
        return None

    building_group = objects_group.subgroups["Buildings"]

    for template_or_group in building_group:
        # Handle both Template objects and nested groups
        from assetextractor.parsing.core.templates import Template

        if isinstance(template_or_group, Template):
            templates_to_check = [template_or_group]
        else:
            # It's a group, get all templates in it
            templates_to_check = list(template_or_group.elements.values())

        for template in templates_to_check:
            for asset in template.assets:
                # Get the English name
                if asset.text and "english" in asset.text.values:
                    english_name = asset.text.values["english"]
                    if english_name == building_name:
                        return asset.guid

    return None


def compare_building_sizes(
    expected_sizes: dict[str, tuple[int, int]],
    calculated_sizes: dict[int, tuple[int, int]],
    assets: AssetCache,
) -> tuple[list[BuildingSizeDifference], int]:
    """
    Compare expected and calculated building sizes.

    Only compares buildings that are present in the expected_sizes CSV.
    Additional buildings in calculated_sizes are ignored.

    Args:
        expected_sizes: Dictionary mapping building names to expected (width, height)
        calculated_sizes: Dictionary mapping GUIDs to calculated (width, height)
        assets: The asset cache for looking up building names

    Returns:
        Tuple of (differences list, matching_count)
        - differences: List of BuildingSizeDifference objects for mismatches and missing buildings
        - matching_count: Number of buildings with matching sizes
    """
    differences = []
    matching_count = 0

    for building_name, expected_size in expected_sizes.items():
        # Find the GUID for this building
        guid = find_building_guid_by_name(assets, building_name)

        if guid is None:
            # Building not found in assets
            differences.append(
                BuildingSizeDifference(
                    building_name=building_name,
                    guid=None,
                    expected_size=expected_size,
                    calculated_size=None,
                )
            )
            continue

        # Check if we have a calculated size for this GUID
        calculated_size = calculated_sizes.get(guid)

        # Sort both sizes before comparison (CSV uses short side, long side)
        # Building orientation in game may vary, so we compare sorted dimensions
        expected_sorted = tuple(sorted(expected_size)) if expected_size else None
        calculated_sorted = tuple(sorted(calculated_size)) if calculated_size else None

        if calculated_sorted == expected_sorted:
            # Sizes match!
            matching_count += 1
        else:
            differences.append(
                BuildingSizeDifference(
                    building_name=building_name,
                    guid=guid,
                    expected_size=expected_size,
                    calculated_size=calculated_size,
                )
            )

    return differences, matching_count


def save_differences_report(differences: list[BuildingSizeDifference], output_path: Path):
    """Save a detailed report of all differences to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write("BUILDING SIZE VERIFICATION REPORT\n")
        f.write("=" * 100 + "\n\n")

        f.write(f"Total differences: {len(differences)}\n\n")

        # Group by difference type
        missing = [d for d in differences if d.difference_type == "MISSING"]
        mismatches = [d for d in differences if d.difference_type == "MISMATCH"]

        if missing:
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"MISSING BUILDINGS: {len(missing)}\n")
            f.write("=" * 100 + "\n\n")
            for diff in missing:
                f.write(f"Building: {diff.building_name}\n")
                f.write(f"  Expected size: {diff.expected_size}\n")
                f.write(f"  Status: Not found in assets or no calculated size\n\n")

        if mismatches:
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"SIZE MISMATCHES: {len(mismatches)}\n")
            f.write("=" * 100 + "\n\n")
            for diff in mismatches:
                f.write(f"Building: {diff.building_name} (GUID: {diff.guid})\n")
                f.write(f"  Expected:   {diff.expected_size}\n")
                f.write(f"  Calculated: {diff.calculated_size}\n\n")


def test_building_sizes(assets, config):
    """
    Compare calculated building sizes with expected sizes from CSV.

    This test:
    1. Loads expected building sizes from demo_record_building_calculation.csv
    2. Runs the building-sizes.py converter to calculate sizes from IFO files
    3. Compares the results and reports any differences
    """
    # Check that CSV exists
    assert CSV_PATH.exists(), f"CSV file not found: {CSV_PATH}"

    # Load expected sizes from CSV
    expected_sizes = load_expected_sizes_from_csv(CSV_PATH)
    expected_sizes["Opulent Arch"] = (1,3)
    expected_sizes["Commemorative Arch"] = (1,3)

    print(f"\nLoaded {len(expected_sizes)} expected building sizes from CSV")

    # Load the converter module dynamically
    building_sizes_module = load_converter_module()
    Converter = building_sizes_module.Converter

    # Run the converter to calculate building sizes
    converter = Converter(assets)
    converter.run()

    # Load the generated JSON
    assert OUTPUT_JSON_PATH.exists(), f"Generated JSON not found: {OUTPUT_JSON_PATH}"

    with open(OUTPUT_JSON_PATH, "r", encoding="utf-8") as f:
        calculated_sizes = json.load(f)

    # Convert string keys to integers
    calculated_sizes = {int(k): tuple(v) for k, v in calculated_sizes.items()}

    print(f"Calculated {len(calculated_sizes)} building sizes from IFO files")

    # Compare sizes (only for buildings in CSV)
    differences, matching_count = compare_building_sizes(expected_sizes, calculated_sizes, assets)

    # Save detailed report
    report_path = Path("results/test_reports/building_size_differences.txt")
    save_differences_report(differences, report_path)

    # Print summary
    print("\n" + "=" * 80)
    print("BUILDING SIZE VERIFICATION RESULTS")
    print("=" * 80)
    print(f"\nTotal buildings in CSV: {len(expected_sizes)}")
    print(f"Total buildings calculated: {len(calculated_sizes)}")
    print(f"\n✓ Matching building sizes: {matching_count}/{len(expected_sizes)}")
    print(f"✗ Total differences: {len(differences)}/{len(expected_sizes)}")

    # Group by difference type
    missing = [d for d in differences if d.difference_type == "MISSING"]
    mismatches = [d for d in differences if d.difference_type == "MISMATCH"]

    if missing:
        print(f"\nMissing buildings: {len(missing)}")
        for diff in missing[:5]:
            print(f"  - {diff.building_name}: expected {diff.expected_size}")
        if len(missing) > 5:
            print(f"  ... and {len(missing) - 5} more")

    if mismatches:
        print(f"\nSize mismatches: {len(mismatches)}")
        for diff in mismatches[:5]:
            print(
                f"  - {diff.building_name}: expected {diff.expected_size}, "
                f"got {diff.calculated_size}"
            )
        if len(mismatches) > 5:
            print(f"  ... and {len(mismatches) - 5} more")

    if differences:
        print(f"\nDetailed report saved to: {report_path.absolute()}")

    # Assert: The test should pass when there are no differences
    if differences:
        pytest.fail(
            f"\n\n{len(differences)} differences found:\n"
            f"  - {len(missing)} buildings not found or missing size\n"
            f"  - {len(mismatches)} size mismatches\n"
            f"See detailed output above.\n"
            f"Detailed report saved to: {report_path.absolute()}"
        )


def test_csv_loading():
    """Verify that the CSV file can be loaded and parsed."""
    assert CSV_PATH.exists(), f"CSV file not found: {CSV_PATH}"

    expected_sizes = load_expected_sizes_from_csv(CSV_PATH)

    assert len(expected_sizes) > 0, "No building sizes loaded from CSV"

    print(f"\nLoaded {len(expected_sizes)} buildings from CSV:")
    for name, size in list(expected_sizes.items())[:10]:
        print(f"  - {name}: {size}")
    if len(expected_sizes) > 10:
        print(f"  ... and {len(expected_sizes) - 10} more")


def test_building_size_parsing_errors(assets: AssetCache, config, capsys):
    """
    Test that summarizes parsing errors from building-sizes.py.

    This test runs the converter and captures any error messages printed
    when building sizes cannot be determined from IFO files.
    """
    # Load the converter module dynamically
    building_sizes_module = load_converter_module()
    Converter = building_sizes_module.Converter

    # Run the converter (it will print errors to stdout)
    converter = Converter(assets)
    converter.run()

    # Capture the output
    captured = capsys.readouterr()

    # Parse error messages
    error_lines = [
        line for line in captured.out.split("\n")
        if "Size could not be determined" in line or "Error parsing IFO" in line
    ]

    # Count errors by type
    size_determination_errors = [line for line in error_lines if "Size could not be determined" in line]
    ifo_parsing_errors = [line for line in error_lines if "Error parsing IFO" in line]

    # Print summary
    print("\n" + "=" * 80)
    print("BUILDING SIZE PARSING ERROR SUMMARY")
    print("=" * 80)
    print(f"\nTotal buildings processed: {len(converter.building_sizes)}")
    print(f"Size determination errors: {len(size_determination_errors)}")
    print(f"IFO parsing errors: {len(ifo_parsing_errors)}")
    print(f"Total errors: {len(error_lines)}")

    if size_determination_errors:
        print("\n" + "-" * 80)
        print("SIZE DETERMINATION ERRORS (defaulted to 1x1):")
        print("-" * 80)
        for line in size_determination_errors[:10]:
            print(f"  {line.strip()}")
        if len(size_determination_errors) > 10:
            print(f"  ... and {len(size_determination_errors) - 10} more")

    if ifo_parsing_errors:
        print("\n" + "-" * 80)
        print("IFO PARSING ERRORS:")
        print("-" * 80)
        for line in ifo_parsing_errors[:10]:
            print(f"  {line.strip()}")
        if len(ifo_parsing_errors) > 10:
            print(f"  ... and {len(ifo_parsing_errors) - 10} more")

    # Save detailed error report
    if error_lines:
        report_path = Path("results/test_reports/building_size_parsing_errors.txt")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 100 + "\n")
            f.write("BUILDING SIZE PARSING ERROR REPORT\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"Total buildings processed: {len(converter.building_sizes)}\n")
            f.write(f"Total errors: {len(error_lines)}\n\n")

            f.write("\n" + "-" * 100 + "\n")
            f.write("SIZE DETERMINATION ERRORS:\n")
            f.write("-" * 100 + "\n\n")
            for line in size_determination_errors:
                f.write(f"{line.strip()}\n")

            if ifo_parsing_errors:
                f.write("\n" + "-" * 100 + "\n")
                f.write("IFO PARSING ERRORS:\n")
                f.write("-" * 100 + "\n\n")
                for line in ifo_parsing_errors:
                    f.write(f"{line.strip()}\n")

        print(f"\nDetailed error report saved to: {report_path.absolute()}")

        assert False, f"{len(error_lines)} Errors parsing IFO files. Detailed error report saved to: {report_path.absolute()}"

    # Test passes - errors are informational only
    print("\n✓ Parsing errors summary complete")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
