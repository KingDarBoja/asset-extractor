#!/usr/bin/env python
"""Debug why mappings aren't working."""

import logging
logging.basicConfig(level=logging.WARNING)

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)
ui_text_cache = assets.properties.ui_text_cache

# Test AdditionalPercentage mapping
print("=" * 80)
print("Testing AreaFestivalAttributeUpgrade.AdditionalPercentage")
print("=" * 80)
property_name = "AreaFestivalAttributeUpgrade"
attr_name = "AdditionalPercentage"

# Simulate get_buff_type_name logic
property_base = property_name.replace("Upgrade", "") if property_name.endswith("Upgrade") else property_name
print(f"Property base: {property_base}")

attr_base = attr_name
if attr_base.endswith("InPercent"):
    attr_base = attr_base[:-len("InPercent")]
elif attr_base.endswith("Percent"):
    attr_base = attr_base[:-len("Percent")]
print(f"After Percent strip: {attr_base}")

if attr_base.endswith("Upgrade"):
    attr_base = attr_base[:-len("Upgrade")]
print(f"After Upgrade strip: {attr_base}")

if attr_base.startswith("Buff"):
    attr_base = attr_base[4:]
print(f"After Buff strip: {attr_base}")

print(f"Final attr_base: {attr_base}")
print(f"Key: ({property_base}, {attr_base})")

# Call actual method
buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)
print(f"Returned buff_type: {buff_type}")

# Check if BuffFestivalAttributePercentage exists
if "BuffFestivalAttributePercentage" in ui_text_cache.buff_text_structs:
    print("BuffFestivalAttributePercentage EXISTS in cache!")
else:
    print("BuffFestivalAttributePercentage NOT in cache")

print()
print("=" * 80)
print("Testing AreaMaintenanceUpgrade.MeshGraphUpkeep")
print("=" * 80)

# Get asset 62152
asset = assets[62152]
mesh_graph_attr = asset.find("AreaMaintenanceUpgrade.MeshGraphUpkeep")
print(f"Attribute type: {type(mesh_graph_attr)}")
print(f"buff_ui: {mesh_graph_attr.buff_ui}")

if mesh_graph_attr.buff_ui is None:
    # Check if dict values have buff_ui
    print(f"Checking dict values...")
    if mesh_graph_attr.value:
        for key, val in mesh_graph_attr.value.items():
            print(f"  {key}: value={val()}, has buff_ui: {hasattr(val, 'buff_ui')}")
