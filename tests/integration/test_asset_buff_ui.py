"""Test the new Asset.buff_ui property."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Test with actual items that have buffs
# Let's find some items with more complex effects
items_template = assets.templates.get("Item")
if items_template:
    # Get items with more buffs to test nested traversal
    test_assets = []
    for item in items_template.assets:
        # Get items with Effect.Buffs to test
        if hasattr(item, "Effect") and item.Effect is not None:
            buffs = item.Effect.Buffs if hasattr(item.Effect, "Buffs") else None
            if buffs and len(buffs) > 0:
                test_assets.append(item)
                if len(test_assets) >= 3:
                    break
else:
    test_assets = []

# If we have specific GUIDs we want to test, use them
test_guids = []

# Test with GUIDs if provided, otherwise use template assets
for asset in (assets.get(guid) for guid in test_guids) if test_guids else test_assets:
    if asset:
        print(f"\n{'='*80}")
        print(f"Asset: {asset.name} ({asset.guid})")
        print(f"Template: {asset.template.name if asset.template else 'None'}")
        print(f"{'='*80}")

        # Get all BuffUI objects from the asset
        buff_ui_list = asset.buff_ui

        print(f"\nFound {len(buff_ui_list)} BuffUI objects:")
        print(f"{'-'*80}")

        for i, buff_ui in enumerate(buff_ui_list, 1):
            print(f"\n{i}. {buff_ui}")
            if buff_ui.icon:
                print(f"   Icon: {buff_ui.icon.value.stem if buff_ui.icon.value else 'None'}")
            if buff_ui.text:
                if hasattr(buff_ui.text, "values"):
                    print(f"   Text: {buff_ui.text.values.get('english', 'N/A')}")
                else:
                    print(f"   Text: {buff_ui.text}")
            if buff_ui.value:
                print(f"   Value: {buff_ui.value}")
            if buff_ui.literal:
                print(f"   Literal: {buff_ui.literal}")

print("\n" + "="*80)
print("Test completed!")
