# Buff UI Text Mapping Fixes

## Summary

Fixed missing text issues for buff attributes by adding special case mappings and variant text handling. All affected attributes now correctly display localized text in their BuffUI representation.

## Issues Fixed

### 1. RecruitmentUpgrade Attributes

**Problem:** Attributes like `ConstructionSpeedInPercent` and `RecruitmentCostInPercent` showed icons and values but no text.

**Root Cause:** BuffConstructionSpeed and BuffConstructionCost have NO default "Text" field - only variant text fields:
- `ShipyardText`: "Ship Construction Speed" / "Ship Construction Cost"
- `RecruitmentText`: "Troop Recruitment Speed" / "Troop Recruitment Cost"
- `SingleShipText`: "{} Construction Speed" / "{} Construction Cost"
- `SingleTroopText`: "{} Recruitment Speed" / "{} Recruitment Cost"

The code was trying `buff_struct.find("Text")` which returned `None`.

**Solution:** Added special handling in `create_buff_ui()` (uitext.py:1388-1396) to select the appropriate variant text based on property context:
```python
elif buff_type in ["BuffConstructionSpeed", "BuffConstructionCost"]:
    # Select appropriate variant based on property_name
    if "Recruitment" in property_name:
        text_attr = buff_struct.find("RecruitmentText")
    else:
        # Default to ShipyardText for other contexts
        text_attr = buff_struct.find("ShipyardText")
    icon_attr = buff_struct.find("Icon")
```

**Affected Attributes:**
- `RecruitmentUpgrade.ConstructionSpeedInPercent` → Now shows "Troop Recruitment Speed"
- `RecruitmentUpgrade.RecruitmentCostInPercent` → Now shows "Troop Recruitment Cost"
- `RecruitmentUpgrade.RecruitmentSpeedInPercent` → Now shows "Troop Recruitment Speed"

### 2. MovementUpgrade Attributes

**Problem:** Attributes like `BuffReduceDamageImpactUpgrade` and `BuffReduceNegativeWindImpactUpgrade` returned `buff_ui = None`.

**Root Cause:** The attribute names don't match the buff type names in the game data:
- Attribute: `BuffReduceDamageImpactUpgrade` → Should map to: `BuffReduceSpeedImpactOfDamage`
- Attribute: `BuffReduceNegativeWindImpactUpgrade` → Should map to: `BuffReduceNegativeSpeedImpactOfWind`

The automatic mapping failed because the naming conventions differ significantly.

**Solution:** Added special case mappings in `get_buff_type_name()` (uitext.py:535-536):
```python
("Movement", "ReduceDamageImpact"): "BuffReduceSpeedImpactOfDamage",
("Movement", "ReduceNegativeWindImpact"): "BuffReduceNegativeSpeedImpactOfWind",
```

**Note:** The mapping keys use `"ReduceDamageImpact"` (without "Buff" prefix) because the `get_buff_type_name()` function strips the "Buff" prefix from attribute names before checking special mappings (line 474-475).

**Affected Attributes:**
- `MovementUpgrade.BuffReduceDamageImpactUpgrade` → Now shows "Damage Slowdown"
- `MovementUpgrade.BuffReduceNegativeWindImpactUpgrade` → Now shows "Unfavourable Wind Impact"

## Test Results

All tests in `test_buff_ui_suite.py` pass:
- ✓ RecruitmentUpgrade Variant Text (3 tests)
- ✓ MovementUpgrade Buff Type Mapping (2 tests)
- ✓ Buff Type Name Mapping (6 tests)
- ✓ Buff Struct Text Fields (5 tests)
- ✓ create_buff_ui Function (3 tests)

**Total: 19 tests passed, 0 failed**

## Files Modified

### assetextractor/parsing/core/uitext.py

**Line 535-536:** Added special case mappings for MovementUpgrade attributes
```python
("Movement", "ReduceDamageImpact"): "BuffReduceSpeedImpactOfDamage",
("Movement", "ReduceNegativeWindImpact"): "BuffReduceNegativeSpeedImpactOfWind",
```

**Line 1388-1396:** Added special handling for BuffConstructionSpeed/BuffConstructionCost to use variant text
```python
# Special handling for BuffConstructionSpeed/BuffConstructionCost - use variant text
elif buff_type in ["BuffConstructionSpeed", "BuffConstructionCost"]:
    # Select appropriate variant based on property_name
    if "Recruitment" in property_name:
        text_attr = buff_struct.find("RecruitmentText")
    else:
        # Default to ShipyardText for other contexts
        text_attr = buff_struct.find("ShipyardText")
    icon_attr = buff_struct.find("Icon")
```

## Example Output

### Before Fix
```
RecruitmentUpgrade.ConstructionSpeedInPercent
68184 Kaiserliche Maße icon_2d_remaining_time_0 | +100%
```

### After Fix
```
RecruitmentUpgrade.ConstructionSpeedInPercent
68184 Kaiserliche Maße icon_2d_remaining_time_0 | Troop Recruitment Speed | +100%
```

## Similar Patterns to Watch

When adding new buff attributes, check if they need special handling:

1. **Variant text buffs:** Buff types with multiple context-specific text fields (like ShipyardText, RecruitmentText) need special handling in `create_buff_ui()` to select the appropriate variant.

2. **Non-standard naming:** Attributes where the name doesn't follow the `Buff{Property}{Attribute}` pattern need special case mappings in `get_buff_type_name()`.

3. **Prefix handling:** Remember that `get_buff_type_name()` strips the "Buff" prefix from attribute names before checking special mappings. Use the stripped name in the mapping key.

## Testing

Run the test suite to verify buff_ui text mappings:
```bash
uv run python test_buff_ui_suite.py
```

The test suite validates:
- Correct buff type name mapping
- Proper variant text selection
- BuffUI object creation with text, icon, and value
- Context-specific text for different property types
