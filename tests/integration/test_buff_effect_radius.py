"""Test BuffEffectRadius implementation for RadiusEffectRangeUpgrade and RadiusEffectRangeTarget."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json('config.json')
print("Loading assets...")
assets = AssetCache.load(config)
ui_cache = assets.properties.ui_text_cache
print("Assets loaded successfully\n")

# Test 1: Buff type derivation
print("=" * 70)
print("Test 1: Buff Type Derivation")
print("=" * 70)
buff_type = ui_cache.get_buff_type_name("AreaBuff", "RadiusEffectRangeUpgrade")
print(f"Property: AreaBuff, Attribute: RadiusEffectRangeUpgrade")
print(f"Derived buff type: {buff_type}")
assert buff_type == "BuffEffectRadius", f"Expected 'BuffEffectRadius', got '{buff_type}'"
print("✓ Buff type derivation works correctly\n")

# Test 2: Get item and check structure
print("=" * 70)
print("Test 2: Asset Structure (GUID 81435 - Market Forces)")
print("=" * 70)
item = assets.get(81435)
item_name = item.text.values.get('english') if item.text else 'N/A'
print(f"Item name: {item_name}")

area_buff = item.find('AreaBuff')
assert area_buff is not None, "AreaBuff property not found"
print("✓ AreaBuff property exists")

# Check RadiusEffectRangeUpgrade
assert hasattr(area_buff, 'RadiusEffectRangeUpgrade'), "RadiusEffectRangeUpgrade not found"
upgrade_attr = area_buff.RadiusEffectRangeUpgrade
print(f"\nRadiusEffectRangeUpgrade:")
print(f"  Value: {upgrade_attr()}")
print(f"  Percental: {upgrade_attr.percental}")
print(f"  Type: {type(upgrade_attr).__name__}")

# Check RadiusEffectRangeTarget
assert hasattr(area_buff, 'RadiusEffectRangeTarget'), "RadiusEffectRangeTarget not found"
target_list = area_buff.RadiusEffectRangeTarget
print(f"\nRadiusEffectRangeTarget:")
print(f"  Type: {type(target_list).__name__}")
print(f"  Length: {len(target_list._value_list)}")

# Inspect target items
for idx, target_item in enumerate(target_list):
    target_asset = target_item.Target()
    target_name = target_asset.text.values.get('english') if target_asset.text else 'N/A'
    print(f"  Target[{idx}]: {target_name} (GUID: {target_asset.guid})")

print("✓ Asset structure is correct\n")

# Test 3: RadiusEffectRangeUpgrade.buff_ui (PrimitiveAttribute)
print("=" * 70)
print("Test 3: RadiusEffectRangeUpgrade.buff_ui (PrimitiveAttribute)")
print("=" * 70)
upgrade_ui = area_buff.RadiusEffectRangeUpgrade.buff_ui

# Check that buff_ui is not None
assert upgrade_ui is not None, "RadiusEffectRangeUpgrade.buff_ui should not be None"
print(f"✓ buff_ui is not None")

# Check value formatting (should be +25% because percental=True)
print(f"\nBuffUI details:")
print(f"  Icon: {upgrade_ui.icon}")
print(f"  Text: {upgrade_ui.text}")
print(f"  Value: {upgrade_ui.value}")
print(f"  String representation: {upgrade_ui}")

assert upgrade_ui.value == "+25%", f"Expected value '+25%', got '{upgrade_ui.value}'"
print(f"✓ Value is correctly formatted as percentage: {upgrade_ui.value}")

# Check text
assert upgrade_ui.text is not None, "Text should not be None"
text_str = str(upgrade_ui.text)
print(f"✓ Text exists: {text_str}")

# Check icon
assert upgrade_ui.icon is not None, "Icon should not be None"
print(f"✓ Icon exists: {upgrade_ui.icon}\n")

# Test 4: RadiusEffectRangeTarget.buff_ui (ListAttribute)
print("=" * 70)
print("Test 4: RadiusEffectRangeTarget.buff_ui (ListAttribute)")
print("=" * 70)
target_uis = area_buff.RadiusEffectRangeTarget.buff_ui

# Check that buff_ui returns a list
assert isinstance(target_uis, list), f"Expected list, got {type(target_uis)}"
print(f"✓ buff_ui returns a list")

# Check list length
assert len(target_uis) == 1, f"Expected 1 target, got {len(target_uis)}"
print(f"✓ List has correct length: {len(target_uis)}")

# Check first item
target_ui = target_uis[0]
assert target_ui is not None, "Target buff_ui should not be None"
print(f"\nBuffUI details:")
print(f"  Icon: {target_ui.icon}")
print(f"  Text: {target_ui.text}")
print(f"  Value: {target_ui.value}")
print(f"  String representation: {target_ui}")

# Check that text is not None
assert target_ui.text is not None, "Target text should not be None"
print(f"✓ Text is not None")

# Check if text contains the target building name "Markets"
text_str = str(target_ui.text)
if hasattr(target_ui.text, 'values'):
    # It's a Text object with localized values
    text_str = target_ui.text.values.get('english', str(target_ui.text))

print(f"✓ Text value: '{text_str}'")

# The text should be "Effect range of Markets"
assert "Markets" in text_str, f"Expected 'Markets' in text, got '{text_str}'"
print(f"✓ Text contains target building name 'Markets'")

assert "Effect range" in text_str or "effect range" in text_str.lower(), \
    f"Expected 'Effect range' in text, got '{text_str}'"
print(f"✓ Text contains 'Effect range'")

# Check icon
assert target_ui.icon is not None, "Icon should not be None"
print(f"✓ Icon exists: {target_ui.icon}\n")

# Test 5: Summary
print("=" * 70)
print("Test 5: Complete Output Summary")
print("=" * 70)
print(f"Item: {item_name} (GUID: {item.guid})")
print(f"\nUpgrade attribute:")
print(f"  {area_buff.RadiusEffectRangeUpgrade.buff_ui}")
print(f"\nTarget list:")
for idx, target_ui in enumerate(target_uis):
    print(f"  [{idx}] {target_ui}")

print("\n" + "=" * 70)
print("✅ All tests passed!")
print("=" * 70)
