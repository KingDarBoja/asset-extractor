"""Test script to verify all buff_ui fixes."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

print("=" * 80)
print("Testing all buff_ui fixes")
print("=" * 80)

# Test cases: (guid, property_name, attr_name, expected_text_contains)
test_cases = [
    # RecruitmentUpgrade - should now use RecruitmentText variant
    (68184, "RecruitmentUpgrade", "ConstructionSpeedInPercent", "Troop Recruitment Speed"),
    (118691, "RecruitmentUpgrade", "RecruitmentCostInPercent", "Troop Recruitment Cost"),
    (68794, "RecruitmentUpgrade", "RecruitmentSpeedInPercent", "Troop Recruitment Speed"),

    # MovementUpgrade - should now map to correct buff types
    (121728, "MovementUpgrade", "BuffReduceDamageImpactUpgrade", "Damage Slowdown"),
    (82163, "MovementUpgrade", "BuffReduceNegativeWindImpactUpgrade", "Unfavourable Wind Impact"),
]

all_passed = True

for guid, property_name, attr_name, expected_text in test_cases:
    asset = assets.get(guid)
    if not asset:
        print(f"\n[ERROR] Asset {guid} not found")
        all_passed = False
        continue

    print(f"\n{'=' * 80}")
    print(f"Asset {guid}: {asset.name}")
    print(f"Testing: {property_name}.{attr_name}")
    print(f"Expected text contains: '{expected_text}'")
    print('-' * 80)

    # Get the property
    prop = asset.find(property_name)
    if not prop:
        print(f"[ERROR] Property {property_name} not found")
        all_passed = False
        continue

    # Get the attribute
    attr = prop.get(attr_name)
    if not attr:
        print(f"[ERROR] Attribute {attr_name} not found")
        all_passed = False
        continue

    # Check if value is non-zero
    value = attr()
    if value == 0 or value == 0.0:
        print(f"[WARNING] Value is 0, skipping (no buff_ui expected)")
        continue

    print(f"Value: {value}")

    # Get buff_ui
    buff_ui = attr.buff_ui
    if not buff_ui:
        print(f"[ERROR] buff_ui is None")
        all_passed = False
        continue

    print(f"\nbuff_ui: {buff_ui}")
    print(f"  icon: {buff_ui.icon.value.stem if buff_ui.icon and buff_ui.icon.value else 'None'}")
    print(f"  value: {buff_ui.value}")

    # Check text
    if buff_ui.text:
        if hasattr(buff_ui.text, "values"):
            english_text = buff_ui.text.values.get("english", "N/A")
        elif isinstance(buff_ui.text, str):
            english_text = buff_ui.text
        else:
            english_text = str(buff_ui.text)

        print(f"  text: {english_text}")

        # Check if expected text is in the actual text
        if expected_text.lower() in english_text.lower():
            print(f"[PASS] Text contains expected value")
        else:
            print(f"[FAIL] Expected '{expected_text}' not found in '{english_text}'")
            all_passed = False
    else:
        print(f"  text: None")
        print(f"[FAIL] Text is None (expected '{expected_text}')")
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("[SUCCESS] All tests PASSED!")
else:
    print("[ERROR] Some tests FAILED")
print("=" * 80)
