# Item Extraction Accuracy Test

This test suite compares the output of `extract_items.ipynb` with a manually corrected CSV file to validate extraction accuracy and guide incremental improvements.

## Test Files

- **Test**: `test_item_extraction_accuracy.py`
- **Manual Corrections**: `results/tables/items_english_v1.3_manual_corrections.csv`
- **Generated Output**: `results/tables/items_english.csv`
- **Difference Report**: `results/test_reports/item_extraction_differences.txt`

## Running the Tests

### Run all tests

```bash
uv run pytest tests/integration/test_item_extraction_accuracy.py -v
```

### Run with detailed output

```bash
uv run pytest tests/integration/test_item_extraction_accuracy.py -v -s
```

### Run specific test

```bash
# Test column name mapping
uv run pytest tests/integration/test_item_extraction_accuracy.py::test_column_name_mapping -v

# Test all items present
uv run pytest tests/integration/test_item_extraction_accuracy.py::test_all_manual_items_present -v

# Test extraction accuracy (main test)
uv run pytest tests/integration/test_item_extraction_accuracy.py::test_item_extraction_accuracy -v -s
```

## Understanding the Output

The test compares 8 columns:

1. **name** - Item name (localized)
2. **rarity** - Item rarity (Common, Rare, Epic, Legendary, Unique, etc.)
3. **selling price** - Trade price (mapped from `trade_price`)
4. **affected buildings** - Target buildings/ships (mapped from `targets`)
5. **effects** - Buff descriptions (mapped from `buffs`)
6. **boost condition** - Condition for ItemWithBoost activation
7. **boosted effects** - Enhanced buffs when boost is active (mapped from `boost_buffs`)
8. **source** - Where the item can be obtained

## Current Status

**Total Differences: 29** (as of last run)

### Breakdown by Category

1. **Rarity (7 differences)**
   - Items showing as "Unique" but should be "Legendary"
   - Affected GUIDs: 42625, 42049, 42050, 91415, 91417, 91419, 91421

2. **Boost Condition (8 differences)**
   - Missing: "No patron on island" detection
   - Missing: Emperor reputation zone conditions
   - Missing: Ship module count requirements
   - Missing: "Must be socketed into flagship" detection

3. **Source (14 differences)**
   - Missing: "Subjugate" source (7 items)
   - Missing: "Hall of Fame" source (7 items)

## Step-by-Step Improvement Process

### 1. Identify the Issue

Run the test to see current differences:

```bash
uv run pytest tests/integration/test_item_extraction_accuracy.py::test_item_extraction_accuracy -v -s
```

Read the detailed report at `results/test_reports/item_extraction_differences.txt`

### 2. Choose a Category to Fix

Start with the smallest or most impactful category. For example:

- **Rarity**: 7 items need correction
- **Source (Hall of Fame)**: 7 items need a new source discovery mechanism
- **Boost Condition**: 8 items need better condition extraction

### 3. Investigate the Root Cause

For each category, look at the affected items in the asset data:

```python
# Example: Investigate rarity issue for GUID 42625
from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

item = assets[42625]
print(f"Name: {item.text()}")
print(f"Rarity: {item.Item.Rarity()}")
print(f"Template: {item.template.name}")
```

### 4. Update the Extraction Code

Modify `assetextractor/conversion/statistics/extract_items.ipynb` to fix the issue.

Example fixes:

#### Fix Rarity Mapping

If "Unique" items from specific sources should be "Legendary":

```python
# In extract_all_items() function
rarity = asset.Item.Rarity()
if rarity == "Unique" and is_hall_of_fame_item(asset):
    rarity = "Legendary"
```

#### Add Source Detection

For "Hall of Fame" source:

```python
# In find_all_item_sources() function
if hasattr(item, 'referenced_by'):
    for ref_guid, weighted_ref in item.referenced_by.items():
        source = weighted_ref.source
        if "HallOfFame" in source.template.name:
            sources["hall_of_fame"].append({
                "name": get_source_display_name(source),
                "guid": source.guid
            })
```

#### Improve Boost Condition Extraction

For module requirements:

```python
# In extract_boost_condition() function
try:
    if hasattr(condition, 'ConditionModuleCount'):
        module_count = condition.ConditionModuleCount.ModuleCount()
        module_type = condition.ConditionModuleCount.ModuleType()
        return f"At least {module_count} different {module_type} modules"
except:
    pass
```

### 5. Regenerate the Output

Re-run the notebook to generate a new CSV:

```bash
# Open the notebook in Jupyter or VS Code and run all cells
# Or use papermill if installed:
uv run papermill assetextractor/conversion/statistics/extract_items.ipynb /dev/null
```

### 6. Re-run the Test

```bash
uv run pytest tests/integration/test_item_extraction_accuracy.py::test_item_extraction_accuracy -v -s
```

### 7. Verify the Fix

Check that:
- The number of differences has decreased
- The specific category you fixed now shows fewer differences
- No new differences were introduced in other categories

### 8. Commit the Changes

Once a category is fully fixed:

```bash
git add assetextractor/conversion/statistics/extract_items.ipynb
git add results/tables/items_english.csv
git commit -m "Fix item extraction: [category name]

- Fixed [specific issue]
- Reduced differences from X to Y
- All [category] issues now resolved"
```

## Iteration Strategy

### Recommended Order

1. **Rarity (7 diffs)** - Simple data mapping fix
2. **Source - Hall of Fame (7 diffs)** - Add new source type
3. **Source - Subjugate (7 diffs)** - Add new source type
4. **Boost Condition (8 diffs)** - Improve condition extraction logic

### Goal

The test should eventually pass with **0 differences**, meaning the automated extraction perfectly matches the manual corrections.

## Adding New Manual Corrections

If you find new issues while reviewing the generated CSV:

1. Edit `results/tables/items_english_v1.3_manual_corrections.csv`
2. Add/update the corrections
3. Re-run the test to see the new differences
4. Follow the improvement process above

## Troubleshooting

### Test skips with "Generated CSV not found"

Run the notebook first:
```bash
jupyter nbconvert --to notebook --execute assetextractor/conversion/statistics/extract_items.ipynb
```

### Column name mismatch error

The test maps generated column names to manual column names:
- `trade_price` → `selling price`
- `targets` → `affected buildings`
- `buffs` → `effects`
- `boost_buffs` → `boosted effects`

If columns change, update the `column_mapping` dict in `test_item_extraction_accuracy.py`.

### Too many differences to review

Focus on one category at a time. The detailed report groups differences by column, making it easier to tackle incrementally.

## Success Metrics

Track your progress:
- Initial state: 29 differences
- After rarity fix: ~22 differences
- After source fixes: ~8 differences
- After boost condition fixes: **0 differences** ✓

## Related Files

- **Extraction notebook**: `assetextractor/conversion/statistics/extract_items.ipynb`
- **Manual corrections**: `results/tables/items_english_v1.3_manual_corrections.csv`
- **Test suite**: `tests/integration/test_item_extraction_accuracy.py`
- **Difference report**: `results/test_reports/item_extraction_differences.txt`
- **AGENTS.md**: Guide for working with asset data structure
- **CLAUDE.md**: Project overview and development commands
