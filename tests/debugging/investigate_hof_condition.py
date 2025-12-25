"""Investigate ConditionOwnedInHallOfFame and how items use it."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Look at the condition template
print("=" * 80)
print("ConditionOwnedInHallOfFame Template")
print("=" * 80)

condition_template = assets.templates.get("ConditionOwnedInHallOfFame")
if condition_template:
    for cond_asset in condition_template.assets:
        print(f"Asset: {cond_asset.guid} - {cond_asset.name}")
        cond_asset.print_tree()

# Now search for items that use this condition
print("\n" + "=" * 80)
print("Searching for items with Hall of Fame unlock conditions...")
print("=" * 80)

item_template = assets.templates.get("Item")
items_with_hof = []

if item_template:
    for item in item_template.assets:
        try:
            # Look for unlock conditions
            unlock_conditions = item.find("Locked.UnlockConditions")
            if unlock_conditions:
                # Check if any condition is ConditionOwnedInHallOfFame
                for condition_entry in unlock_conditions:
                    try:
                        condition_asset = condition_entry.Condition()
                        if condition_asset and "HallOfFame" in condition_asset.template.name:
                            items_with_hof.append(item)
                            print(f"\nFound: {item.name} ({item.guid})")
                            print(f"  Condition: {condition_asset.name} ({condition_asset.guid})")

                            # Print the condition details
                            if hasattr(condition_asset, 'ConditionOwnedInHallOfFame'):
                                print("  Condition details:")
                                condition_asset.ConditionOwnedInHallOfFame.print_tree()
                            break
                    except:
                        pass
        except:
            pass

print(f"\n\nTotal items with Hall of Fame unlock: {len(items_with_hof)}")

# Let's also check if there are any ItemWithBoost items
print("\n" + "=" * 80)
print("Checking ItemWithBoost for Hall of Fame conditions...")
print("=" * 80)

boost_template = assets.templates.get("ItemWithBoost")
if boost_template:
    for item in boost_template.assets:
        try:
            unlock_conditions = item.find("Locked.UnlockConditions")
            if unlock_conditions:
                for condition_entry in unlock_conditions:
                    try:
                        condition_asset = condition_entry.Condition()
                        if condition_asset and "HallOfFame" in condition_asset.template.name:
                            print(f"\nFound (ItemWithBoost): {item.name} ({item.guid})")
                            print(f"  Condition: {condition_asset.name} ({condition_asset.guid})")

                            if hasattr(condition_asset, 'ConditionOwnedInHallOfFame'):
                                print("  Condition details:")
                                condition_asset.ConditionOwnedInHallOfFame.print_tree()
                            break
                    except:
                        pass
        except:
            pass

print("\nDone!")
