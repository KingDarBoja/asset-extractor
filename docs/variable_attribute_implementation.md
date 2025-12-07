# Variable Attribute Implementation

## Overview

Implemented support for "Variable" data type attributes in the asset parsing system. Variables are placeholders that contain a variable name instead of a concrete value, used for dynamic references in the game's asset system.

## Changes Made

### 1. Core Implementation (`assetextractor/parsing/core/attributes.py`)

#### Variable Mixin Class (lines 184-193)
- Cleaned up the `Variable` class to be a proper mixin interface
- Added comprehensive docstring explaining the purpose
- Removed unused `__init__` method that was never called
- Documented `is_variable` and `variable_name` attributes in docstring

#### PrimitiveAttribute Class (line 268)
- **Made `PrimitiveAttribute` inherit from `Variable` mixin**
- Already had `is_variable` and `variable_name` initialization in `__init__`
- Added new `resolve_inheritance` method (lines 339-357) to properly handle variable inheritance:
  - Returns early if attribute is a variable (doesn't inherit concrete values)
  - Inherits variable name from default if needed
  - Otherwise performs normal value inheritance

#### ReferenceAttribute Class
- Already inherited from `Variable` (line 787)
- Updated `resolve_inheritance` method (lines 823-838) to handle variables:
  - Returns early if attribute is a variable
  - Inherits variable name from default when GUID is 0
  - Otherwise performs normal reference inheritance

#### QuestAttribute Class (line 871)
- **Fixed missing parameter bug**: Added `is_variable=False` to `super().__init__()` call
- This was a pre-existing bug exposed by the Variable implementation

### 2. Asset Browser HTML Templates

#### asset.html
- **ReferenceAttribute rendering** (lines 36-43):
  - Added check for `node.is_variable`
  - Displays `variable_name (Variable)` in italics if it's a variable
  - Otherwise shows normal reference link

- **Simple attribute rendering** (lines 62-66):
  - Added check for `is_variable` attribute
  - Displays `name: variable_name (Variable)` if it's a variable
  - Otherwise shows normal attribute value

#### template.html
- **ReferenceAttribute rendering** (lines 18-24):
  - Added check for `node.is_variable`
  - Displays `variable_name (Variable)` in italics if it's a variable

- **Simple attribute rendering** (lines 40-44):
  - Added check for `is_variable` attribute
  - Displays `name: variable_name (Variable)` if it's a variable

### 3. Testing

Created `tests/debugging/test_variable_attributes.py`:
- Searches through assets to find Variable attributes
- Successfully found several examples in quest-related assets
- Confirms proper initialization and display

## How Variables Work

### XML Structure

Variables appear in XML with an `<IsVariable>` element:

```xml
<Asset>
  <IsVariable>1</IsVariable>
  <Value>DeliveryGoods02</Value>
</Asset>
```

Or for primitive types:
```xml
<SomeAttribute>
  <IsVariable>1</IsVariable>
  <Value>VariableName</Value>
</SomeAttribute>
```

### Attribute Factory Processing

The `AttributeFactory.create()` method (lines 1534-1546):
1. Detects `DataType="Variable"`
2. Checks for `<IsVariable>` element
3. Extracts the actual type from `VariableType` (e.g., "Asset", "String")
4. Creates appropriate attribute (PrimitiveAttribute or ReferenceAttribute) with `is_variable=True`

### Initialization

**For PrimitiveAttribute** (lines 295-297):
- Sets `self.variable_name = self._value_text`
- Sets `self.value = None` (implicitly, set in parent `Attribute.__init__`)
- Returns early without processing as concrete value

**For ReferenceAttribute** (lines 796-799):
- Sets `self.variable_name = self._value_text`
- Sets `self.guid = 0`
- Sets `self.value = None`

### Inheritance Resolution

Variables have special inheritance behavior:

1. **If the attribute is a variable**: Don't inherit concrete values (we have a variable name)
2. **If the attribute is not set and default is a variable**: Inherit the variable name
3. **Otherwise**: Perform normal value/reference inheritance

This ensures variables are preserved through the inheritance chain and not accidentally replaced with concrete values.

## Examples Found in Game Data

The test script found several Variable attributes in quest-related assets:

```
Asset: 121721 - INHERITANCE BASE Quest Entry Declare War
Path: 121721.QuestEntry.Value
Variable Name: ActiveEmperor
Meta Data Type: Variable
Variable Type: Asset
```

These represent dynamic references that are resolved at runtime based on game state (e.g., which emperor is currently active).

## Benefits

1. **Type Safety**: Variables are properly typed and checked
2. **Clear Display**: Users can see when a value is a variable placeholder vs. a concrete reference
3. **Proper Inheritance**: Variables are preserved through the inheritance chain
4. **Consistent Handling**: Both PrimitiveAttribute and ReferenceAttribute handle variables the same way
5. **Future Proof**: Easy to extend for new variable types

## Testing

Run the test script to verify the implementation:

```bash
uv run python -c "import sys; sys.path.insert(0, '.'); exec(open('tests/debugging/test_variable_attributes.py').read())"
```

Type checking passes with 0 errors:
```bash
uv run pyright assetextractor/parsing/core/attributes.py
```

## Visual Representation

In the HTML asset browser, variables now appear as:

**For References:**
```
QuestEntry.Value: ActiveEmperor (Variable)
```

**For Primitives:**
```
SomeAttribute: VariableName (Variable)
```

This makes it immediately clear which values are dynamic placeholders vs. concrete values.
