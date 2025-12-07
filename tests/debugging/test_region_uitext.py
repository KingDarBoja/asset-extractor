"""Test script for Region mapping in UITextCache."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Get UITextCache
ui_cache = assets.properties.ui_text_cache

print("Testing Region mapping in UITextCache\n" + "="*80)

# Test regions
regions = ["Roman", "Celtic", "Meta"]

for region_code in regions:
    print(f"\nRegion: {region_code}")

    # Get UI text mapping
    mapping = ui_cache.get_ui_text("Region", region_code)

    if mapping:
        print(f"  Mapping found: Yes")

        # Check text
        if mapping.text:
            print(f"  Text object: {mapping.text}")
            if "english" in mapping.text.values:
                print(f"  English name: {mapping.text.values['english']}")
        else:
            print(f"  Text object: None")

        # Check icon
        if mapping.icon:
            print(f"  Icon: {mapping.icon.value.stem if mapping.icon.value else 'No value'}")
        else:
            print(f"  Icon: None")
    else:
        print(f"  Mapping found: No")

print("\n" + "="*80)

# Test that canonical_name uses the UITextCache
print("\nTesting canonical_name uses UITextCache:")
production_asset = assets[31752]  # Resin Tapper
canonical = production_asset.canonical_name
print(f"  Production asset canonical_name: {canonical}")
print(f"  Should contain 'latium': {'latium' in canonical}")

print("\n" + "="*80)
print("Test complete!")
