"""Debug MovementUpgrade buff_ui issue."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)
ui_cache = assets.properties.ui_text_cache

# Test the buff type name mapping
print("=" * 80)
print("Testing buff type name mapping")
print("=" * 80)

test_cases = [
    ("MovementUpgrade", "BuffReduceDamageImpactUpgrade"),
    ("MovementUpgrade", "BuffReduceNegativeWindImpactUpgrade"),
]

for property_name, attr_name in test_cases:
    print(f"\n{property_name}.{attr_name}")

    # Test the mapping
    buff_type = ui_cache.get_buff_type_name(property_name, attr_name)
    print(f"  Buff type: {buff_type}")

    if buff_type:
        if buff_type in ui_cache.buff_text_structs:
            print(f"  Found in buff_text_structs: YES")
        else:
            print(f"  Found in buff_text_structs: NO")

# Now test with the actual asset
print("\n" + "=" * 80)
print("Testing with actual asset")
print("=" * 80)

asset = assets.get(121728)
if asset:
    print(f"\nAsset {asset.guid}: {asset.name}")

    movement_upgrade = asset.find("MovementUpgrade")
    if movement_upgrade:
        attr = movement_upgrade.get("BuffReduceDamageImpactUpgrade")
        if attr:
            print(f"\nBuffReduceDamageImpactUpgrade:")
            print(f"  Type: {type(attr).__name__}")
            print(f"  Value: {attr()}")
            print(f"  Has buff_ui property: {hasattr(attr, 'buff_ui')}")

            if hasattr(attr, 'percental'):
                print(f"  Percental: {attr.percental}")

            # Try to manually call create_buff_ui
            if hasattr(attr, 'parent'):
                print(f"  Parent name: {attr.parent.name}")
                print(f"  Attribute name: {attr.name}")

                # Try to get buff_ui
                try:
                    buff_ui = ui_cache.create_buff_ui(
                        property_name="MovementUpgrade",
                        attr_name="BuffReduceDamageImpactUpgrade",
                        value=attr(),
                        percental=attr.percental
                    )
                    print(f"\n  Manual create_buff_ui result: {buff_ui}")
                    if buff_ui:
                        print(f"    icon: {buff_ui.icon}")
                        print(f"    text: {buff_ui.text}")
                        print(f"    value: {buff_ui.value}")
                except Exception as e:
                    print(f"  Error calling create_buff_ui: {e}")
                    import traceback
                    traceback.print_exc()
