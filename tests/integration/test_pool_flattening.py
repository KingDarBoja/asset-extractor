"""Test pool flattening functionality."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
print("Loading assets...")
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Test pool 122533 (Festival Happiness) from the HTML example
pool_guid = 122533
print(f"\nTesting pool {pool_guid}...")

pool = assets.elements.get(pool_guid)
if pool is None:
    print(f"Pool {pool_guid} not found!")
else:
    print(f"Pool: {pool.name} ({pool.guid})")
    print(f"Template: {pool.template.name}")

    # Test pool_assets method
    print("\nCalling pool.pool_assets()...")
    pool_results = pool.pool_assets()

    print(f"Found {len(pool_results)} leaf assets:")
    total_prob = 0.0
    for asset, probability in pool_results.items():
        print(f"  - {asset.name} ({asset.guid}): {probability:.4f} ({probability * 100:.2f}%)")
        total_prob += probability

    print(f"\nTotal probability: {total_prob:.4f} (should be ~1.0)")

    # Check if this is a root pool
    is_root_pool = False
    for ref in pool.referenced_by.values():
        if "Pool" not in ref.source.template.name:
            is_root_pool = True
            print(f"\nRoot pool referenced by: {ref.source.name} ({ref.source.template.name})")
            break

    if is_root_pool:
        print("\nThis is a root pool - leaf assets should have in_reward_pool references")

        # Check one of the leaf assets
        if pool_results:
            first_leaf = next(iter(pool_results.keys()))
            print(f"\nChecking leaf asset: {first_leaf.name} ({first_leaf.guid})")
            print(f"in_reward_pool count: {len(first_leaf.in_reward_pool)}")

            if pool.guid in first_leaf.in_reward_pool:
                ref = first_leaf.in_reward_pool[pool.guid]
                print(f"  - Found reference from pool {ref.source.name} with weight {ref.weight:.4f}")
            else:
                print(f"  - WARNING: No reference from pool {pool.guid} found!")
    else:
        print("\nThis is a subpool (only referenced by other pools)")

print("\n" + "=" * 60)
print("Test completed!")
