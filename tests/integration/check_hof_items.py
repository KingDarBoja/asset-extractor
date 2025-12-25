"""Check the Hall of Fame items to see what identifies them."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Hall of Fame item GUIDs from the manual CSV
hof_item_guids = [42625, 42049, 42050, 91415, 91417, 91419, 91421]

print("=" * 80)
print("Hall of Fame Items")
print("=" * 80)

for guid in hof_item_guids:
    item = assets[guid]
    print(f"\n{item.name} ({guid}):")
    print(f"  Template: {item.template.name}")
    print(f"  Rarity: {item.Item.Rarity()}")

    # Check for tech unlocks or special properties
    # Look for references
    if hasattr(item, '_referenced_by') and item._referenced_by:
        print(f"  Referenced by {len(item._referenced_by)} assets:")
        for ref_guid in list(item._referenced_by)[:10]:
            ref = assets[ref_guid]
            print(f"    - {ref.name} ({ref_guid}) [{ref.template.name}]")

print("\n" + "=" * 80)
print("Searching for Hall of Fame related assets...")
print("=" * 80)

# Search for Techs that might unlock these items
tech_template = assets.templates.get("Tech")
if tech_template:
    for tech in tech_template.assets:
        # Check if this tech rewards any of our Hall of Fame items
        try:
            rewards = tech.find("Tech.Rewards.Items")
            if rewards:
                for item_entry in rewards:
                    item_asset = item_entry.ItemAsset()
                    if item_asset and item_asset.guid in hof_item_guids:
                        print(f"\nFound Tech: {tech.name} ({tech.guid})")
                        tech_name_text = tech.find("Tech.TechName")()
                        if tech_name_text and hasattr(tech_name_text, 'values'):
                            print(f"  Tech Name: {tech_name_text.values.get('english', 'N/A')}")
                        print(f"  Rewards item: {item_asset.name} ({item_asset.guid})")

                        # Print full tech info
                        tech.print_tree()
                        break
        except:
            pass

print("\nDone!")
