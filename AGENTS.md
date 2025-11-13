# Asset Extractor Guide for AI Agents
@CLAUDE.md

This guide documents how to navigate and extract data from Anno 117's asset structure using the asset-extractor library.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Item Structure](#item-structure)
3. [Buff System](#buff-system)
4. [Boost Conditions (ItemWithBoost)](#boost-conditions-itemwithboost)
5. [Finding Item Sources](#finding-item-sources)
6. [Asset Pools](#asset-pools)
7. [Common Patterns](#common-patterns)

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
