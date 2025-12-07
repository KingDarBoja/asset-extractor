"""Test script to investigate RecruitmentUpgrade buff_ui issue."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Test assets that show the issue
test_guids = [68184, 118691, 68794]

print("=" * 80)
print("Testing RecruitmentUpgrade attributes buff_ui")
print("=" * 80)

for guid in test_guids:
    asset = assets.get(guid)
    if not asset:
        print(f"\nAsset {guid} not found")
        continue

    print(f"\n\nAsset {guid}: {asset.name}")
    print("-" * 80)

    # Check if this is a BuildingBuff
    if hasattr(asset, "template"):
        print(f"Template: {asset.template.name}")

    # Get RecruitmentUpgrade property
    recruitment_upgrade = asset.find("RecruitmentUpgrade")
    if not recruitment_upgrade:
        print("No RecruitmentUpgrade found")
        continue

    # Test each attribute
    test_attrs = [
        "ConstructionSpeedInPercent",
        "RecruitmentCostInPercent",
        "RecruitmentSpeedInPercent"
    ]

    for attr_name in test_attrs:
        attr = recruitment_upgrade.get(attr_name)
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
        buff_type = ui_cache.get_buff_type_name("RecruitmentUpgrade", attr_name)
        print(f"  Buff type: {buff_type}")

        # Check if buff type is in buff_text_structs
        if buff_type and buff_type in ui_cache.buff_text_structs:
            print(f"  Buff text struct found: YES")
            buff_info = ui_cache.buff_text_structs[buff_type]
            print(f"  Variants: {buff_info.get('variants', [])}")
        else:
            print(f"  Buff text struct found: NO")

        # Check if buff type is in mappings
        mapping = ui_cache.mappings.get(("RecruitmentUpgrade", attr_name))
        if mapping:
            print(f"  Mapping found: YES")
            print(f"    text_id: {mapping.text_id}")
            print(f"    text: {mapping.text}")
            print(f"    icon: {mapping.icon}")
        else:
            print(f"  Mapping found: NO")

print("\n" + "=" * 80)
print("Checking special mappings in uitext.py")
print("=" * 80)

ui_cache = assets.properties.ui_text_cache

# Check special mappings
special_mappings = {
    ("Recruitment", "RecruitmentCost"): "BuffConstructionCost",
    ("Recruitment", "RecruitmentSpeed"): "BuffConstructionSpeed",
}

for key, expected_buff_type in special_mappings.items():
    property_base, attr_base = key
    result = ui_cache.get_buff_type_name(f"{property_base}Upgrade", f"{attr_base}InPercent")
    print(f"\n{property_base}Upgrade.{attr_base}InPercent -> {result}")
    print(f"  Expected: {expected_buff_type}")
    print(f"  Match: {result == expected_buff_type}")

    # Check if result is in buff_text_structs
    if result and result in ui_cache.buff_text_structs:
        print(f"  Found in buff_text_structs: YES")
    else:
        print(f"  Found in buff_text_structs: NO")

print("\n" + "=" * 80)
print("Checking ConstructionSpeedInPercent mapping")
print("=" * 80)

# The problematic one
result = ui_cache.get_buff_type_name("RecruitmentUpgrade", "ConstructionSpeedInPercent")
print(f"RecruitmentUpgrade.ConstructionSpeedInPercent -> {result}")

# Try without "InPercent" suffix
result2 = ui_cache.get_buff_type_name("RecruitmentUpgrade", "ConstructionSpeed")
print(f"RecruitmentUpgrade.ConstructionSpeed -> {result2}")

# Check if BuffConstructionSpeed exists
if "BuffConstructionSpeed" in ui_cache.buff_text_structs:
    print("BuffConstructionSpeed exists in buff_text_structs")
    buff_info = ui_cache.buff_text_structs["BuffConstructionSpeed"]
    buff_struct = buff_info["struct"]

    # Try to get text
    text_attr = buff_struct.find("Text")
    if text_attr:
        text_obj = text_attr()
        print(f"  Text: {text_obj}")
        if hasattr(text_obj, "values"):
            print(f"  Text (english): {text_obj.values.get('english', 'N/A')}")

    # Try to get icon
    icon_attr = buff_struct.find("Icon")
    if icon_attr:
        print(f"  Icon attr: {icon_attr}")
