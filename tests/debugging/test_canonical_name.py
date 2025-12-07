"""Test script for canonical_name property on Asset and FileNameAttribute."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Test cases from the examples
test_cases = [
    {
        "guid": 31752,
        "expected_asset": "production_resin_tapper_latium",
        "expected_icon": "icon_production_resin_tapper_latium",
        "description": "Production Area - Resin Tapper (Roman/Latium)"
    },
    {
        "guid": 41350,
        "expected_asset": "item_dorian",
        "expected_icon": "icon_item_dorian",
        "description": "ItemWithBoost - Dorian, Philos of Philhellenes"
    }
]

print("Testing canonical_name property\n" + "="*80)

for test_case in test_cases:
    guid = test_case["guid"]
    expected_asset = test_case["expected_asset"]
    expected_icon = test_case["expected_icon"]
    description = test_case["description"]

    print(f"\nTest: {description}")
    print(f"GUID: {guid}")

    # Get asset
    asset = assets[guid]

    # Test asset canonical_name
    actual_asset = asset.canonical_name
    print(f"  Asset canonical_name: {actual_asset}")
    print(f"  Expected:             {expected_asset}")
    print(f"  Match: {'PASS' if actual_asset == expected_asset else 'FAIL'}")

    # Test icon canonical_name
    icon = asset.icon
    if icon:
        actual_icon = icon.canonical_name
        print(f"  Icon canonical_name:  {actual_icon}")
        print(f"  Expected:             {expected_icon}")
        print(f"  Match: {'PASS' if actual_icon == expected_icon else 'FAIL'}")
    else:
        print("  Icon: Not found")

    # Show details
    print(f"  Template: {asset.template.name}")
    if asset.text and "english" in asset.text.values:
        print(f"  English name: {asset.text.values['english']}")
    else:
        print(f"  Internal name: {asset.name}")

print("\n" + "="*80)
print("Test complete!")
