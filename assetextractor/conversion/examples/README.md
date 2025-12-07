# Asset Extractor - Beginner Examples

This directory contains beginner-friendly Jupyter notebooks that demonstrate common tasks with the Asset Extractor library.

## Prerequisites

1. Install Jupyter support:
   ```bash
   uv sync --extra jupyter
   ```

2. Ensure you have extracted RDA files:
   ```bash
   extract.cmd
   ```

3. Launch Jupyter:
   ```bash
   uv run jupyter notebook
   ```

## Notebooks Overview

### 01_basic_setup.ipynb
**Start here!** Learn the fundamentals:
- Loading the asset cache
- Exploring templates
- Accessing assets by GUID
- Navigating asset properties
- Using `print_tree()` for debugging

### 02_localization.ipynb
Working with different languages:
- Setting the localization language
- Retrieving localized texts in any language
- Exporting all texts as JSON
- Text formatting with placeholders
- Multilingual comparisons

### 03_iterate_buildings.ipynb
Working with production buildings:
- Finding production building templates
- Extracting building properties
- Getting production chains (inputs/outputs)
- Using `format_production_list()` for formatted output
- Creating building summaries

### 04_buffs_and_effects.ipynb
Understanding buffs and effects:
- Extracting buffs from items using `.buff_ui` property
- Manual buff extraction for custom needs
- Finding affected buildings (targets)
- Comparing different buff types
- Analyzing buff distribution

### 05_construction_materials.ipynb
Analyzing building costs:
- Extracting construction costs
- Using `format_production_list()` method
- Getting maintenance costs
- Comparing costs across buildings
- Finding most expensive buildings
- Exporting cost data to CSV

### 06_backtrack_effects.ipynb
Finding items by their effects:
- Finding items with specific buff types (e.g., productivity)
- Searching items by target building
- Finding items with additional output
- Building reverse indices for fast lookups
- Combining filters (rarity + buff type)

### 07_area_effects.ipynb
Working with area/radius effects:
- Understanding effect scopes (Local, Radius, Area, Session, Island)
- Finding items by effect scope
- Exploring AreaBuff template
- Extracting radius information
- Finding items with largest effect radius

### 08_localize_literals.ipynb
Working with datasets and literals:
- Understanding datasets (enums)
- Getting localized text for dataset values
- Using UI text cache for automatic localization
- Localizing common datasets (Rarity, ItemNiche, Scope, etc.)
- Exporting localized dictionaries to JSON

### 09_pool_references.ipynb
Working with reward pools and asset pools:
- Understanding pool structures (RewardPool, AssetPool)
- Using `pool_assets()` to get all items from a pool with probabilities
- Finding items by their reward pools using `in_reward_pool`
- Identifying which traders, quests, or expeditions offer specific items
- Analyzing pool distribution and rarity

## Recommended Learning Path

1. **Complete Beginner**: Follow notebooks in order (01 → 09)
2. **Quick Start**: 01 → 02 → 04 (basics + localization + buffs)
3. **Data Analysis Focus**: 01 → 03 → 05 → 06 (buildings + costs + searching)
4. **Item Database Creation**: 01 → 02 → 04 → 06 → 08 → 09 (items + buffs + localization + pools)

## Common Patterns

### Get English text from a Text object
```python
text_value = text_obj.values.get('english', 'N/A')
```

### Get localized literal using UI cache
```python
rarity_attr = item.Item.Rarity
if hasattr(rarity_attr, 'ui_text') and rarity_attr.ui_text:
    localized = rarity_attr.ui_text.values.get(LANGUAGE)
```

### Extract all buffs from an item
```python
buff_list = item.buff_ui  # Returns list[BuffUI]
for buff_ui in buff_list:
    print(buff_ui)  # Formatted string representation
```

### Find items by template
```python
items_template = assets.templates["Item"]
for item in items_template.assets:
    # Process each item
    pass
```

### Safe property access
```python
value = item.find("Path.To.Property")
if value and value():
    # Use value()
    pass
```

### Find items in reward pools with probabilities
```python
# Check which reward pools contain this item
if item.in_reward_pool:
    for pool_guid, ref in item.in_reward_pool.items():
        pool = ref.source  # The pool that contains this item
        probability = ref.weight  # Probability of getting this item (0.0-1.0)
        print(f"{pool.name}: {probability * 100:.2f}% chance")

# Get all items from a pool with their probabilities
pool = assets[pool_guid]
pool_results = pool.pool_assets()  # Returns dict[Asset, float]
for asset, probability in pool_results.items():
    print(f"{asset.name}: {probability * 100:.2f}%")
```

## Tips

- **Use `print_tree()`** to explore unknown asset structures
- **Check `buff_ui` property** for automatic buff formatting
- **Use UI text cache** instead of manual text ID lookups
- **Sample data first** when iterating large templates (use `[:100]`)
- **Create helper functions** for repetitive tasks
- **Export to CSV/JSON** for analysis in other tools

## Example Output Structure

Most notebooks save results to:
```
results/example/
├── texts_english_sample.json
├── factory_costs.csv
├── dataset_localizations.json
└── item_card.html
```

## Advanced Topics

For more complex examples, see:
- `../statistics/extract_items.ipynb` - Complete item extraction with all features
- `../assetbrowser/conversion_asset_browser.ipynb` - HTML generation
- `item_card.ipynb` - Styled HTML item cards

## Getting Help

- Check `@AGENTS.md` for comprehensive API documentation
- Check `@CLAUDE.md` for project architecture overview
- Use `asset.print_tree()` to explore structures
- Use `asset.print_meta_tree()` to see metadata

## Common Issues

**Issue**: `config.json not found`
**Solution**: Run from project root directory or update path in notebook

**Issue**: Empty asset cache
**Solution**: Run `extract.cmd` to extract RDA files first

**Issue**: `ui_text_cache is None`
**Solution**: This is normal for attributes without UI text mappings; check the attribute's meta definition

**Issue**: Text shows as GUID
**Solution**: The text might not be available; check `item.text.values` dict

## Contributing

Feel free to create additional example notebooks! Follow these guidelines:
- Keep notebooks focused on one topic
- Add clear markdown explanations
- Show both simple and advanced examples
- Include sample output
- Add error handling for common issues
