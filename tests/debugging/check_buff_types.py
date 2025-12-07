#!/usr/bin/env python
"""Check what buff types exist for the missing mappings."""

import logging
logging.basicConfig(level=logging.WARNING)

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)
ui_text_cache = assets.properties.ui_text_cache

print("Available buff types matching our missing attributes:")
print()

# Pattern 1 - No automatic mapping
search_terms = [
    "Festival",
    "PassiveTrade",
    "Cargo",
    "Damage",
    "Wind",
    "Heal",
    "Repair",
    "Crane",
]

for term in search_terms:
    matches = [bt for bt in ui_text_cache.buff_text_structs.keys() if term.lower() in bt.lower()]
    if matches:
        print(f"{term}: {matches}")
    else:
        print(f"{term}: NO MATCHES")

print()
print("=" * 80)
print("Check MeshGraphUpkeep (Pattern 2):")
print("=" * 80)

if "BuffMeshGraphUpkeep" in ui_text_cache.buff_text_structs:
    buff_info = ui_text_cache.buff_text_structs["BuffMeshGraphUpkeep"]
    print(f"BuffMeshGraphUpkeep EXISTS in cache")
    print(f"Structure: {buff_info}")
    print(f"Struct type: {type(buff_info['struct'])}")
    print(f"Variants: {buff_info['variants']}")
else:
    print("BuffMeshGraphUpkeep NOT in cache")
