# Asset Extractor Guide for AI Agents
@CLAUDE.md

This guide documents how to navigate and extract data from Anno 117's asset structure using the asset-extractor library.

## Project Overview

Asset Extractor is a modular Python library for reading Anno 117 game data files, resolving dependencies, and converting them into legible formats. The project consists of three main modules:

1. **Extraction** (`assetextractor/extraction/`) - Opens RDA files and extracts XML, DDS, and CFG files to a cache directory using RDAConsole.exe
2. **Parsing** (`assetextractor/parsing/core/`) - Reads XML files and reconstructs their hierarchical structure in memory with full inheritance resolution
3. **Conversion** (`assetextractor/conversion/`) - Generates excerpts in different formats (HTML, JSON) from the parsed asset data

The library provides a complete object model for navigating Anno 117's asset system, including items, buffs, buildings, templates, localized text, and UI mappings.

## Table of Contents

1. [Running Scripts and Modules](#running-scripts-and-modules)
2. [Class Reference](#class-reference)
3. [Basic Setup](#basic-setup)
4. [Item Structure](#item-structure)
5. [Buff System](#buff-system)
6. [UI Text Mapping](#ui-text-mapping)
7. [Boost Conditions (ItemWithBoost)](#boost-conditions-itemwithboost)
8. [Finding Item Sources](#finding-item-sources)
9. [Asset Pools](#asset-pools)
10. [Common Patterns](#common-patterns)

## Running Scripts and Modules

### Important: Module vs File Execution

When running Python scripts in this project, you **must** run them as modules using the `-m` flag, not as file paths. This ensures the Python import system can find the `assetextractor` package.

**Correct:**
```bash
# Run as a module (project root is automatically added to sys.path)
uv run python -m assetextractor.conversion.calculator.building-sizes
uv run python -m assetextractor.extraction.extract
uv run python -m assetextractor.versioning
```

**Incorrect:**
```bash
# Running as a file path - will fail with ModuleNotFoundError
uv run python assetextractor/conversion/calculator/building-sizes.py
```

**Testing with pytest:**
```bash
# Pytest automatically handles module imports correctly
uv run pytest                                                          # Run all tests
uv run pytest -v                                                       # Verbose output
uv run pytest tests/integration/verify_building_sizes.py              # Specific file
uv run pytest tests/integration/verify_building_sizes.py::test_csv_loading -v  # Specific test
uv run pytest -k "building_size"                                      # Tests matching keyword
```

### Converting File Paths to Module Names

To convert a file path to a module name:
1. Remove the project root directory
2. Remove the `.py` extension
3. Replace path separators (`/` or `\`) with dots (`.`)

Examples:
- `assetextractor/conversion/calculator/building-sizes.py` → `assetextractor.conversion.calculator.building-sizes`
- `assetextractor/extraction/extract.py` → `assetextractor.extraction.extract`
- `tests/integration/test_buff_ui.py` → `tests.integration.test_buff_ui`

### Running from Different Directories

Always run scripts from the **project root** directory (`C:\dev\asset-extractor`). The `-m` flag assumes you're at the root of the package structure.

## Class Reference

### Parsing Module (assetextractor/parsing/core/)

#### common.py
- `AttributeMissingError(Exception)` - raised when expected XML attribute is missing
- `NamedElement[CacheT]` - base class for XML elements, provides name, find(), get(), full_path, property_path
- `Group[CacheT](NamedElement[CacheT])` - container for elements and subgroups, provides print_tree()
- `ElementCache[ElementT, GroupT]` - base cache class with elements dict, provides add(), get(), find(), print_tree()
- `Dataset(NamedElement["DatasetCache"])` - dataset with name-to-id mappings, provides literals property
- `DatasetCache(ElementCache["Dataset"])` - loads datasets.xml file

#### attributes.py
- `parse_bool(text)` - converts Anno boolean string to Python bool
- `Property(NamedElement[Any])` - property with nested structure, provides resolve_inheritance(), print_tree()
- `Attribute[CacheT, ValueT](NamedElement[CacheT])` - base class for attributes, provides __call__(), is_compound, is_default
- `PrimitiveAttribute(Attribute)` - handles Boolean, Choice, Float, FloatOrPercental, Int64, Integer, String types, provides ui_text_id, ui_icon_guid, ui_text_variants, buff_ui
- `ColorAttribute(Attribute)` - handles single int or dict with color components
- `TextAttribute(Attribute)` - references localized text by ID, returns Text object
- `TimeAttribute(Attribute)` - duration stored as datetime.timedelta
- `UpgradeAttribute(Attribute)` - numeric value with percental flag, provides buff_ui
- `FlagsAttribute(Attribute)` - semicolon-separated list of dataset literals, provides buff_ui
- `FileNameAttribute(Attribute)` - file path with .dds resolution, provides is_image, get_image(), get_data_url()
- `ReferenceAttribute(Attribute)` - reference to Asset by GUID, provides set_reference()
- `QuestAttribute(ReferenceAttribute)` - quest reference with win_quest boolean
- `ListItem` - container for list item data, provides full_path, property_path, buff_ui, print_tree()
- `ListAttribute(Attribute)` - ordered list of ListItem, provides __len__(), buff_ui
- `GenericDictAttribute[ValueT](Attribute)` - base for dict-like attributes, provides __len__()
- `DictAttribute(GenericDictAttribute)` - dict of attributes for Array/Struct/Property, provides buff_ui
- `TemplateAttribute(GenericDictAttribute)` - AutoCreateAsset with template reference, provides set_template(), process_properties()
- `AttributeFactory` - static factory with create(), create_default_node()

#### properties.py
- `ValueDefinition(NamedElement["MetaPropertyCache"])` - metadata for attributes, provides is_primitive, is_compound
- `MetaProperty(NamedElement["MetaPropertyCache"])` - metadata for properties, provides is_complex, print_tree()
- `PropertyGroup(Group["MetaPropertyCache"])` - group with properties and defaults
- `MetaPropertyCache(ElementCache[MetaProperty, PropertyGroup])` - parses properties-toolone.xml, provides resolve_template_attributes()

#### templates.py
- `WeightedReference` - stores reference with optional weight and path
- `Template(NamedElement["TemplateCache"])` - template definition, provides add_instance(), print_tree(), print_meta_tree(), assets property
- `TemplateGroup(Group["TemplateCache"])` - group containing templates
- `TemplateCache(ElementCache[Template, TemplateGroup])` - loads templates.xml, provides resolve_template_attributes()

#### assets.py
- `Asset(NamedElement["AssetCache"])` - concrete asset instance, provides guid, text, template, resolve_inheritance(), set_referenced_by(), print_tree(), short_description, long_description, buff_ui (returns list[BuffUI])
- `AssetGroup(Group["AssetCache"])` - group containing assets
- `AssetCache(ElementCache[Any])` - loads assets.xml, provides resolve_inheritance(), resolve_references(), resolve_dlc_unlocks(), static load(config)

#### texts.py
- `Text(NamedElement["TextCache"])` - localized text with id and values dict, provides has_html_escapes(), count_format_args(), format(list), __call__() for conversion
- `TextCache(ElementCache[Text])` - loads texts_*.xml for all languages, provides converter property
- `StandardTextConverter` - converts Text to string in specified language, provides __call__(text)

#### uitext.py
- `UITextMapping` - dataclass with text_id, text, icon, variants fields
- `BuffUI` - dataclass with icon, text, value, literal fields for UI display
- `UITextCache` - maps dataset literals to UI text/icons, provides get_ui_text(), get_text_id(), get_buff_type_name(), format_buff_text(), create_buff_ui(), create_buff_ui_list(), create_buff_ui_dict(), create_buff_ui_flags()

### Conversion Module (assetextractor/conversion/)

#### assetbrowser/convert.py
- `Converter` - generates HTML asset browser, provides render_elements(), render_overview(), run()

## Basic Setup

```python
from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load the asset cache
config = Config.from_json("config.json")
assets = AssetCache.load(config)
templates = assets.templates

# Access specific template
items = templates["Item"].assets
```

## Getting BuffUI from Assets

### Asset.buff_ui Property

All `Asset` objects now have a `buff_ui` property that recursively traverses all nested attributes and returns a list of `BuffUI` objects representing the asset's effects.

```python
# Get an asset (Item, BuildingBuff, ShipBuff, etc.)
item = assets[some_guid]

# Get all BuffUI representations from the asset
buff_ui_list = item.buff_ui  # Returns list[BuffUI]

# Iterate through the buffs
for buff_ui in buff_ui_list:
    # Access BuffUI properties
    icon = buff_ui.icon          # FileNameAttribute or None
    text = buff_ui.text          # Text object or str or None
    value = buff_ui.value        # Formatted string (e.g., "+25%", "50")
    literal = buff_ui.literal    # Dataset literal or None

    # Get English text
    if text and hasattr(text, "values"):
        english_text = text.values.get("english", "N/A")
    elif isinstance(text, str):
        english_text = text

    # Get icon filename
    if icon and icon.value:
        icon_filename = icon.value.stem
```

**How it works:**
- Recursively traverses all properties and attributes in the asset
- Calls the `buff_ui` property on each attribute that has one
- Collects all non-None BuffUI results into a single list
- Handles nested structures (Properties, DictAttribute, ListAttribute, etc.)

**Supported attribute types:**
- `PrimitiveAttribute` - Returns single BuffUI for Choice attributes with datasets
- `UpgradeAttribute` - Returns single BuffUI with formatted value and percental
- `FlagsAttribute` - Returns list of BuffUI for flag literals
- `ListAttribute` - Returns list of BuffUI for formatted list items
- `DictAttribute` - Returns list of BuffUI for dict entries with non-zero values
- `ListItem` - Returns single BuffUI with formatted text (for special buff types)

**Example usage:**

```python
# Get all items from the Item template
items_template = assets.templates["Item"]

for item in items_template.assets:
    buff_list = item.buff_ui

    if buff_list:
        print(f"\n{item.name} ({item.guid}):")
        for buff in buff_list:
            print(f"  - {buff}")  # Uses BuffUI.__str__()
```

**Example with BuildingBuff:**

```python
# Get a building buff
buff = assets[82302]  # TechEffect Production Beaver Terrain Buff

# Get all BuffUI objects
buffs = buff.buff_ui
# Returns:
# [
#   BuffUI(icon=productivity_icon, text="Productivity", value="+25%"),
#   BuffUI(icon=forest_icon, text="Can use forests", value="+1"),
#   BuffUI(icon=meadow_icon, text="Can use meadows", value="+1")
# ]
```

## Item Structure

### Core Item Properties

Items in Anno 117 follow this structure:

```python
# Basic properties
item.guid                    # Unique identifier
item.text.values["english"]  # Localized name
item.Item.Rarity()          # "Common", "Rare", "Epic", "Legendary"
item.Item.TradePrice()      # Purchase price
item.Item.Allocation()      # "Villa", "Ship", etc.
item.Item.Niche()           # "Finance", "Nautics", etc.
item.Item.ItemType()        # "Specialist", "Captains", etc.

# Effect system
item.Effect.Targets         # Buildings/ships affected
item.Effect.Buffs           # List of buff references
item.Effect.EffectScope()   # "Local", "Radius", "Session"
```

### Extracting Item Names

Always use localized text for display:

```python
def get_english_name(asset):
    if asset.text is not None and "english" in asset.text.values:
        return asset.text.values["english"]
    # Fallback to internal name
    return asset.find("Standard.Name")()
```

## Buff System

### Two Buff Types

1. **BuildingBuff** - Affects buildings
2. **ShipBuff** - Affects ships

### Accessing Buff Attributes

```python
# Get the buff asset
effect = item.Effect
for buff_entry in effect.Buffs:
    buff_asset = assets[buff_entry.GUID.guid]

    # Check buff type
    if "ShipBuff" in buff_asset.template.name:
        # Process ship buffs
        pass
    else:
        # Process building buffs
        pass
```

### BuildingBuff Upgrade Categories

```python
# BuildingUpgrade
buff.find("BuildingUpgrade.AdditionalAttributes")  # Money, Happiness, Prestige
buff.find("BuildingUpgrade.WorkforceModifierInPercent")
buff.find("BuildingUpgrade.AdditionalFunctionalEffect")  # Points to Effect asset

# ResidenceUpgrade
buff.find("ResidenceUpgrade.ProvidedNeedUpgrade")
buff.find("ResidenceUpgrade.ConsumptionModifierInPercent")
buff.find("ResidenceUpgrade.NeedProvidedNeedAttributes")  # Conditional bonuses

# FactoryUpgrade
buff.find("FactoryUpgrade.ProductivityUpgrade")
buff.find("FactoryUpgrade.AdditionalOutput")
buff.find("FactoryUpgrade.ReplaceInputs")

# MaintenanceUpgrade
buff.find("MaintenanceUpgrade.MaintenanceFactorUpgrade")
buff.find("MaintenanceUpgrade.WorkforceMaintenanceFactorUpgrade")

# Other categories
# - ModuleOwnerUpgrade
# - CityInstitutionUpgrade (ResolverUnitCountUpgrade, etc.)
# - RecruitmentUpgrade
# - AqueductUpgrade
# - WarehouseUpgrade (StorageCapacityModifier)
# - IrrigationUpgrade
```

### ShipBuff Upgrade Categories

```python
# MovementUpgrade
buff.find("MovementUpgrade.BuffBaseSpeedUpgrade")
buff.find("MovementUpgrade.BuffReduceCargoImpactUpgrade")

# HealthUpgrade
buff.find("HealthUpgrade.BaseHealthUpgrade")
buff.find("HealthUpgrade.SelfHealUpgrade")

# TradeShipUpgrade
buff.find("TradeShipUpgrade.ActiveTradePriceInPercent")
buff.find("TradeShipUpgrade.LoadingSpeedUpgrade")

# UnitUpgrade
buff.find("UnitUpgrade.DiscoveryRadiusUpgrade")
buff.find("UnitUpgrade.DefenseUpgrade")

# ItemContainerUpgrade
buff.find("ItemContainerUpgrade.SlotCountUpgrade")  # Cargo slots
buff.find("ItemContainerUpgrade.SocketCountUpgrade")
```

### Special Cases

#### Functional Effects (Two-Level Indirection)

Some buffs reference additional effects:

```python
# Step 1: Get the functional effect from the buff
functional_effect_attr = buff.find("BuildingUpgrade.AdditionalFunctionalEffect")
if functional_effect_attr and functional_effect_attr():
    effect_asset = functional_effect_attr()

    # Step 2: Get buffs from the effect
    effect_cfg = effect_asset.Effect
    for nested_buff_entry in effect_cfg.Buffs:
        nested_buff = assets[nested_buff_entry.GUID.guid]
        # Process nested buff attributes
```

**Important**: Track visited effects to prevent infinite recursion!

#### Conditional Attributes

Items may have bonuses that only apply when specific needs are provided:

```python
need_attrs = buff.find("ResidenceUpgrade.NeedProvidedNeedAttributes")
if need_attrs:
    # Get the required need
    change_needs = need_attrs.ChangeNeedAttributesOf
    for item in change_needs:
        provided_product = item.ProvidedProduct()  # e.g., "Bardic Hearth"

    # Get the bonus attributes
    additional_attrs = need_attrs.AdditionalNeedAttributes
    # These apply only when the need is provided
```

## UI Text Mapping

### Overview

The UI Text Mapping system automatically associates localized display text and icons to dataset/enum values (like rarity, item niche, buff types) by loading configuration assets. This eliminates hardcoded text ID lookups.

**Key Benefits**:
- Zero manual text ID maintenance
- Automatic updates when game data changes
- Type-safe attribute access
- Configuration-driven (only 3 asset GUIDs needed)

### Accessing UI Text from Attributes

All `PrimitiveAttribute` instances with `Choice` data type automatically provide UI text via lazy-loaded properties:

```python
# Load assets
assets = AssetCache.load(config)
texts = assets.texts

# Get an item
item = assets[some_guid]

# Access UI text properties (lazy loaded on first access)
rarity_attr = item.Item.Rarity
rarity_value = rarity_attr()           # e.g., "Legendary"
rarity_text_id = rarity_attr.ui_text_id       # Localized text ID (negative number)
rarity_icon_guid = rarity_attr.ui_icon_guid   # Icon asset GUID

# Get the English text from TextCache
if rarity_text_id:
    text_obj = texts.elements.get(rarity_text_id)
    if text_obj:
        english_text = text_obj.values.get("english", "N/A")  # "Legendary"
```

### TextCache Access Pattern

The `texts` object is a `TextCache`, not a simple dictionary. Use this pattern:

```python
def get_text(text_id, texts):
    """Get English text for a text ID."""
    if text_id is None:
        return None
    text_obj = texts.elements.get(text_id)
    if text_obj:
        return text_obj.values.get("english", "N/A")
    return None

# Usage
rarity_text = get_text(rarity_attr.ui_text_id, texts)
```

**Important**: Do NOT use `texts["english"].get(text_id)` - this will fail with AttributeError.

### Variant Text

Some attributes have context-specific text variants (e.g., BuffConstructionCost has different text for shipyards vs recruitment):

```python
# Get buff attribute with variants
buff_attr = buff.find("BuildingUpgrade.ProductivityUpgrade")

# Access base text
base_text_id = buff_attr.ui_text_id

# Access variant text
variants = buff_attr.ui_text_variants  # dict[str, int] or None
if variants:
    shipyard_text_id = variants.get("ShipyardText")
    recruitment_text_id = variants.get("RecruitmentText")

    # Get the actual text
    shipyard_text = get_text(shipyard_text_id, texts)
```

### Direct UITextCache Access

You can also query the cache directly without using attributes:

```python
# Get the UI text cache
ui_cache = assets.properties.ui_text_cache

# Lookup by dataset and literal
mapping = ui_cache.get_ui_text("Rarity", "Legendary")
if mapping:
    text_id = mapping.text_id
    icon_guid = mapping.icon_guid
    variants = mapping.variants  # dict[str, int]

# Convenience methods
text_id = ui_cache.get_text_id("ItemNiche", "Finance")
icon_guid = ui_cache.get_icon_guid("ItemNiche", "Finance")

# Check cache size
num_mappings = len(ui_cache)  # e.g., 44 mappings
```

### Supported Datasets

The following datasets have automatic UI text mappings:

- **Rarity** (8 values): Common, Rare, Epic, Legendary, Unique, Artifact, QuestItem, CollectorsEdition
- **ItemNiche** (10 values): Finance, Religion, Research, Culture, Military, Nautics, Tourism, Special, Public, Trade
- **ItemAllocation** (3 values): Ship, Villa, None
- **Scope** (12 values): Local, Radius, Area, Session, Meta, Island, VisitorHarbour, Guild, Expedition, Trade, Shared, QuestGiver
- **BuffUpgradeType** (~100+ values): BuffProductivity, BuffSpeed, BuffHitpoints, BuffMaintenance, BuffLoadingSpeed, BuffAttackRange, etc.
- **NeedAttributeType** (8 values): Population, Money, Happiness, Health, FireSafety, Belief, Knowledge, Prestige
- **IncidentType** (6 values): Fire, Unrest, Disease, Inferno, Rebellion, Plague (uses special pattern via IncidentInfection assets)
- **NotSockableReason** (4 values): WrongAllocation, Duplicate, Exclusive, NoSpaceLeft
- **SocketExclusiveGroup**: Various exclusive socket groups
- **ItemType**: Specialist, Captains, etc.
- **BuffCategoryType**: Buff category names

### Example: Item Extraction with UI Text

```python
def extract_item_with_ui_text(item, assets):
    """Extract item data with UI text for all attributes."""
    texts = assets.texts
    result = {}

    # Basic info
    result["guid"] = item.guid
    result["name"] = item.text.values.get("english", "Unknown") if item.text else "N/A"

    # Rarity with UI text
    if hasattr(item.Item, "Rarity"):
        rarity_attr = item.Item.Rarity
        result["rarity_value"] = rarity_attr()
        result["rarity_text_id"] = rarity_attr.ui_text_id
        result["rarity_icon_guid"] = rarity_attr.ui_icon_guid

        # Get English text
        if rarity_attr.ui_text_id:
            text_obj = texts.elements.get(rarity_attr.ui_text_id)
            if text_obj:
                result["rarity_display"] = text_obj.values.get("english", "N/A")

    # Niche with UI text
    if hasattr(item.Item, "Niche"):
        niche_attr = item.Item.Niche
        result["niche_value"] = niche_attr()
        result["niche_text_id"] = niche_attr.ui_text_id

        # Get English text
        if niche_attr.ui_text_id:
            text_obj = texts.elements.get(niche_attr.ui_text_id)
            if text_obj:
                result["niche_display"] = text_obj.values.get("english", "N/A")

    # Allocation with UI text
    if hasattr(item.Item, "Allocation"):
        alloc_attr = item.Item.Allocation
        result["allocation_value"] = alloc_attr()
        result["allocation_text_id"] = alloc_attr.ui_text_id

        # Get English text
        if alloc_attr.ui_text_id:
            text_obj = texts.elements.get(alloc_attr.ui_text_id)
            if text_obj:
                result["allocation_display"] = text_obj.values.get("english", "N/A")

    return result

# Usage
items = assets.templates["Item"].assets
for item in items:
    data = extract_item_with_ui_text(item, assets)
    print(f"{data['name']}: {data.get('rarity_display')} {data.get('niche_display')}")
```

### Buff Attributes with UI Text

When extracting buff attributes, UI text is automatically available:

```python
# Get buff from item
effect = item.Effect
for buff_entry in effect.Buffs:
    buff_asset = assets[buff_entry.GUID.guid]

    # Check productivity upgrade
    prod_attr = buff.find("FactoryUpgrade.ProductivityUpgrade")
    if prod_attr and prod_attr():
        # The attribute has a dataset reference
        if hasattr(prod_attr, 'meta') and prod_attr.meta.dataset:
            dataset_name = prod_attr.meta.dataset.name  # "BuffUpgradeType"
            buff_type = prod_attr()  # "BuffProductivity"

            # Get UI text
            text_id = prod_attr.ui_text_id
            icon_guid = prod_attr.ui_icon_guid

            if text_id:
                text_obj = texts.elements.get(text_id)
                if text_obj:
                    buff_display = text_obj.values.get("english")  # "Productivity"
```

### NeedAttributeType Example

When working with population attributes or boost conditions, NeedAttributeType mappings provide localized text and icons:

```python
# Access NeedAttributeType UI text
ui_cache = assets.properties.ui_text_cache

# Get mapping for a need attribute
mapping = ui_cache.get_ui_text("NeedAttributeType", "Health")
if mapping:
    text = mapping.text          # Text object with "Health" in all languages
    icon = mapping.icon          # FileNameAttribute for the health icon
    english = text.values.get("english")  # "Health"

# Example: Processing AdditionalNeedAttributes from a buff
buff_dict = buff.find("BuildingUpgrade.AdditionalAttributes")
if buff_dict and buff_dict.value:
    for literal, attr in buff_dict.value.items():
        # literal is a NeedAttributeType value (e.g., "Happiness", "Health")
        mapping = ui_cache.get_ui_text("NeedAttributeType", literal)
        if mapping:
            attr_name = mapping.text.values.get("english")  # Localized name
            attr_icon = mapping.icon                        # Icon for display
            value = attr.AmountOrPercent()                  # Numeric value
            print(f"{attr_name}: {value}")
```

### Configuration

The UI text mappings are loaded from three configuration assets:

1. **ItemInfotipTextFeature (GUID 142928)**: Buff upgrade types, need attribute types, and their variants
2. **ItemBalancing (GUID 6000017)**: Item properties (rarity, niche, scope, allocation)
3. **BuffConfig (GUID 52456)**: Buff category names

**Note**: IncidentType uses a special pattern that loads text from IncidentInfection template assets rather than configuration assets.

To add support for new datasets, edit `CONFIG_ASSETS` in `assetextractor/parsing/core/uitext.py`:

```python
CONFIG_ASSETS = {
    142928: {
        "path": "ItemInfotipTextFeature.BuffUpgradeTextAndIcons",
        "mappings": {
            "BuffUpgradeType": "{}.Text",  # {} is replaced with literal value
            "NeedAttributeType": "BuffAdditionalNeedAttributes.Attributes.{}.Text",
        },
        "variants": {
            "BuffConstructionCost": ["ShipyardText", "RecruitmentText"],
        },
    },
}
```

### Best Practices

1. **Use the helper function** - Create a `get_text()` helper to handle TextCache access
2. **Check for None** - Always check if `ui_text_id` is not None before accessing TextCache
3. **Cache the texts object** - Keep a reference to `assets.texts` instead of accessing it repeatedly
4. **Lazy loading** - UI text is only loaded on first property access (performance optimization)
5. **Graceful degradation** - If UI text is unavailable, properties return `None` (no crashes)
6. **Type-safe access** - Use `.ui_text_id` properties instead of manual cache lookups
7. **Variant awareness** - Check `.ui_text_variants` for context-specific text

### Testing

See `test_uitext.ipynb` for comprehensive examples including:
1. Direct cache lookups for all supported datasets
2. Attribute property access patterns
3. Variant text handling
4. Coverage statistics (% of dataset values mapped)
5. Integration with item extraction

## Boost Conditions (ItemWithBoost)

### Understanding Boost Conditions

Items with the **ItemWithBoost** template can have conditional boosts that activate when specific requirements are met. These conditions are found at:

```python
condition = item_asset.find("ItemWithBoost.BoostCondition.PreConditionList.Condition")
```

When the condition is met, the item's base buffs are replaced by enhanced **BoostBuffs**:

```python
# Base buffs (always active)
base_buffs = item_asset.Effect.Buffs

# Boost buffs (replace base when condition is met)
boost_buffs = item_asset.find("ItemWithBoost.BoostBuffs")
```

### Condition Structure

All conditions have a base `Condition` property with metadata, plus one or more specific condition types:

```python
# Base metadata (usually default values)
condition.Condition.SubConditionCompletionOrder()  # "Parallel" or "Linear"
condition.Condition.IsOptional()                   # Usually False
condition.Condition.CountForAchievementProgress()  # Usually True

# Specific condition type (one or more)
condition.ConditionObjectCount         # Building/object count requirement
condition.ConditionDominantPatron      # Patron deity requirement
condition.ConditionPlayerCounter       # Various game statistics
# ... many other types
```

### Common Condition Types

#### ConditionAlwaysTrue

No requirements - boost is always active.

```python
if hasattr(condition, 'ConditionAlwaysTrue'):
    # Check if there are other conditions besides AlwaysTrue
    has_other = any(hasattr(condition, ct) for ct in other_condition_types)
    if not has_other:
        return "Always active"
```

#### ConditionObjectCount

Requires a certain count of buildings or objects.

```python
amount = condition.ConditionObjectCount.Amount()
comparison_op = condition.ConditionObjectCount.ComparisonOp()  # 0, "AtLeast", "AtMost", etc.
obj_guid = condition.ObjectFilter.ObjectGUID()  # The building type

# Result: "Residences >= 600"
```

**Note**: The `ObjectFilter` is a sibling to `ConditionObjectCount`, not nested within it.

#### ConditionPlayerCounter

Requires a specific value for a named counter or building context.

```python
player_counter = condition.ConditionPlayerCounter.PlayerCounter()  # Named counter (e.g., "NavalStrength")
context = condition.ConditionPlayerCounter.Context()               # Or building reference
comparison_op = condition.ConditionPlayerCounter.ComparisonOp()
counter_amount = condition.ConditionPlayerCounter.CounterAmount()

# Examples:
# - "NavalStrength <= 5000" (named counter)
# - "Amphitheatre >= 1" (building context)
```

**PlayerCounter Literals** (85 types):
- Population: `PopulationTotal`, `PopulationByLevel`, `PopulationByGroup`
- Economy: `MoneyBalance`, `TradeProductBought`, `TradeProductSold`, `GoodsInStock`
- Military: `NavalStrength`, `ArmyStrength`, `DefenseStrength`
- Buildings: `ObjectCount`, `BuildingsMoved`, `BuildingsDemolished`
- Diplomacy: `ParticipantDefeated`, `PirateDefeated`
- And 70+ more...

#### ConditionDominantPatron / ConditionReligion

Requires a specific patron deity to be dominant.

```python
# ConditionDominantPatron (older style)
patron_guid = condition.ConditionDominantPatron.PatronGUID()

# ConditionReligion (newer style)
religion_asset = condition.ConditionReligion.ReligionAsset()

# Result: "Patron: Mars"
```

#### ConditionNeedAttributeCounter

Requires a minimum value of a population attribute.

```python
need_type = condition.ConditionNeedAttributeCounter.NeedAttributeType()  # "Health", "Happiness", etc.
amount = condition.ConditionNeedAttributeCounter.NeedAttributeAmount()

# Result: "Health >= 1000"
```

#### ConditionActiveEmperor

Requires a specific emperor to be active.

```python
emperor = condition.ConditionActiveEmperor.EmperorParticipant()

# Result: "Emperor: Gnaeus Firmius Calidus"
```

#### ConditionDiplomacyState

Requires a specific diplomatic relationship with a faction.

```python
profile2 = condition.ConditionDiplomacyState.Profile2()         # The faction
desired_state = condition.ConditionDiplomacyState.DesiredState()  # "Alliance", "Peace", "War", etc.

# Result: "Diplomacy with Tarragon: Alliance"
```

#### ConditionTradeRouteCount

Requires a minimum number of active trade routes.

```python
count = condition.ConditionTradeRouteCount.TradeRouteCount()
count_op = condition.ConditionTradeRouteCount.CountComparisonOp()

# Result: "Trade routes >= 15"
```

#### ConditionItemUsed

Requires a specific number of items to be equipped.

```python
item_amount = condition.ConditionItemUsed.ItemAmount()
target_item = condition.ConditionItemUsed.TargetItem()  # Often an AssetPool of items

# Result: "4 items equipped"
```

#### Other Condition Types

Less common but still important:

- **ConditionMonumentEventsActive** - Monument events must be active
- **ConditionEmperorRelation** - Specific emperor relationship required
- **ConditionWarState** - Must be at war
- **ConditionInStorage** - Specific items must be in storage
- **ConditionLocationFilter** - Geographic/regional requirements
- **ConditionCounterProps** - Counter-based comparisons
- **ConditionPropsComparable** - Property comparisons

### Comparison Operators

Many conditions use comparison operators with these values:

```python
comparison_map = {
    0: ">=",           # AtLeast (default)
    "AtLeast": ">=",
    "AtMost": "<=",
    "LessThan": "<",
    "GreaterThan": ">",
    "Equal": "="
}

op_symbol = comparison_map.get(condition.ComparisonOp(), ">=")
```

### Parsing Pattern

Use a cascade of try-except blocks to check each condition type:

```python
def extract_boost_condition(item_asset: Asset) -> str:
    try:
        condition_attr = item_asset.find("ItemWithBoost.BoostCondition.PreConditionList.Condition")
        if not condition_attr:
            return ""

        condition = condition_attr

        # Try ConditionAlwaysTrue first
        try:
            if hasattr(condition, 'ConditionAlwaysTrue'):
                # Check if there are other conditions
                has_other = any(hasattr(condition, ct) for ct in [
                    'ConditionObjectCount', 'ConditionPlayerCounter', ...
                ])
                if not has_other:
                    return "Always active"
        except:
            pass

        # Try ConditionObjectCount
        try:
            if hasattr(condition, 'ConditionObjectCount'):
                amount = condition.ConditionObjectCount.Amount()
                obj_guid = condition.ObjectFilter.ObjectGUID()
                # Build condition string...
                return result
        except:
            pass

        # Try other condition types...

        # Fallback for unhandled conditions
        return "Boost condition active"
    except:
        return ""
```

### Multiple Conditions

Some items have multiple conditions that must all be satisfied (SubConditionCompletionOrder: "Parallel"):

```python
# Example: Item requires both a patron AND a building count
condition.ConditionReligion           # Patron: Mars
condition.ConditionObjectCount        # Baths >= 3
condition.ConditionAlwaysTrue         # Always present as marker
```

In these cases, you may want to combine the conditions into a single string or return a list.

### Best Practices

1. **Check ConditionAlwaysTrue last** - It's often present alongside other conditions as a marker
2. **Use hasattr before accessing** - Not all condition types are present
3. **Handle ObjectFilter separately** - It's a sibling property, not nested
4. **Map comparison operators** - Convert integer codes to symbols for readability
5. **Format amounts as integers** - When possible, show "600" not "600.0"
6. **Get English names for references** - Use `get_english_name()` for buildings, patrons, etc.
7. **Implement logging for unknowns** - Add debug output for unhandled condition types
8. **Track visited conditions** - Prevent infinite loops if conditions reference each other

## Finding Item Sources

Items can be obtained from multiple sources:

### 1. Traders

```python
if "Participant 3rdParty" in assets.templates:
    for trader in assets.templates["Participant 3rdParty"].assets:
        offered_items = trader.find("Trader.OfferedItems")
        if offered_items and offered_items():
            reward_pool = offered_items()
            # This reward pool contains items offered by this trader
            trader_name = get_english_name(trader)
```

### 2. Tech Tree Research

Research rewards are found in the Tech template:

```python
if "Tech" in assets.templates:
    for tech in assets.templates["Tech"].assets:
        rewards = tech.find("Tech.Rewards.Items")
        if rewards:
            for item_entry in rewards:
                item_asset = item_entry.ItemAsset()
                # This is either an Item or a RewardPool

                # Get the research name
                tech_name = tech.find("Tech.TechName")()
                # Or: tech.find("Tech.ResearchableTechName")()
```

**Tech Properties**:
- `Tech.IsRepeatable()` - Whether the tech can be researched multiple times
- `Tech.KnowledgeNeeded()` - Research cost
- `Tech.TechName()` - Localized text key for the tech name

### 3. Quest Objectives

```python
if "Objective" in assets.templates:
    for objective in assets.templates["Objective"].assets:
        reward_assets = objective.find("Reward.RewardAssets")
        if reward_assets:
            for reward_entry in reward_assets:
                reward = reward_entry.Reward()
                # This is a RewardPool
```

### 4. Expeditions

```python
if "Expedition" in assets.templates:
    for expedition in assets.templates["Expedition"].assets:
        expedition_rewards = expedition.find("Expedition.ExpeditionReward")
        if expedition_rewards:
            for reward_entry in expedition_rewards:
                reward_pool = reward_entry.RewardPool()
```

## Asset Pools

### Understanding Pools

There are two main pool types:

1. **RewardPool** - Contains items with weights for random selection
2. **AssetPool** - Generic container for grouping assets

### RewardPool Structure

```python
pool = assets[pool_guid]
items_pool = pool.RewardPool.ItemsPool

for item_entry in items_pool:
    item_link = item_entry.ItemLink()  # Can be Item or another RewardPool
    weight = item_entry.Weight()        # Selection probability
    min_amount = item_entry.MinAmount()
    max_amount = item_entry.MaxAmount()
```

**Properties**:
- `GenerateUniqueRewards()` - If true, won't generate duplicates
- `IgnoreUnlocks()` - Whether locked items can be rewarded

### Flattening Pools Recursively

Pools can contain other pools. Use recursion to flatten:

```python
def flatten_pool(pool):
    """Recursively flatten an AssetPool into individual asset GUIDs."""
    if pool is None:
        return []

    if "AssetPool" not in pool.template.name:
        return [pool.guid]

    result = []
    for entry in pool.AssetPool.AssetList:
        if entry.Asset():
            result.extend(flatten_pool(entry.Asset()))
    return result
```

### Building a Reverse Index

To find which pools contain a specific item:

```python
def build_reward_pool_index(assets):
    """Map items to all RewardPools that contain them."""
    item_to_pools = {}

    for template_name in ["RewardPool", "RegionRewardPool"]:
        if template_name not in assets.templates:
            continue

        for pool in assets.templates[template_name].assets:
            items_pool = pool.RewardPool.ItemsPool
            if items_pool:
                for item_entry in items_pool:
                    item_link = item_entry.ItemLink()
                    if item_link:
                        if item_link.guid not in item_to_pools:
                            item_to_pools[item_link.guid] = set()
                        item_to_pools[item_link.guid].add(pool.guid)

    return item_to_pools
```

### Resolving Pool Chains

An item may be in pool A, which is in pool B, which is referenced by a trader:

```python
def resolve_pool_chain(item_guid, item_to_pools, visited=None):
    """Find all pools that directly or indirectly contain this item."""
    if visited is None:
        visited = set()

    if item_guid in visited:
        return set()

    visited.add(item_guid)
    result = set()

    if item_guid in item_to_pools:
        for pool_guid in item_to_pools[item_guid]:
            result.add(pool_guid)
            # Recursively find pools containing this pool
            result.update(resolve_pool_chain(pool_guid, item_to_pools, visited))

    return result
```

## Common Patterns

### Template Names

- **Item** / **ItemWithBoost** - All items (specialists, captains, etc.)
- **BuildingBuff** - Building modification buffs
- **ShipBuff** - Ship modification buffs
- **Tech** - Tech tree research
- **Participant 3rdParty** - Traders
- **Objective** - Quest objectives
- **Expedition** - Expedition events
- **RewardPool** / **RegionRewardPool** - Item reward containers
- **AssetPool** - Generic asset grouping

### Safe Attribute Access

Always use try-except when accessing attributes:

```python
try:
    value = asset.find("Path.To.Attribute")()
    if value and value != 0:
        # Process value
except:
    pass
```

### Checking for Specific Values

```python
# Boolean checks
if asset.find("SomePath.BooleanValue")():
    # True case

# Numeric comparisons
attr = asset.find("SomePath.NumericValue")()
if attr and attr != 0:
    # Non-zero value

# Default value checks (for percentages)
attr = asset.find("SomePath.PercentValue")()
if attr and attr != 100:
    # Modified from default 100%
```

### Iterating Lists

```python
# Check if list exists and has items
attr = asset.find("SomePath.ListAttribute")
if attr and len(attr._value_list) > 0:
    for item in attr:
        # Process each item
```

### Formatting Numbers

```python
# Format as integer when appropriate
value = attr()
if value == int(value):
    formatted = f"{int(value)}"
else:
    formatted = f"{value}"

# Add sign for modifiers
sign = "+" if value > 0 else ""
formatted = f"{sign}{value}"
```

## Best Practices

1. **Always use localized text** for display names instead of internal names
2. **Never hardcode GUIDs** - they change between game versions
3. **Use template names and paths** to find assets
4. **Implement cycle detection** when traversing recursive structures (pools, functional effects)
5. **Handle missing attributes gracefully** with try-except blocks
6. **Build indices** for reverse lookups when needed (e.g., item → pools → sources)
7. **Check list lengths** before iterating with `len(attr._value_list) > 0`
8. **Use fallbacks** for missing localized text

## Example: Complete Item Extraction

See `assetextractor/conversion/statistics/extract_items.ipynb` for a complete working example that:

1. Extracts all items with their attributes
2. Resolves buff chains (including functional effects)
3. Handles ItemWithBoost conditions (patron, building count, diplomacy, etc.)
4. Extracts both base and boost buffs
5. Finds all sources (traders, research, quests, expeditions)
6. Handles both BuildingBuff and ShipBuff types
7. Exports to CSV with human-readable names

The notebook demonstrates all concepts in this guide in a practical, reusable implementation.
