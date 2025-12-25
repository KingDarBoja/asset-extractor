"""Investigate Hall of Fame item structure."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Get HallOfFameItem assets
hof_items = list(assets.templates['HallOfFameItem'].assets)
print(f"Found {len(hof_items)} HallOfFameItem assets\n")

# Look at one of the actual cards (not just pictures)
for item in hof_items:
    if "Card" in item.name and "Pic" not in item.name:
        print(f"=" * 80)
        print(f"Hall of Fame Card: {item.guid} - {item.name}")
        print(f"=" * 80)
        item.print_tree()
        print("\n")
        break

# Now let's see if there's a HallOfFame template or similar
print("\n" + "=" * 80)
print("Searching for Hall of Fame related templates...")
print("=" * 80)

for template_name in assets.templates.elements.keys():
    if "Hall" in template_name or "Fame" in template_name or "Hof" in template_name.lower():
        print(f"\nFound template: {template_name}")
        template = assets.templates[template_name]
        print(f"  Number of assets: {len(list(template.assets))}")

# Check if items reference HallOfFameItem
print("\n" + "=" * 80)
print("Checking if regular Items reference Hall of Fame...")
print("=" * 80)

item_template = assets.templates.get("Item")
if item_template:
    count = 0
    for item in list(item_template.assets)[:50]:  # Check first 50 items
        # Search for any Hall of Fame references
        item_str = str(item.name)
        if "Hall" in item_str or "Fame" in item_str:
            print(f"Found item with Hall/Fame in name: {item.name} ({item.guid})")
            count += 1

    if count == 0:
        print("No items with 'Hall' or 'Fame' in name found (checked first 50)")

print("\nDone!")
