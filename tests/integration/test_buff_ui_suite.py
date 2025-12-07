"""Comprehensive test suite for buff_ui text mapping.

This test suite validates that all buff attributes correctly map to their
localized text and icons, including special cases like:
- RecruitmentUpgrade attributes (using variant text)
- MovementUpgrade attributes (non-standard naming)
- BuffConstructionSpeed/BuffConstructionCost (context-specific variants)
"""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


def test_recruitment_upgrade_variant_text():
    """Test that RecruitmentUpgrade attributes use RecruitmentText variant."""
    print("\n" + "=" * 80)
    print("Test: RecruitmentUpgrade Variant Text")
    print("=" * 80)

    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    test_cases = [
        (68184, "ConstructionSpeedInPercent", "Troop Recruitment Speed"),
        (118691, "RecruitmentCostInPercent", "Troop Recruitment Cost"),
        (68794, "RecruitmentSpeedInPercent", "Troop Recruitment Speed"),
    ]

    passed = 0
    failed = 0

    for guid, attr_name, expected_text in test_cases:
        asset = assets.get(guid)
        if not asset:
            print(f"[FAIL] Asset {guid} not found")
            failed += 1
            continue

        prop = asset.find("RecruitmentUpgrade")
        if not prop:
            print(f"[FAIL] RecruitmentUpgrade not found in asset {guid}")
            failed += 1
            continue

        attr = prop.get(attr_name)
        if not attr or attr() == 0:
            print(f"[SKIP] {attr_name} is 0 or not found")
            continue

        buff_ui = attr.buff_ui
        if not buff_ui or not buff_ui.text:
            print(f"[FAIL] {guid}.RecruitmentUpgrade.{attr_name}: No text")
            failed += 1
            continue

        text_str = buff_ui.text.values.get("english") if hasattr(buff_ui.text, "values") else str(buff_ui.text)

        if expected_text.lower() in text_str.lower():
            print(f"[PASS] {guid}.{attr_name}: {text_str}")
            passed += 1
        else:
            print(f"[FAIL] {guid}.{attr_name}: Expected '{expected_text}', got '{text_str}'")
            failed += 1

    return passed, failed


def test_movement_upgrade_mapping():
    """Test that MovementUpgrade attributes map to correct buff types."""
    print("\n" + "=" * 80)
    print("Test: MovementUpgrade Buff Type Mapping")
    print("=" * 80)

    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    test_cases = [
        (121728, "BuffReduceDamageImpactUpgrade", "Damage Slowdown"),
        (82163, "BuffReduceNegativeWindImpactUpgrade", "Unfavourable Wind Impact"),
    ]

    passed = 0
    failed = 0

    for guid, attr_name, expected_text in test_cases:
        asset = assets.get(guid)
        if not asset:
            print(f"[FAIL] Asset {guid} not found")
            failed += 1
            continue

        prop = asset.find("MovementUpgrade")
        if not prop:
            print(f"[FAIL] MovementUpgrade not found in asset {guid}")
            failed += 1
            continue

        attr = prop.get(attr_name)
        if not attr or attr() == 0:
            print(f"[SKIP] {attr_name} is 0 or not found")
            continue

        buff_ui = attr.buff_ui
        if not buff_ui or not buff_ui.text:
            print(f"[FAIL] {guid}.MovementUpgrade.{attr_name}: No text")
            failed += 1
            continue

        text_str = buff_ui.text.values.get("english") if hasattr(buff_ui.text, "values") else str(buff_ui.text)

        if expected_text.lower() in text_str.lower():
            print(f"[PASS] {guid}.{attr_name}: {text_str}")
            passed += 1
        else:
            print(f"[FAIL] {guid}.{attr_name}: Expected '{expected_text}', got '{text_str}'")
            failed += 1

    return passed, failed


def test_buff_type_name_mapping():
    """Test that get_buff_type_name correctly maps property/attribute names."""
    print("\n" + "=" * 80)
    print("Test: Buff Type Name Mapping")
    print("=" * 80)

    config = Config.from_json("config.json")
    assets = AssetCache.load(config)
    ui_cache = assets.properties.ui_text_cache

    test_cases = [
        # (property_name, attr_name, expected_buff_type)
        ("RecruitmentUpgrade", "ConstructionSpeedInPercent", "BuffConstructionSpeed"),
        ("RecruitmentUpgrade", "RecruitmentCostInPercent", "BuffConstructionCost"),
        ("MovementUpgrade", "BuffReduceDamageImpactUpgrade", "BuffReduceSpeedImpactOfDamage"),
        ("MovementUpgrade", "BuffReduceNegativeWindImpactUpgrade", "BuffReduceNegativeSpeedImpactOfWind"),
        ("FactoryUpgrade", "ProductivityUpgrade", "BuffProductivity"),
        ("MovementUpgrade", "BaseSpeedUpgrade", "BuffSpeed"),
    ]

    passed = 0
    failed = 0

    for property_name, attr_name, expected_buff_type in test_cases:
        buff_type = ui_cache.get_buff_type_name(property_name, attr_name)

        if buff_type == expected_buff_type:
            print(f"[PASS] {property_name}.{attr_name} -> {buff_type}")
            passed += 1
        else:
            print(f"[FAIL] {property_name}.{attr_name}: Expected '{expected_buff_type}', got '{buff_type}'")
            failed += 1

    return passed, failed


def test_buff_struct_text_fields():
    """Test that buff structs have correct text fields."""
    print("\n" + "=" * 80)
    print("Test: Buff Struct Text Fields")
    print("=" * 80)

    config = Config.from_json("config.json")
    assets = AssetCache.load(config)
    ui_cache = assets.properties.ui_text_cache

    test_cases = [
        # (buff_type, expected_text_field, expected_english_text)
        ("BuffConstructionSpeed", "RecruitmentText", "Troop Recruitment Speed"),
        ("BuffConstructionSpeed", "ShipyardText", "Ship Construction Speed"),
        ("BuffConstructionCost", "RecruitmentText", "Troop Recruitment Cost"),
        ("BuffReduceSpeedImpactOfDamage", "Text", "Damage Slowdown"),
        ("BuffReduceNegativeSpeedImpactOfWind", "Text", "Unfavourable Wind Impact"),
    ]

    passed = 0
    failed = 0

    for buff_type, text_field, expected_text in test_cases:
        if buff_type not in ui_cache.buff_text_structs:
            print(f"[FAIL] {buff_type} not found in buff_text_structs")
            failed += 1
            continue

        buff_info = ui_cache.buff_text_structs[buff_type]
        buff_struct = buff_info["struct"]

        text_attr = buff_struct.find(text_field)
        if not text_attr:
            print(f"[FAIL] {buff_type}.{text_field} not found")
            failed += 1
            continue

        text_obj = text_attr()
        if not text_obj:
            print(f"[FAIL] {buff_type}.{text_field} returned None")
            failed += 1
            continue

        text_str = text_obj.values.get("english") if hasattr(text_obj, "values") else str(text_obj)

        if expected_text.lower() in text_str.lower():
            print(f"[PASS] {buff_type}.{text_field}: {text_str}")
            passed += 1
        else:
            print(f"[FAIL] {buff_type}.{text_field}: Expected '{expected_text}', got '{text_str}'")
            failed += 1

    return passed, failed


def test_create_buff_ui():
    """Test that create_buff_ui correctly creates BuffUI objects."""
    print("\n" + "=" * 80)
    print("Test: create_buff_ui Function")
    print("=" * 80)

    config = Config.from_json("config.json")
    assets = AssetCache.load(config)
    ui_cache = assets.properties.ui_text_cache

    test_cases = [
        # (property_name, attr_name, value, percental, expected_text_contains)
        ("RecruitmentUpgrade", "ConstructionSpeedInPercent", 100, True, "Troop Recruitment Speed"),
        ("MovementUpgrade", "BuffReduceDamageImpactUpgrade", 25, False, "Damage Slowdown"),
        ("FactoryUpgrade", "ProductivityUpgrade", 25, True, "Productivity"),
    ]

    passed = 0
    failed = 0

    for property_name, attr_name, value, percental, expected_text in test_cases:
        buff_ui = ui_cache.create_buff_ui(
            property_name=property_name,
            attr_name=attr_name,
            value=value,
            percental=percental
        )

        if not buff_ui:
            print(f"[FAIL] {property_name}.{attr_name}: create_buff_ui returned None")
            failed += 1
            continue

        if not buff_ui.text:
            print(f"[FAIL] {property_name}.{attr_name}: No text in BuffUI")
            failed += 1
            continue

        text_str = buff_ui.text.values.get("english") if hasattr(buff_ui.text, "values") else str(buff_ui.text)

        if expected_text.lower() in text_str.lower():
            print(f"[PASS] {property_name}.{attr_name}: {text_str} | {buff_ui.value}")
            passed += 1
        else:
            print(f"[FAIL] {property_name}.{attr_name}: Expected '{expected_text}', got '{text_str}'")
            failed += 1

    return passed, failed


def main():
    """Run all tests and report results."""
    print("=" * 80)
    print("Buff UI Test Suite")
    print("=" * 80)

    all_passed = 0
    all_failed = 0

    # Run all tests
    tests = [
        test_recruitment_upgrade_variant_text,
        test_movement_upgrade_mapping,
        test_buff_type_name_mapping,
        test_buff_struct_text_fields,
        test_create_buff_ui,
    ]

    for test_func in tests:
        try:
            passed, failed = test_func()
            all_passed += passed
            all_failed += failed
        except Exception as e:
            print(f"\n[ERROR] Test {test_func.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            all_failed += 1

    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Passed: {all_passed}")
    print(f"Failed: {all_failed}")
    print(f"Total:  {all_passed + all_failed}")

    if all_failed == 0:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[ERROR] {all_failed} test(s) failed")

    return all_failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
