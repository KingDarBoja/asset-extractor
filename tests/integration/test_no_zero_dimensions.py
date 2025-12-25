"""
Test that no buildings have zero dimensions in building-sizes.json.

This test ensures that the building size extraction correctly handles
BoundingBox values in physical units and applies appropriate fallbacks.
"""

import json
from pathlib import Path

import pytest


def test_no_zero_dimensions():
    """Verify that no buildings have zero width or height."""
    json_path = Path("building-sizes.json")

    if not json_path.exists():
        pytest.skip("building-sizes.json not found - run building-sizes.py first")

    with open(json_path, encoding="utf-8") as f:
        building_sizes = json.load(f)

    # Find all buildings with at least one dimension = 0
    zero_dimension_buildings = []
    for guid_str, size in building_sizes.items():
        width, height = size
        if width == 0 or height == 0:
            zero_dimension_buildings.append((guid_str, size))

    # Assert no buildings have zero dimensions
    if zero_dimension_buildings:
        error_msg = f"Found {len(zero_dimension_buildings)} buildings with zero dimensions:\n"
        for guid, size in zero_dimension_buildings[:10]:
            error_msg += f"  GUID {guid}: {size[0]}x{size[1]}\n"
        if len(zero_dimension_buildings) > 10:
            error_msg += f"  ... and {len(zero_dimension_buildings) - 10} more\n"
        pytest.fail(error_msg)

    print(f"\nSUCCESS: All {len(building_sizes)} buildings have valid dimensions")
