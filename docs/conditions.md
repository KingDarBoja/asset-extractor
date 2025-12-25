# Anno 117 Boost Conditions - Technical Documentation

## Overview

Items with the **ItemWithBoost** template have conditional bonuses that activate when specific requirements are met. This document describes how boost conditions are structured, parsed, and formatted for display.

## Structure

Boost conditions are found at:
```
ItemWithBoost.BoostCondition.PreConditionList.Condition
```

When the condition is satisfied:
- **Base buffs** (`Effect.Buffs`) are replaced by **Boost buffs** (`ItemWithBoost.BoostBuffs`)
- The boosted buffs typically provide stronger bonuses

## Condition Types

### 1. ConditionAlwaysTrue

**Description**: No requirements - boost is always active.

**Output**: `"Always active"`

**Logic**:
- Check if `ConditionAlwaysTrue` exists AND no other condition types are present
- If other condition types exist alongside it, process those instead

### 2. ConditionObjectCount (with Matcher Support)

**Description**: Requires a certain count of buildings/objects, optionally with ship module requirements.

**Basic Format**: `"{Building/Ship} {operator} {amount}"`

**Examples**:
- `"Residences >= 600"`
- `"Amphitheatre >= 1 (Global)"`

#### Ship Module Requirements (Matcher)

When a Matcher reference exists at `ObjectFilter.Matcher`, parse the `MatcherCriterionShipConfiguration`:

**Matcher Attributes**:
- `RequiredModuleCount`: Total module count requirement
- `RequiredMilitaryModuleCount`: Military module count requirement
- `ShipConfiguration`: Specific ship type requirement (e.g., Flagship)
- `Negate`: Invert the condition (rarely used)

**Formatting Rules**:
1. **Military Modules**: `"At least {count} military modules"`
   - Example: `"At least 2 military modules"`

2. **Total Modules**: `"At least {count} modules on the ship"`
   - Example: `"At least 3 modules on the ship"`

3. **Ship Configuration**: `"Must be socketed into {ship_name}"`
   - Example: `"Must be socketed into the flagship"`
   - Used when `ShipConfiguration` is set

4. **Negated**: `"NOT (...)"`
   - Wraps the condition if `Negate` is true

**Implementation Note**: When a Matcher condition is present, return it directly and skip the standard object count formatting.

### 3. ConditionNeedAttributeCounter

**Description**: Requires a minimum value of a population attribute.

**Format**: `"{AttributeType} {operator} {amount} [{suffix}]"`

**Attributes**:
- `NeedAttributeType`: Health, Happiness, Prestige, Population, etc.
- `NeedAttributeAmount`: Required threshold
- `ComparisonOpType`: Comparison operator (AtLeast, AtMost, Equal, etc.)
- `UseGlobalSum`: Whether the check is global or island-specific

**Examples**:
- `"Health >= 1000"`
- `"Prestige >= 10000 (Global)"`
- `"All Need Attributes >= 500"` (when NeedAttributeType is 0)

### 4. ConditionReligion / ConditionDominantPatron

**Description**: Requires a specific patron deity to be active.

**Format**: `"Patron: {patron_name}"` or `"Dominant Patron: {patron_name}"`

**Special Case**: If `ReligionAsset` is None (no patron):
- Output: `"No patron god selected on this island"` (localized text ID: -6910831837642126966)

**Examples**:
- `"Patron: Mars"`
- `"Dominant Patron: Diana"`
- `"No patron god selected on this island"`

### 5. ConditionPlayerCounter

**Description**: Requires a specific value for a named counter or building context.

**Format**: `"{Counter/Building} {operator} {amount} ({scope})"`

**Attributes**:
- `PlayerCounter`: Named counter (85 types: PopulationTotal, NavalStrength, MoneyBalance, etc.)
- `Context`: Building reference (alternative to PlayerCounter)
- `ComparisonOp`: Comparison operator
- `CounterAmount`: Threshold value
- `CounterScope`: Global, Island, Session

**Examples**:
- `"NavalStrength <= 5000 (Global)"`
- `"Amphitheatre >= 1 (Global)"`
- `"MoneyBalance >= 50000 (Island)"`

### 6. ConditionActiveEmperor

**Description**: Requires a specific emperor to be active.

**Format**: `"Emperor: {emperor_name}"`

**Example**: `"Emperor: Gnaeus Firmius Calidus"`

### 7. ConditionEmperorRelation

**Description**: Requires specific reputation zone or special state with the emperor.

**Format**:
- Zones: `"Reputation: {zone1} or {zone2}"`
- States: `"Emperor State: {state1} or {state2}"`
- Combined: Both conditions joined with `"; "`

**Reputation Zones** (loaded from asset 38180):
- `HostileZone` → "Threat"
- `UnrulyZone` → "Troublemaker"
- `CasualZone` → "Neutral"
- `EffortZone` → "Supporter"
- `ChallengeZone` → "Favourite"

**Special States** (loaded from asset 38180):
- `Rebellion`, `RebellionPending`, etc.

**Examples**:
- `"Reputation: Supporter or Favourite"`
- `"Emperor State: Rebellion or RebellionPending"`
- `"Reputation: Neutral; Emperor State: Trade"`

**Fallback**: `"Emperor relation required"` (if no zones/states specified)

### 8. ConditionDiplomacyState

**Description**: Requires a specific diplomatic relationship with a faction.

**Format**: `"Diplomacy with {faction}: {state}"`

**Attributes**:
- `Profile2`: The target faction
- `DesiredState`: Alliance, Peace, War, Trade, etc.

**Example**: `"Diplomacy with Tarragon: Alliance"`

### 9. ConditionTradeRouteCount

**Description**: Requires a minimum number of active trade routes.

**Format**: `"Trade routes {operator} {count}"`

**Note**: "Trade routes" text is localized (text ID: -6916519845325395691)

**Example**: `"Trade routes >= 15"`

### 10. ConditionItemUsed

**Description**: Requires a specific number of items to be equipped.

**Format**: `"{count} items equipped"`

**Example**: `"4 items equipped"`

### 11. ConditionMonumentEventsActive

**Description**: Monument events must be active.

**Output**: `"Monument events active"`

### 12. ConditionWarState

**Description**: Must be at war.

**Output**: `"At war"`

### 13. ConditionInStorage

**Description**: Specific items must be in storage.

**Output**: `"Items in storage"`

## Comparison Operators

Used across multiple condition types:

| Value | Operator | Symbol |
|-------|----------|--------|
| 0 (default) | AtLeast | >= |
| AtLeast | AtLeast | >= |
| AtMost | AtMost | <= |
| LessThan | LessThan | < |
| GreaterThan | GreaterThan | > |
| Equal | Equal | = |

## Formatting Helper

The `format_comparison_condition()` function standardizes comparison formatting:

```python
def format_comparison_condition(subject: str, amount: float, comparison_op, suffix: str = "") -> str:
    """Format a comparison condition consistently.

    Args:
        subject: The thing being compared (e.g., "Population")
        amount: The numeric threshold
        comparison_op: The operator (0, "AtLeast", etc.)
        suffix: Optional suffix like "(Global)"

    Returns:
        Formatted string (e.g., "Population >= 5000 (Global)")
    """
```

**Usage Examples**:
- `format_comparison_condition("Health", 1000, "AtLeast")` → `"Health >= 1000"`
- `format_comparison_condition("Trade routes", 15, 0, "(Global)")` → `"Trade routes >= 15 (Global)"`

## Implementation Notes

### Error Handling

Each condition type is wrapped in a try-except block:
```python
try:
    if hasattr(condition, 'ConditionTypeX'):
        # Parse and return formatted string
except:
    pass  # Silently skip this condition type
```

This ensures that parsing errors in one condition type don't affect others.

### Fallback Behavior

If no recognized condition is found:
- Return `"Boost condition active"`
- This indicates a boost exists but the condition couldn't be parsed

### Condition Priority

Conditions are checked in order:
1. ConditionAlwaysTrue (if alone)
2. ConditionObjectCount (with Matcher support)
3. ConditionNeedAttributeCounter
4. ConditionDominantPatron / ConditionReligion
5. ConditionPlayerCounter
6. ConditionActiveEmperor
7. ConditionEmperorRelation
8. ConditionDiplomacyState
9. ConditionTradeRouteCount
10. ConditionItemUsed
11. ConditionMonumentEventsActive
12. ConditionWarState
13. ConditionInStorage

**Return Early**: Once a condition is successfully parsed, return immediately (don't check remaining types).

### Localized Text

Several condition types use localized text IDs:
- **No Patron**: -6910831837642126966
- **Trade Routes**: -6916519845325395691

Load these via `texts.get(text_id)()` for multi-language support.

### Reputation Data Loading

Reputation zones and special states are loaded once from asset 38180:
```python
REPUTATION_ZONES, REPUTATION_SPECIAL_STATES = load_reputation_zones(assets)
```

These mappings convert internal names to localized display names.

## Examples

### Example 1: Ship Captain with Module Requirement

**Item**: Calydon Deiranira, Arcadian Archer (GUID 71585)

**Condition Structure**:
```
ConditionObjectCount:
  Amount: 1
  ComparisonOp: AtLeast
  ObjectFilter:
    ObjectGUID: 38995 (Ships)
    Matcher: 112041
      MatcherCriterionShipConfiguration:
        RequiredMilitaryModuleCount: 2
```

**Output**: `"At least 2 military modules"`

### Example 2: Population Requirement

**Condition Structure**:
```
ConditionNeedAttributeCounter:
  NeedAttributeType: Health
  NeedAttributeAmount: 1000
  ComparisonOpType: AtLeast
  UseGlobalSum: False
```

**Output**: `"Health >= 1000"`

### Example 3: Reputation Zones

**Condition Structure**:
```
ConditionEmperorRelation:
  AllowedZones: "EffortZone;ChallengeZone"
```

**Output**: `"Reputation: Supporter or Favourite"`

### Example 4: Building Count

**Condition Structure**:
```
ConditionObjectCount:
  Amount: 600
  ComparisonOp: AtLeast
  ObjectFilter:
    ObjectGUID: <residence_guid>
```

**Output**: `"Residences >= 600"`

### Example 5: No Patron

**Condition Structure**:
```
ConditionReligion:
  ReligionAsset: None
```

**Output**: `"No patron god selected on this island"`

## Testing

### Verification Items

Test with these representative items:
- **71585**: Ship module requirement (military modules)
- **42617**: Ship module requirement (total modules)
- **71550**: Ship configuration requirement (flagship)
- **107554**: Reputation zones
- **107337**: Special states
- **41350**: Health requirement
- **41351**: Prestige requirement

### Comparison with Manual Corrections

The implementation is validated against `results/tables/items_english_v1.3_manual_corrections.csv`, which contains manually verified boost conditions for all items.

Run `tests/integration/test_item_extraction_accuracy.py` to check for discrepancies.

## Future Enhancements

Potential improvements:
1. **Multiple Conditions**: Some items may have compound conditions (AND/OR logic)
2. **SubConditions**: Parse `Condition.SubConditions` if present
3. **Special Ship Types**: Handle specific ship configurations beyond Flagship
4. **Additional Matchers**: Support other Matcher criterion types beyond ShipConfiguration
5. **Localization**: Ensure all condition text is fully localized

## Related Files

- **Implementation**: `assetextractor/conversion/statistics/extract_items.ipynb` (Cell 6)
- **Tests**: `tests/integration/test_item_extraction_accuracy.py`
- **Manual Corrections**: `results/tables/items_english_v1.3_manual_corrections.csv`
- **Asset Browser**: Shows conditions in HTML format at `C:/temp/assetbrowser-2025-12-08/`
