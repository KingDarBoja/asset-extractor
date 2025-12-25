"""Quick investigation script to check building size calculation."""

import json
from pathlib import Path
from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)
texts = assets.texts

# Load calculated sizes
with open("building-sizes.json", "r") as f:
    calculated_sizes = json.load(f)

# Convert to int keys
calculated_sizes = {int(k): tuple(v) for k, v in calculated_sizes.items()}

# Buildings to check from CSV
test_buildings = {
    "Market": (5, 6),  # Expected from CSV: short=5, long=6
    "Oats": (4, 4),
    "Tunics": (3, 4),
    "Bread": (4, 5),
}

print("=" * 80)
print("BUILDING SIZE INVESTIGATION")
print("=" * 80)
print()

def find_building_by_name(name):
    """Find building GUID by English name."""
    from assetextractor.parsing.core.templates import Template

    # Iterate through all building templates
    for template in assets.templates.groups["Objects"]["Buildings"]:
        if not isinstance(template, Template):
            # It's a nested group
            for nested_template in template.elements.values():
                for asset in nested_template.assets:
                    if asset.text and "english" in asset.text.values:
                        if asset.text.values["english"] == name:
                            return asset.guid, asset
        else:
            # It's a template directly
            for asset in template.assets:
                if asset.text and "english" in asset.text.values:
                    if asset.text.values["english"] == name:
                        return asset.guid, asset

    return None, None

for building_name, expected_size in test_buildings.items():
    guid, asset = find_building_by_name(building_name)

    if guid is None:
        print(f"{building_name}: NOT FOUND")
        continue

    calculated_size = calculated_sizes.get(guid, "NO SIZE CALCULATED")

    # Compare sorted dimensions (CSV uses short side, long side)
    if calculated_size != "NO SIZE CALCULATED":
        expected_sorted = tuple(sorted(expected_size))
        calculated_sorted = tuple(sorted(calculated_size))
        match = "[MATCH]" if calculated_sorted == expected_sorted else "[MISMATCH]"
    else:
        match = "[NO DATA]"

    print(f"{building_name} (GUID {guid}):")
    print(f"  Expected:        {expected_size}")
    print(f"  Calculated:      {calculated_size}")
    if calculated_size != "NO SIZE CALCULATED":
        print(f"  Expected sorted: {expected_sorted}")
        print(f"  Calc sorted:     {calculated_sorted}")
    print(f"  {match}")
    print()

print("=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("Building dimensions are compared after sorting (short side, long side).")
print("This accounts for different building orientations in the game.")
print("The script returns [x, z] order, and both are sorted before comparison.")
