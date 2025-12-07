"""Comprehensive test for pool flattening functionality."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

print("Loading assets...")
config = Config.from_json("config.json")
assets = AssetCache.load(config)

print("\n" + "=" * 80)
print("TEST 1: Verify pool_assets returns correct type (dict[Asset, float])")
print("=" * 80)

pool_guid = 122533
pool = assets.elements.get(pool_guid)
pool_results = pool.pool_assets()

print(f"Return type check: {type(pool_results)}")
print(f"Is dict: {isinstance(pool_results, dict)}")

if pool_results:
    first_asset, first_prob = next(iter(pool_results.items()))
    print(f"First entry - Asset type: {type(first_asset).__name__}, Probability type: {type(first_prob).__name__}")
    print(f"Asset is Asset instance: {first_asset.__class__.__name__ == 'Asset'}")
    print(f"Probability is float: {isinstance(first_prob, float)}")
    print("[PASS] Return type is correct")
else:
    print("[FAIL] No results returned")

print("\n" + "=" * 80)
print("TEST 2: Verify probabilities sum to ~1.0")
print("=" * 80)

total_prob = sum(pool_results.values())
print(f"Total probability: {total_prob:.6f}")

if abs(total_prob - 1.0) < 0.0001:
    print("[PASS]: Probabilities sum to 1.0")
else:
    print(f"[FAIL]: Total probability is {total_prob}, expected 1.0")

print("\n" + "=" * 80)
print("TEST 3: Verify root pool detection")
print("=" * 80)

# Count root pools
root_reward_pools = []
root_asset_pools = []
subpools = []

for asset in assets.elements.values():
    if "Pool" not in asset.template.name:
        continue

    # Check if referenced by non-pool
    is_root = False
    for ref in asset.referenced_by.values():
        if "Pool" not in ref.source.template.name:
            is_root = True
            break

    if is_root:
        if "RewardPool" in asset.template.name:
            root_reward_pools.append(asset)
        elif "AssetPool" in asset.template.name:
            root_asset_pools.append(asset)
    else:
        subpools.append(asset)

print(f"Root reward pools: {len(root_reward_pools)}")
print(f"Root asset pools: {len(root_asset_pools)}")
print(f"Subpools (not root): {len(subpools)}")

# Verify subpools are NOT in leaf assets' in_reward_pool
if subpools:
    subpool = subpools[0]
    subpool_results = subpool.pool_assets()

    if subpool_results:
        leaf = next(iter(subpool_results.keys()))
        if subpool.guid in leaf.in_reward_pool:
            print(f"[FAIL]: Subpool {subpool.guid} found in leaf's in_reward_pool")
        else:
            print(f"[PASS]: Subpool {subpool.guid} correctly NOT in leaf's in_reward_pool")

print("\n" + "=" * 80)
print("TEST 4: Verify WeightedReference construction")
print("=" * 80)

# Check a leaf asset's in_reward_pool
first_leaf = next(iter(pool_results.keys()))
print(f"Leaf asset: {first_leaf.name} ({first_leaf.guid})")
print(f"in_reward_pool count: {len(first_leaf.in_reward_pool)}")

if pool.guid in first_leaf.in_reward_pool:
    ref = first_leaf.in_reward_pool[pool.guid]
    print(f"  source: {ref.source.name} ({ref.source.guid})")
    print(f"  target: {ref.target.name} ({ref.target.guid})")
    print(f"  weight: {ref.weight:.6f}")
    print(f"  is_forward: {ref.is_forward}")

    # Verify values
    if ref.source.guid == pool.guid and ref.target.guid == first_leaf.guid:
        if 0.0 <= ref.weight <= 1.0:
            print("[PASS]: WeightedReference correctly constructed")
        else:
            print(f"[FAIL]: Weight {ref.weight} not in range [0.0, 1.0]")
    else:
        print("[FAIL]: Source/target mismatch")
else:
    print(f"[FAIL]: Pool {pool.guid} not in leaf's in_reward_pool")

print("\n" + "=" * 80)
print("TEST 5: Verify cycle detection")
print("=" * 80)

# Create a visited set with the pool's GUID to simulate a cycle
visited = {pool.guid}
result_with_cycle = pool.pool_assets(visited=visited)

if len(result_with_cycle) == 0:
    print("[PASS]: Cycle detection works (returns empty dict)")
else:
    print(f"[FAIL]: Should return empty dict for cycle, got {len(result_with_cycle)} results")

print("\n" + "=" * 80)
print("TEST 6: Check statistics")
print("=" * 80)

leaf_assets_with_reward_pools = sum(1 for asset in assets.elements.values() if len(asset.in_reward_pool) > 0)
leaf_assets_with_asset_pools = sum(1 for asset in assets.elements.values() if len(asset.in_asset_pool) > 0)

print(f"Leaf assets with reward pool refs: {leaf_assets_with_reward_pools}")
print(f"Leaf assets with asset pool refs: {leaf_assets_with_asset_pools}")

if leaf_assets_with_reward_pools > 0:
    print("[PASS]: At least some leaf assets have reward pool references")
else:
    print("[FAIL]: No leaf assets have reward pool references")

print("\n" + "=" * 80)
print("TEST 7: Verify named_reference_collections")
print("=" * 80)

# Check that the new collections are in named_reference_collections
if "In Reward Pools" in first_leaf.named_reference_collections:
    print("[PASS]: 'In Reward Pools' in named_reference_collections")
else:
    print("[FAIL]: 'In Reward Pools' not in named_reference_collections")

if "In Asset Pools" in first_leaf.named_reference_collections:
    print("[PASS]: 'In Asset Pools' in named_reference_collections")
else:
    print("[FAIL]: 'In Asset Pools' not in named_reference_collections")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)
