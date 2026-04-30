# Asset Pools

Two pool types group assets:

- **RewardPool** — weighted item containers (random selection)
- **AssetPool** — generic asset grouping

## RewardPool

```python
for entry in pool.RewardPool.ItemsPool:
    link = entry.ItemLink()      # Item or nested RewardPool
    weight = entry.Weight()
    min_amt, max_amt = entry.MinAmount(), entry.MaxAmount()
```

Pool-level flags: `GenerateUniqueRewards()`, `IgnoreUnlocks()`.

## Recursive flattening

Pools nest. Walk recursively, returning leaf GUIDs:

```python
def flatten_pool(pool):
    if pool is None: return []
    if "AssetPool" not in pool.template.name: return [pool.guid]
    return [g for entry in pool.AssetPool.AssetList
              if entry.Asset() for g in flatten_pool(entry.Asset())]
```

## Reverse index (item → pools)

Build once, reuse to locate sources:

```python
def build_reward_pool_index(assets):
    index = {}
    for tpl in ("RewardPool", "RegionRewardPool"):
        if tpl not in assets.templates: continue
        for pool in assets.templates[tpl].assets:
            for entry in (pool.RewardPool.ItemsPool or []):
                link = entry.ItemLink()
                if link:
                    index.setdefault(link.guid, set()).add(pool.guid)
    return index
```

## Resolving pool chains

An item may sit inside pool A inside pool B. Recurse with a `visited` set to avoid cycles, expanding `item_to_pools[guid]` until fixpoint.
