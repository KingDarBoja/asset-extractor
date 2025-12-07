"""Detailed test of Asset.buff_ui property showing nested traversal."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Find an item with ItemWithBoost (has both base and boost buffs)
items_with_boost = assets.templates.get("ItemWithBoost")
if items_with_boost and len(items_with_boost.assets) > 0:
    test_asset = list(items_with_boost.assets)[0]

    print("="*80)
    print(f"Testing with ItemWithBoost asset:")
    print(f"Asset: {test_asset.name} ({test_asset.guid})")
    print(f"Template: {test_asset.template.name}")
    print("="*80)

    # Get BuffUI objects
    buff_ui_list = test_asset.buff_ui

    print(f"\nFound {len(buff_ui_list)} BuffUI objects from nested attributes:")
    print("-"*80)

    for i, buff_ui in enumerate(buff_ui_list, 1):
        print(f"\n{i}. {buff_ui}")
        if buff_ui.icon and buff_ui.icon.value:
            print(f"   Icon: {buff_ui.icon.value.stem}")
        if buff_ui.text:
            if hasattr(buff_ui.text, "values"):
                print(f"   Text: {buff_ui.text.values.get('english', 'N/A')}")
            else:
                print(f"   Text: {buff_ui.text}")
        if buff_ui.value:
            print(f"   Value: {buff_ui.value}")
        if buff_ui.literal:
            print(f"   Literal: {buff_ui.literal}")

# Also test with a building buff asset
building_buff_template = assets.templates.get("BuildingBuff")
if building_buff_template and len(building_buff_template.assets) > 0:
    # Find a buff with multiple upgrade attributes
    for buff_asset in building_buff_template.assets:
        buff_ui_list = buff_asset.buff_ui
        if len(buff_ui_list) > 2:  # Find one with multiple buffs
            print("\n" + "="*80)
            print(f"Testing with BuildingBuff asset:")
            print(f"Asset: {buff_asset.name} ({buff_asset.guid})")
            print(f"Template: {buff_asset.template.name}")
            print("="*80)

            print(f"\nFound {len(buff_ui_list)} BuffUI objects:")
            print("-"*80)

            for i, buff_ui in enumerate(buff_ui_list, 1):
                print(f"\n{i}. {buff_ui}")
                if buff_ui.icon and buff_ui.icon.value:
                    print(f"   Icon: {buff_ui.icon.value.stem}")
                if buff_ui.text:
                    if hasattr(buff_ui.text, "values"):
                        print(f"   Text: {buff_ui.text.values.get('english', 'N/A')}")
                    else:
                        print(f"   Text: {buff_ui.text}")
                if buff_ui.value:
                    print(f"   Value: {buff_ui.value}")
                if buff_ui.literal:
                    print(f"   Literal: {buff_ui.literal}")

            break  # Only show first one with multiple buffs

print("\n" + "="*80)
print("Detailed test completed!")
print("="*80)
