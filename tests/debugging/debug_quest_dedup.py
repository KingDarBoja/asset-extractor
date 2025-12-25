"""Debug script to understand quest deduplication for item 71438."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache
from assetextractor.conversion.statistics.quest_tracking import QuestTracker

print("Loading assets...")
config = Config.from_json("config.json")
assets = AssetCache.load(config)

print("Creating quest tracker...")
quest_tracker = QuestTracker(assets, assets.texts)

# Get item 71438
item_71438 = assets[71438]

print("\n=== Checking all Decision references for item 71438 ===")
decision_count = 0
quest_guids_found = []

if hasattr(item_71438, 'referenced_by'):
    for ref_guid, weighted_ref in item_71438.referenced_by.items():
        source = weighted_ref.source

        # Check for decisions with ActionAddGoodsToItemContainer
        if source.template.name == "Decision" and "ActionAddGoodsToItemContainer" in weighted_ref.path:
            decision_count += 1
            print(f"\nDecision {decision_count}: {source.guid} - {source.name}")
            print(f"  Path: {weighted_ref.path}")

            # Find the quest
            quest = quest_tracker.find_quest(source)
            if quest:
                print(f"  Quest found: {quest.guid} - {quest.name}")
                quest_guids_found.append(quest.guid)
            else:
                print(f"  No quest found")

print(f"\n=== Summary ===")
print(f"Total decisions with ActionAddGoodsToItemContainer: {decision_count}")
print(f"Quest GUIDs found: {quest_guids_found}")
print(f"Unique quest GUIDs: {set(quest_guids_found)}")
print(f"Number of times quest 99231 appears: {quest_guids_found.count(99231)}")
