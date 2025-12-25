"""Find items that are referenced via ItemGainedWhenDefeated."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Check all items to see if they're referenced via ItemGainedWhenDefeated
item_templates = ["Item", "ItemWithBoost"]
subjugated_items = []

for template_name in item_templates:
    template = assets.templates.get(template_name)
    if not template:
        continue

    for item in template.assets:
        # Check if this item is referenced via ItemGainedWhenDefeated
        if hasattr(item, 'referenced_by'):
            for ref_guid, weighted_ref in item.referenced_by.items():
                if "ItemGainedWhenDefeated" in weighted_ref.path:
                    source = weighted_ref.source
                    print(f"\nItem: {item.name} ({item.guid})")
                    if item.text:
                        print(f"  Localized: {item.text.values.get('english', 'N/A')}")
                    print(f"  Referenced by: {source.name} ({ref_guid})")
                    print(f"  Template: {source.template.name}")
                    print(f"  Path: {weighted_ref.path}")
                    subjugated_items.append(item.guid)
                    break

print(f"\n\nTotal subjugated items: {len(subjugated_items)}")
print(f"GUIDs: {subjugated_items}")
