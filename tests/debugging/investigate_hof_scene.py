"""Investigate HallOfFameScene and find what references HallOfFameItem."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Look at the HallOfFameScene
print("=" * 80)
print("HallOfFameScene Template")
print("=" * 80)

scene_template = assets.templates.get("HallOfFameScene")
if scene_template:
    for scene in scene_template.assets:
        print(f"\n{scene.name} ({scene.guid}):")
        scene.print_tree()

# Now search for any assets that reference HallOfFameItem GUIDs
print("\n" + "=" * 80)
print("Searching for assets that reference HallOfFameItem...")
print("=" * 80)

# Get the first few HallOfFameItem GUIDs
hof_items = list(assets.templates['HallOfFameItem'].assets)
test_guids = [item.guid for item in hof_items[:5]]

print(f"Testing with HallOfFameItem GUIDs: {test_guids}")

# Get one of the HallOfFame picture items
for item in hof_items:
    if "Pic" in item.name:
        print(f"\nChecking {item.name} ({item.guid}):")
        item.print_tree()

        # Check what references this item
        if hasattr(item, '_referenced_by') and item._referenced_by:
            print(f"\n  Referenced by {len(item._referenced_by)} assets:")
            for ref in list(item._referenced_by)[:5]:
                print(f"    - {assets[ref].name} ({ref}) [{assets[ref].template.name}]")
        break

print("\nDone!")
