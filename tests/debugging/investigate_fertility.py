#!/usr/bin/env python
"""Investigate why FertilityPercent shows as missing buff_ui."""

import logging
logging.basicConfig(level=logging.WARNING)

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
print("Loading assets...")
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Asset 42658 - the one my test found
print("=" * 80)
print("Asset 42658 (from test_missing_buff_ui.py):")
print("=" * 80)
asset = assets[42658]
print(f"Asset: {asset}")
print(f"FertilityPercent value: {asset.FactoryUpgrade.FertilityPercent()}")
print(f"FertilityPercent buff_ui: {asset.FactoryUpgrade.FertilityPercent.buff_ui}")
print(f"AddedFertility value: {asset.FactoryUpgrade.AddedFertility()}")
print()

# Assets that work (from user's example)
print("=" * 80)
print("Assets with AddedFertility (working examples):")
print("=" * 80)
for asset in assets.templates["BuildingBuff"].assets:
    if asset.FactoryUpgrade.AddedFertility() is not None:
        fert_percent = asset.FactoryUpgrade.FertilityPercent()
        buff_ui = asset.FactoryUpgrade.FertilityPercent.buff_ui
        added_fert = asset.FactoryUpgrade.AddedFertility()

        print(f"GUID {asset.guid}:")
        print(f"  FertilityPercent: {fert_percent}")
        print(f"  AddedFertility: {added_fert}")
        print(f"  buff_ui: {buff_ui}")
        print()

        if len([a for a in assets.templates["BuildingBuff"].assets if a.FactoryUpgrade.AddedFertility() is not None]) >= 3:
            break

# Check all assets with FertilityPercent set
print("=" * 80)
print("All assets with FertilityPercent != 0:")
print("=" * 80)
count = 0
for asset in assets.templates["BuildingBuff"].assets:
    fert_percent_attr = asset.find("FactoryUpgrade.FertilityPercent")
    if fert_percent_attr and fert_percent_attr.value and fert_percent_attr.value != 0:
        fert_percent = fert_percent_attr()
        added_fert = asset.FactoryUpgrade.AddedFertility()
        buff_ui = fert_percent_attr.buff_ui

        print(f"GUID {asset.guid}: FertilityPercent={fert_percent}, AddedFertility={added_fert}, buff_ui={buff_ui is not None}")
        count += 1

        if count >= 10:
            print("... (limited to 10)")
            break

print()
print(f"Total assets with FertilityPercent != 0: {sum(1 for a in assets.templates['BuildingBuff'].assets if a.find('FactoryUpgrade.FertilityPercent') and a.find('FactoryUpgrade.FertilityPercent').value and a.find('FactoryUpgrade.FertilityPercent').value != 0)}")
