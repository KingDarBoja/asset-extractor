"""Test script to investigate MovementUpgrade buff_ui issue."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Test assets that show the issue
test_guids = [121728, 82163]

print("=" * 80)
print("Testing MovementUpgrade attributes buff_ui")
print("=" * 80)

for guid in test_guids:
    asset = assets.get(guid)
    if not asset:
        print(f"\nAsset {guid} not found")
        continue

    print(f"\n\nAsset {guid}: {asset.name}")
    print("-" * 80)

    # Check if this is a ShipBuff
    if hasattr(asset, "template"):
        print(f"Template: {asset.template.name}")

    # Get MovementUpgrade property
    movement_upgrade = asset.find("MovementUpgrade")
    if not movement_upgrade:
        print("No MovementUpgrade found")
        continue

    # Test each attribute
    test_attrs = [
        "BuffReduceDamageImpactUpgrade",
        "BuffReduceNegativeWindImpactUpgrade"
    ]

    for attr_name in test_attrs:
        attr = movement_upgrade.get(attr_name)
        if not attr:
            continue

        print(f"\n{attr_name}:")
        print(f"  Value: {attr()}")
        print(f"  Type: {type(attr).__name__}")

        if hasattr(attr, "percental"):
            print(f"  Percental: {attr.percental}")

        # Get buff_ui
        buff_ui = attr.buff_ui
        print(f"  buff_ui: {buff_ui}")

        if buff_ui:
            print(f"    icon: {buff_ui.icon}")
            print(f"    text: {buff_ui.text}")
            print(f"    value: {buff_ui.value}")

            # Check if text is a Text object
            if buff_ui.text and hasattr(buff_ui.text, "values"):
                print(f"    text.id: {buff_ui.text.id}")
                print(f"    text (english): {buff_ui.text.values.get('english', 'N/A')}")

        # Try to manually get buff type name
        ui_cache = assets.properties.ui_text_cache
        buff_type = ui_cache.get_buff_type_name("MovementUpgrade", attr_name)
        print(f"  Buff type: {buff_type}")

        # Check if buff type is in buff_text_structs
        if buff_type and buff_type in ui_cache.buff_text_structs:
            print(f"  Buff text struct found: YES")
            buff_info = ui_cache.buff_text_structs[buff_type]
            print(f"  Variants: {buff_info.get('variants', [])}")

            # Print the struct tree
            buff_struct = buff_info["struct"]
            print(f"\n  Struct tree:")
            if hasattr(buff_struct, "print_tree"):
                buff_struct.print_tree(indent="    ")

            # Check if Text field exists
            text_attr = buff_struct.find("Text")
            print(f"\n  Text field exists: {text_attr is not None}")
            if text_attr:
                text_obj = text_attr()
                print(f"  Text: {text_obj}")
                if hasattr(text_obj, "values"):
                    print(f"  English: {text_obj.values.get('english', 'N/A')}")
        else:
            print(f"  Buff text struct found: NO")

print("\n" + "=" * 80)
print("Checking buff type name mapping")
print("=" * 80)

ui_cache = assets.properties.ui_text_cache

# Check what buff types are available for these attributes
test_mappings = [
    ("MovementUpgrade", "BuffReduceDamageImpactUpgrade"),
    ("MovementUpgrade", "BuffReduceNegativeWindImpactUpgrade"),
]

for property_name, attr_name in test_mappings:
    result = ui_cache.get_buff_type_name(property_name, attr_name)
    print(f"\n{property_name}.{attr_name}")
    print(f"  Mapped to: {result}")

    if result:
        # Check if it's in buff_text_structs
        if result in ui_cache.buff_text_structs:
            print(f"  Found in buff_text_structs: YES")
        else:
            print(f"  Found in buff_text_structs: NO")

        # Try similar names
        print(f"\n  Searching for similar buff types:")
        for buff_name in ui_cache.buff_text_structs.keys():
            if "Damage" in buff_name or "Wind" in buff_name or "Impact" in buff_name:
                print(f"    - {buff_name}")

print("\n" + "=" * 80)
print("All buff types with 'Speed' or 'Reduce' in name:")
print("=" * 80)
for buff_name in sorted(ui_cache.buff_text_structs.keys()):
    if "Speed" in buff_name or "Reduce" in buff_name:
        print(f"  {buff_name}")
