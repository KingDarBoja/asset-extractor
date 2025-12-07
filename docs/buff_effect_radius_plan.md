# Implementation Plan: BuffEffectRadius Support

## Overview

Add support for `BuffEffectRadius` to the buff_ui system. This buff type handles area effect range upgrades with specific building targets.

**Example Item**: Market Forces (GUID 81435)
- `AreaBuff.RadiusEffectRangeUpgrade`: +25% (PrimitiveAttribute, percental=True)
- `AreaBuff.RadiusEffectRangeTarget[0].Target`: Markets (GUID 31659)

**Expected Output**:
- `RadiusEffectRangeUpgrade.buff_ui` → `BuffUI(icon="...", text="Effect Range", value="+25%")`
- `RadiusEffectRangeTarget.buff_ui` → `[BuffUI(icon="...", text="Effect range of Markets", value=None)]`

## Analysis

### Current State

1. **BuffEffectRadius exists** in `ui_cache.buff_text_structs`:
   - Text: "Effect range of {}" (with format placeholder)
   - Icon: "Icon Effect Area EffectRange"
   - No variants

2. **Buff type derivation fails**:
   - Property: "AreaBuff" → property_base = "Area"
   - Attribute: "RadiusEffectRangeUpgrade" → attr_base = "RadiusEffectRange"
   - Pattern `Buff{attr_base}` = "BuffRadiusEffectRange" → NOT FOUND
   - Pattern `Buff{property}{attr}` = "BuffAreaRadiusEffectRange" → NOT FOUND
   - Needs special mapping: `("Area", "RadiusEffectRange") → "BuffEffectRadius"`

3. **Current behavior**:
   - `RadiusEffectRangeUpgrade.buff_ui` returns `None` (no buff type mapping)
   - `RadiusEffectRangeTarget.buff_ui` returns `[]` (ListAttribute calls ListItem.buff_ui, but no formatter)

### Structure

```
AreaBuff/
├── RadiusEffectRangeUpgrade (PrimitiveAttribute)
│   ├── Value: 25.0
│   └── Percental: True
└── RadiusEffectRangeTarget (ListAttribute)
    └── [0] (ListItem)
        └── Target (ReferenceAttribute) → Asset 31659 (Markets)
```

### Similar Implementations

**BuffOutputWorkforce** (lines 647-693 in uitext.py):
- Extracts `WorkforceGUID` reference from list item
- Follows reference to get asset name from `text` property
- Gets icon from asset's `Standard.IconFilename`
- Formats with `AdditionalText` variant

**BuffResidenceProvidedNeedText** (lines 601-645 in uitext.py):
- Extracts `ProvidedNeed` reference
- Follows to Need asset → gets product → gets product text
- Icon from Need asset

**Pattern to follow**: Similar to BuffOutputWorkforce (simpler - single reference, format with asset name)

## Implementation Steps

### 1. Add Special Mapping in uitext.py

**File**: `assetextractor/parsing/core/uitext.py`
**Location**: Line ~420 in `BUFF_NAME_SPECIAL_MAPPINGS`

```python
# Add to BUFF_NAME_SPECIAL_MAPPINGS dict
("Area", "RadiusEffectRange"): "BuffEffectRadius",
```

**Verification**: After adding, `ui_cache.get_buff_type_name("AreaBuff", "RadiusEffectRangeUpgrade")` should return `"BuffEffectRadius"`

### 2. Implement Format Method in UITextCache

**File**: `assetextractor/parsing/core/uitext.py`
**Location**: After `_format_passive_trade_bonus()` (around line 761)

```python
def _format_effect_radius(
    self, list_item: Any, buff_info: dict[str, Any]
) -> Text | None:
    """Format BuffEffectRadius with building target name.

    Template: "Effect range of {}"
    Placeholder: [target_building_name]

    Structure:
    - list_item.Target (ReferenceAttribute) → Building asset

    Example: "Effect range of Markets"
    """
    try:
        # Get the target building reference
        if not hasattr(list_item, "Target"):
            return None

        target_ref = list_item.Target
        if not target_ref:
            return None

        # Follow reference to get building asset
        target_asset = target_ref()
        if not target_asset:
            return None

        # Get building name from asset text
        target_name = None
        if hasattr(target_asset, "text") and target_asset.text:
            target_name = target_asset.text

        if not target_name:
            return None

        # Get text template from buff struct
        struct = buff_info["struct"]
        text_attr = struct.find("Text")
        if not text_attr:
            return None

        text_obj = text_attr()
        if not text_obj:
            return None

        # Format with target name
        # Text is "Effect range of {}", format with [target_name]
        if hasattr(text_obj, "format"):
            return text_obj.format([target_name])

        return text_obj

    except Exception:
        return None
```

**Key differences from BuffOutputWorkforce**:
- Simpler: No variants (no AdditionalText field)
- Direct text reference (not localized text object like workforce)
- Single placeholder

### 3. Register Formatter in format_buff_text()

**File**: `assetextractor/parsing/core/uitext.py`
**Location**: In `format_buff_text()` method, around line 544

```python
# Add after BuffPassiveTradeBonus case
if buff_type == "BuffEffectRadius":
    return self._format_effect_radius(list_item, buff_info)
```

### 4. Icon Handling

**No special handling needed** - the icon comes from the buff struct:
- Icon path: "Icon Effect Area EffectRange"
- Automatically resolved by existing `create_buff_ui_list()` logic

### 5. Testing

**Test file**: Create `test_buff_effect_radius.py`

```python
from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json('config.json')
assets = AssetCache.load(config)
ui_cache = assets.properties.ui_text_cache

# Test 1: Buff type derivation
buff_type = ui_cache.get_buff_type_name("AreaBuff", "RadiusEffectRangeUpgrade")
assert buff_type == "BuffEffectRadius", f"Expected BuffEffectRadius, got {buff_type}"
print("✓ Buff type derivation works")

# Test 2: Get item and check buff_ui
item = assets.get(81435)
area_buff = item.find('AreaBuff')

# Test RadiusEffectRangeUpgrade (PrimitiveAttribute)
upgrade_ui = area_buff.RadiusEffectRangeUpgrade.buff_ui
assert upgrade_ui is not None, "RadiusEffectRangeUpgrade.buff_ui should not be None"
assert upgrade_ui.value == "+25%", f"Expected +25%, got {upgrade_ui.value}"
print(f"✓ RadiusEffectRangeUpgrade.buff_ui: {upgrade_ui}")

# Test RadiusEffectRangeTarget (ListAttribute)
target_uis = area_buff.RadiusEffectRangeTarget.buff_ui
assert len(target_uis) == 1, f"Expected 1 target, got {len(target_uis)}"
assert target_uis[0].text is not None, "Target text should not be None"
# Check if text contains "Markets"
text_str = str(target_uis[0].text)
assert "Markets" in text_str, f"Expected 'Markets' in text, got {text_str}"
print(f"✓ RadiusEffectRangeTarget.buff_ui: {target_uis[0]}")

print("\n✅ All tests passed!")
```

## Edge Cases to Handle

1. **Missing Target attribute**: Return None (handled in try-except)
2. **Target reference is None**: Return None (check before dereferencing)
3. **Target asset has no text**: Return None (check for text property)
4. **Text template missing**: Return None (check for Text field in struct)
5. **Multiple targets**: Should work automatically (list comprehension in create_buff_ui_list)

## Files Modified

1. `assetextractor/parsing/core/uitext.py`:
   - Add mapping to `BUFF_NAME_SPECIAL_MAPPINGS` (~line 420)
   - Add `_format_effect_radius()` method (~line 761)
   - Register formatter in `format_buff_text()` (~line 544)

2. `test_buff_effect_radius.py` (new):
   - Comprehensive tests for both attributes
   - Validates text formatting with placeholder

## Success Criteria

- [ ] `ui_cache.get_buff_type_name("AreaBuff", "RadiusEffectRangeUpgrade")` returns `"BuffEffectRadius"`
- [ ] `RadiusEffectRangeUpgrade.buff_ui` returns `BuffUI` with `value="+25%"`
- [ ] `RadiusEffectRangeTarget.buff_ui` returns `[BuffUI]` with formatted text containing target name
- [ ] Text includes building name (e.g., "Effect range of Markets")
- [ ] Icon is correctly resolved from buff struct
- [ ] All tests in `test_buff_effect_radius.py` pass

## Notes

- **Percental handling**: Already works automatically in `PrimitiveAttribute.buff_ui` property (lines 380-443 in attributes.py)
- **No variants**: BuffEffectRadius has no variant fields, simpler than other formatters
- **Text is already a Text object**: Unlike BuffOutputWorkforce which needs to get text from asset, here the text template is already a Text object with format() method
- **Reusable pattern**: This formatter can serve as a template for other single-reference buff types

## Estimated Changes

- **3 lines added** to BUFF_NAME_SPECIAL_MAPPINGS
- **~40 lines** for `_format_effect_radius()` method (with docstring)
- **2 lines** to register formatter
- **~35 lines** for test file
- **Total: ~80 lines** (minimal, focused changes)
