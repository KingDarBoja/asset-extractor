#!/usr/bin/env python
"""Check what buff types are in the cache."""

import logging
logging.basicConfig(level=logging.WARNING)

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)
ui_text_cache = assets.properties.ui_text_cache

print("Buff types containing 'Health':")
for name in sorted(ui_text_cache.buff_text_structs.keys()):
    if "Health" in name:
        print(f"  {name}")

print("\nBuff types containing 'Movement' or 'Speed':")
for name in sorted(ui_text_cache.buff_text_structs.keys()):
    if "Movement" in name or "Speed" in name:
        print(f"  {name}")

print("\nBuff types containing 'Aqueduct':")
for name in sorted(ui_text_cache.buff_text_structs.keys()):
    if "Aqueduct" in name:
        print(f"  {name}")

print("\nBuff types containing 'Assembly':")
for name in sorted(ui_text_cache.buff_text_structs.keys()):
    if "Assembly" in name:
        print(f"  {name}")

print("\nBuff types containing 'Vehicle' or 'Flag':")
for name in sorted(ui_text_cache.buff_text_structs.keys()):
    if "Vehicle" in name or "Flag" in name:
        print(f"  {name}")

print(f"\nAll {len(ui_text_cache.buff_text_structs)} buff types:")
for name in sorted(ui_text_cache.buff_text_structs.keys()):
    print(f"  {name}")
