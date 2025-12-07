# UI Text Mapping System

## Overview

Automatically maps buff attributes to their localized display text and icons by loading game configuration assets. Eliminates hardcoded lookup tables.

## Quick Start

### Configuration Assets

The game uses special configuration assets that map dataset/enum values to UI text IDs and icon GUIDs:

1. **ItemInfotipTextFeature (GUID 142928)**
   - Maps ~100+ buff types to display text and icons
   - Includes variant text for context-specific display
   - Example: `BuffProductivity` → text ID, icon GUID

2. **ItemBalancing (GUID 6000017)**
   - Maps item properties (rarity, niche, scope, allocation) to text/icons
   - Example: `Legendary` (rarity) → "Legendary" text, legendary icon

3. **BuffConfig (GUID 52456)**
   - Maps buff categories to category names

### Architecture

```
┌─────────────────┐
│  Configuration  │  (ItemInfotipTextFeature, ItemBalancing, etc.)
│     Assets      │
└────────┬────────┘
         │ loads at startup
         ▼
   ┌──────────┐
   │ UITextCache │  (Lookup table: (dataset, literal) → UITextMapping)
   └────┬─────┘
        │ referenced by
        ▼
  ┌──────────────────┐
  │ MetaPropertyCache │  (holds ui_text_cache)
  └────┬─────────────┘
       │ used by
       ▼
 ┌─────────────────┐
 │ PrimitiveAttribute │  (lazy loads UI text via properties)
 └──────────────────┘
```

```python
# Load assets
assets = AssetCache.load(config)

# Get UI text from any buff attribute
buff_attr = item.find("BuildingUpgrade.ProductivityUpgrade")
text_id = buff_attr.ui_text_id          # Localized text ID
icon = buff_attr.ui_icon_guid           # Icon asset GUID
variants = buff_attr.ui_text_variants   # Context-specific text

# Or query the cache directly
ui_cache = assets.properties.ui_text_cache
mapping = ui_cache.get_ui_text("Rarity", "Legendary")

# Automatic buff type mapping from attributes
buff_type = ui_cache.get_buff_type_name("FactoryUpgrade", "ProductivityUpgrade")
# Returns: "BuffProductivity"

# Format buff text with placeholders
list_item = buff.FactoryUpgrade.AdditionalOutput[0]
formatted = ui_cache.format_buff_text("BuffAdditionalFactoryOutput", list_item)
# Returns: "Additional 1t Flax every 10 cycles"
```

## Key Features

**Automatic Buff Type Mapping**: Derives buff type names from attribute paths with pattern-based matching and ~30 special cases. Achieves 85.8% match rate across building, ship, and unit buffs.

**Text Formatting**: Fills placeholders in buff text templates with actual values from list items (e.g., amounts, products, cycles).

**Lazy Loading**: UI text loaded on-demand, cached after first access.

**Data-Driven**: Configuration uses 3 asset GUIDs + path templates instead of 200+ manual entries.

## Supported Datasets

- **BuffUpgradeType**: ~93 buff types with automatic name mapping
- **Rarity**: Common, Rare, Epic, Legendary, etc.
- **ItemNiche**: Finance, Religion, Research, Culture, Military, etc.
- **ItemAllocation**: Ship, Villa, None
- **Scope**: Local, Radius, Area, Session, etc.

## Configuration

Add new datasets in `assetextractor/parsing/core/uitext.py`:

```python
CONFIG_ASSETS = {
    142928: {  # ItemInfotipTextFeature
        "path": "ItemInfotipTextFeature.BuffUpgradeTextAndIcons",
        "buff_texts": "ItemInfotipTextFeature.BuffUpgradeTextAndIcons",
        "mappings": {
            "BuffUpgradeType": "{}.Text",
        },
        "variants": {
            "BuffAdditionalFactoryOutput": [
                "TextWithSpecifiedProduct",
                "TextWithSpecifiedProductEveryCycle",
            ],
        },
    },
}
```

## Implementation

**Files**:
- `assetextractor/parsing/core/uitext.py`: UITextCache with mapping and formatting
- `assetextractor/parsing/core/attributes.py`: UI text properties on attributes
- `assetextractor/parsing/core/assets.py`: Cache initialization

**Initialization**: UITextCache loads after assets resolve, builds lookup tables from configuration assets.

**Error Handling**: Returns `None` for missing mappings, logs warnings for missing assets. Non-critical system.
