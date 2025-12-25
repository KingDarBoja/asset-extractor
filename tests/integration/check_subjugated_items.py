"""Check which items are obtained by defeating rivals."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Get all rival participants
rival_template = assets.templates.get("Participant 2ndParty (Rival)")
rivals = list(rival_template.assets)

print(f"Total rivals: {len(rivals)}\n")
print("Checking for ItemGainedWhenDefeated...\n")

subjugated_items = []
for rival in rivals:
    item_ref = rival.find("Participant.ItemGainedWhenDefeated")
    if item_ref and item_ref():
        item = item_ref()
        print(f"Rival: {rival.name} ({rival.guid})")
        print(f"  Item: {item.name} ({item.guid})")
        if item.text:
            print(f"  Localized: {item.text.values.get('english', 'N/A')}")
        subjugated_items.append(item.guid)
        print()

print(f"\nTotal items obtained by defeating rivals: {len(subjugated_items)}")
print(f"GUIDs: {subjugated_items}")
