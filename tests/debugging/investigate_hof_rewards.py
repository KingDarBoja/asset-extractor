"""Investigate Hall of Fame reward pools and items."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Look for the "HallOfFame Tech Pool" mentioned in the achievement
print("=" * 80)
print("Searching for Hall of Fame Pools...")
print("=" * 80)

for template_name in ["RewardPool", "AssetPool", "RegionRewardPool"]:
    template = assets.templates.get(template_name)
    if template:
        for pool in template.assets:
            if "HallOfFame" in pool.name or "Hof" in pool.name:
                print(f"\nFound: {pool.name} ({pool.guid}) in template {template_name}")
                pool.print_tree()

# Let's check the HallOfFameItem assets more carefully
# They might have reward pools attached
print("\n" + "=" * 80)
print("Checking HallOfFameItem assets for rewards...")
print("=" * 80)

hof_items = list(assets.templates['HallOfFameItem'].assets)

# Look at the actual cards (not just pictures)
for item in hof_items:
    if "Card" in item.name and "Pic" not in item.name:
        print(f"\n{item.name} ({item.guid}):")

        # Print full tree to see what properties exist
        item.print_tree()
        print("\n" + "-" * 80)

print("\nDone!")
