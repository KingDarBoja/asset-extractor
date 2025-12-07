"""Test HTML probability display for pool references."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
print("Loading assets...")
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Find an item that's in reward pools
print("\nFinding an item with reward pool references...")
test_item = None
for asset in list(assets.elements.values())[:1000]:  # Check first 1000 assets
    if len(asset.in_reward_pool) > 0:
        test_item = asset
        break

if test_item:
    print(f"\nFound test item: {test_item.name} ({test_item.guid})")
    print(f"In {len(test_item.in_reward_pool)} reward pools:")

    for pool_guid, ref in list(test_item.in_reward_pool.items())[:5]:  # Show first 5
        pool = ref.source
        probability = ref.weight
        print(f"  - {pool.name}: {probability:.4f} ({probability * 100:.2f}%)")

    print("\n✓ Probability values are available in WeightedReference.weight")
    print("✓ HTML template should display these values in the 'Probability' column")
else:
    print("\n✗ No items found with reward pool references")
