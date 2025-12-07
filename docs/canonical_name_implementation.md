# Canonical Name Implementation

This document describes the implementation of the `canonical_name` property for `Asset` and `FileNameAttribute` classes.

## Overview

The `canonical_name` property generates URL-safe, human-readable names for assets and their icons, suitable for use in filenames and URLs.

## Asset.canonical_name

### Format

`{template_word}_{cleaned_name}[_{region}]`

Where:
- `template_word`: First word of the template name (lowercase)
- `cleaned_name`: English name cleaned for URLs (lowercase, no special chars)
- `region`: For production buildings, the associated region name (optional)

### Examples

- **Production Area (Resin Tapper, Roman)**: `production_resin_tapper_latium`
- **ItemWithBoost (Dorian, Philos of Philhellenes)**: `item_dorian`
- **Building (Market)**: `building_market`

### Implementation Details

1. **Template Word Extraction**:
   - Handles space-separated templates: "Production Area" → "production"
   - Handles CamelCase templates: "ItemWithBoost" → "item"
   - Uses regex to extract first CamelCase word: `^[A-Z][a-z]*`

2. **Name Cleaning**:
   - Takes first part before comma (e.g., "Dorian, Philos..." → "Dorian")
   - Converts to lowercase
   - Replaces non-alphanumeric characters with underscores
   - Removes leading/trailing underscores
   - Collapses multiple underscores to single

3. **Region Mapping**:
   - For production buildings, checks `Building.AssociatedRegions` attribute
   - Uses `UITextCache.get_ui_text("Region", region_code)` to get region name
   - Falls back to region code if mapping not found
   - Example: "Roman" → "latium", "Celtic" → "albion"

### Code Location

`assetextractor/parsing/core/assets.py:170-250`

## FileNameAttribute.canonical_name

### Format

`icon_{template}_{asset_canonical_name}`

Where:
- `template`: First word of asset's template name (lowercase)
- `asset_canonical_name`: The asset's canonical name (without template prefix to avoid duplication)

### Examples

- **Production icon**: `icon_production_resin_tapper_latium`
- **Item icon**: `icon_item_dorian`

### Implementation Details

1. Traverses parent chain to find owning `Asset`
2. Uses same template word extraction logic as `Asset.canonical_name`
3. Removes template prefix from asset's canonical name to avoid duplication
4. Falls back to `icon_unknown` if no parent asset found

### Code Location

`assetextractor/parsing/core/attributes.py:751-795`

## UITextCache Region Support

### Overview

Region mapping was added to `UITextCache` to centralize region name lookups and make them available to all parts of the codebase.

### New Components

1. **region_mapping**: `dict[str, Asset]`
   - Maps Region dataset literals to Region assets
   - Populated at startup in `_load_region_mappings()`

2. **_load_region_mappings()**: Method
   - Loads all Region template assets
   - Extracts `Region.RegionID` attribute
   - Stores mapping: literal → asset

3. **_get_region_text()**: Method
   - Retrieves region text and icon from Region asset
   - Returns `UITextMapping` with text and optional icon

4. **get_ui_text()**: Updated
   - Now handles "Region" dataset
   - Returns region text and icon via `_get_region_text()`

### Code Location

`assetextractor/parsing/core/uitext.py`

### Usage

```python
# Get region mapping
ui_cache = assets.properties.ui_text_cache
mapping = ui_cache.get_ui_text("Region", "Roman")

if mapping:
    # Access text
    english_name = mapping.text.values["english"]  # "Latium"

    # Access icon
    if mapping.icon:
        icon_path = mapping.icon.value  # Path to region icon
```

## Testing

### Test Files

1. `tests/debugging/test_canonical_name.py`
   - Tests Asset.canonical_name and FileNameAttribute.canonical_name
   - Verifies production building with region
   - Verifies ItemWithBoost with CamelCase template

2. `tests/debugging/test_region_uitext.py`
   - Tests UITextCache region mapping
   - Verifies Roman → Latium, Celtic → Albion
   - Confirms canonical_name uses UITextCache

### Test Results

All tests pass:
- Asset canonical names match expected format
- Icon canonical names match expected format
- Region mapping correctly loaded
- Type checking passes with zero errors

## Benefits

1. **Consistency**: Standardized naming across all assets
2. **URL-Safe**: No special characters, lowercase only
3. **Human-Readable**: Uses English names, not GUIDs
4. **Centralized**: Region mapping in UITextCache, available to all code
5. **Maintainable**: Data-driven, uses game configuration assets
6. **Type-Safe**: Full type hints, passes pyright checks

## Future Enhancements

Potential improvements:
- Add canonical_name to Template class
- Support for other region-specific assets (not just production)
- Canonical name caching to improve performance
- Support for locales other than English
