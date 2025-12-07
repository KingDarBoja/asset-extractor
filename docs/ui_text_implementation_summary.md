# UI Text Mapping Implementation Summary

## TL;DR

**Get human-readable buff descriptions with icons automatically.** Access `.buff_ui` on any buff attribute to get formatted text, icons, and values without manual text ID lookups or hardcoded strings. Works for 85%+ of buff types, supports conditional formatting, and handles special cases like terrain-specific icons and percentage values.

```python
# Before: Manual lookups, hardcoded text
productivity = item.FactoryUpgrade.ProductivityUpgrade()  # → 0.25
# Need to manually map to "Productivity" text and format as "+25%"

# After: Automatic with .buff_ui
buff_ui = item.FactoryUpgrade.ProductivityUpgrade.buff_ui
print(buff_ui)  # → "icon_productivity | Productivity | +25%"
```

## What Was Built

Automatic UI text and icon mapping system for buff attributes with placeholder-based text formatting.

## Core Functionality

**Automatic Buff Type Mapping**: Pattern-based system derives buff type names from attribute paths (e.g., `FactoryUpgrade.ProductivityUpgrade` → `BuffProductivity`). Handles ~30 special cases for non-standard naming. Achieves 85.8% match rate (121/141 buff attributes).

**Text Formatting with Placeholders**: Fills template strings with actual values from list items:
- `BuffAdditionalFactoryOutput`: "Additional {amount}t {product} every {cycle} cycles"
- Automatically extracts values from list item attributes
- Supports multiple text variants per buff type

**Lazy Loading**: UI text loaded on first access, cached for subsequent use.

## Key Files

**New**:
- `assetextractor/parsing/core/uitext.py` (490 lines): UITextCache with `get_buff_type_name()` and `format_buff_text()` methods
- `test_buff_mapping.py`: Validates buff type name mappings across building/ship/unit buffs
- `docs/ui_text_mapping.md`: Usage documentation

**Modified**:
- `assetextractor/parsing/core/attributes.py`: Added `ui_text` property to ListItem
- `assetextractor/parsing/core/properties.py`: Added `ui_text_cache` field
- `assetextractor/parsing/core/assets.py`: Initialize UITextCache after asset resolution

## Usage

```python
# Automatic mapping
buff_type = ui_cache.get_buff_type_name("FactoryUpgrade", "AdditionalOutput")
# → "BuffAdditionalFactoryOutput"

# Format text with placeholders
list_item = buff.FactoryUpgrade.AdditionalOutput[0]
text = ui_cache.format_buff_text("BuffAdditionalFactoryOutput", list_item)
# → "Additional 1t Flax every 10 cycles"

# Or use the property
formatted = list_item.ui_text
```

## Configuration

Maps 93 buff types from 3 configuration assets (GUIDs 142928, 6000017, 52456) using path templates and variant lists.

## Design

**Pattern-Based Matching**:
1. Strip suffixes: "InPercent", "Percent", "Upgrade", "Upgrage" (typo)
2. Strip "Buff" prefix if present
3. Try patterns: `Buff{attr}`, `Buff{property}{attr}`, `Buff{attr}Upgrade`
4. Check ~30 special case mappings
5. Fallback to substring search

**Text Formatting**:
- Loads buff text structs from configuration assets
- Extracts variant field names per buff type
- Fills placeholders using list item attribute values
- Handles conditional logic (e.g., cycle vs. no cycle variants)

**Error Handling**: Returns `None` for unmatched buffs (20 attributes without UI text). Non-critical system.

## BuffUI Integration (Latest Updates)

**BuffUI Class**: Unified representation of buff attributes with icon, text, and formatted value:
- `icon: FileNameAttribute` - Icon file path
- `text: Text | str` - Localized text (formatted with placeholders)
- `value: str` - Formatted value with sign/percentage (e.g., "+25%")
- `literal: str | None` - Dataset literal for DictAttribute entries
- `__str__()`: One-line representation using icon stem, text, and value

**buff_ui Properties**: Added to all attribute types:
- `PrimitiveAttribute.buff_ui` → `BuffUI | None`
- `UpgradeAttribute.buff_ui` → `BuffUI | None` (uses `percental` flag for formatting)
- `ListAttribute.buff_ui` → `list[BuffUI]` (uses `ui_text` from ListItems)
- `DictAttribute.buff_ui` → `list[BuffUI]` (only non-zero values, uses literals as keys)

**Special Cases**:
- `BuffCanUseTerrain`: Uses terrain-specific text/icons (ForestText/Icon, MeadowText/Icon, MarshText/Icon)
- `AreaFertilityPercent`/`FertilityPercent`: Extracts text/icon from referenced Fertility asset via `AddedAreaFertility`/`AddedFertility`
- `BuffResidenceProvidedNeedText`: Follows ProvidedNeed reference to get product name and building icon from Need asset's NeedProduct
- `BuffOutputWorkforce` (`AdditionalWorkforces`): Follows WorkforceGUID reference to get workforce name and icon, formats with AdditionalText variant
- `BuffReplaceWorkforceText` (`ReplaceWorkforce`): Follows OldWorkforce and NewWorkforce references to get both workforce names and icon from NewWorkforce
- **`AdditionalFunctionalEffect`**: Handles two-level buff indirection where buffs reference Effect assets containing nested buffs (BuildingUpgrade.AdditionalFunctionalEffect → Effect → Effect.Buffs). Uses recursion with `is_additional_effect` flag to prevent infinite loops. When processing nested buffs, applies "AttributeInRange" text template for area/radius effect formatting instead of plain literal text.
- Percentage formatting: Respects `UpgradeAttribute.percental` flag for accurate value display

**Usage**:
```python
# Single attribute
buff_ui = item.FactoryUpgrade.ProductivityUpgrade.buff_ui
# → BuffUI(icon=..., text="Productivity", value="+25%")

# List attribute
buff_uis = item.FactoryUpgrade.AdditionalOutput.buff_ui
# → [BuffUI(text="Additional 1t Flax every 10 cycles", ...)]

# Dict attribute (only non-zero)
buff_uis = item.BuildingUpgrade.AdditionalAttributes.buff_ui
# → [BuffUI(literal="Money", value="+100"), BuffUI(literal="Happiness", value="+50")]

# ProvidedNeedUpgrade with product name and icon
buff_uis = item.ResidenceUpgrade.ProvidedNeedUpgrade.buff_ui
# → [BuffUI(icon="icon_3d_public_roman_marketplace_0", text="Marketplace Need Supplied")]

# AdditionalWorkforces with workforce name and icon
buff_uis = item.BuildingUpgrade.AdditionalWorkforces.buff_ui
# → [BuffUI(icon="icon_2d_libertus_workforce_roman_0", text="Also provides equal amounts of Libertus Workforce")]

# ReplaceWorkforce with both workforce names and icon from NewWorkforce
buff_uis = item.MaintenanceUpgrade.ReplaceWorkforce.buff_ui
# → [BuffUI(icon="icon_2d_plebeians_workforce_roman_0", text="Run by Plebeian Workforce, instead of Liberti Workforce")]

# String representation
str(buff_ui)
# → "icon_productivity | Productivity | +25%"
```

## Incident Types

**BuffInfectableImmunity**: Context-aware text variants now work correctly. BuildingBuff shows "Immune against Disease", AreaBuff shows "Prevents new Disease outbreaks".

**IncidentType mappings**: `_load_incident_type_mappings()`: Iterates `templates["IncidentInfection"].assets` to build mapping from InfectionType literal → asset
