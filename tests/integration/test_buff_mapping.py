#!/usr/bin/env python
"""Test script for automatic buff type name mapping."""

import logging
logging.basicConfig(level=logging.WARNING)

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)
ui_text_cache = assets.properties.ui_text_cache

# Test assets
test_assets = [
    (51283, "Building Buff - Casponia Casta, Sacerdos Cereris"),
    (42621, "Ship Buff"),
    (80568, "Unit Buff"),
]

all_unmatched = []
matched_count = 0
total_count = 0

for guid, description in test_assets:
    buff_asset = assets.get(guid)
    if not buff_asset:
        print(f"Asset {guid} not found!")
        continue

    for prop in buff_asset:
        if prop.name.endswith("Upgrade"):
            property_name = prop.name

            for attr in prop:
                attr_name = attr.name
                attr_class = attr.__class__.__name__
                total_count += 1

                # Get buff type name using the automatic mapping
                buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)

                if buff_type:
                    matched_count += 1
                else:
                    all_unmatched.append({
                        "asset": guid,
                        "description": description,
                        "property": property_name,
                        "attribute": attr_name,
                        "class": attr_class
                    })

# Print summary
print(f"\n{'='*70}")
print("BUFF TYPE MAPPING RESULTS")
print(f"{'='*70}")
print(f"\nMatched: {matched_count}/{total_count} ({100*matched_count/total_count:.1f}%)")
print(f"Available buff types in cache: {len(ui_text_cache.buff_text_structs)}")

if all_unmatched:
    print(f"\n{'='*70}")
    print(f"UNMATCHED BUFFS: {len(all_unmatched)}")
    print(f"{'='*70}")

    # Group by property
    by_property = {}
    for item in all_unmatched:
        prop = item['property']
        if prop not in by_property:
            by_property[prop] = []
        by_property[prop].append(item)

    for property_name, items in sorted(by_property.items()):
        print(f"\n{property_name}:")
        for item in items:
            asset_desc = item['description']
            print(f"  - {item['attribute']:40s} ({item['class']:20s}) [{asset_desc}]")
else:
    print("\nAll buffs matched successfully!")

print(f"\n{'='*70}")
