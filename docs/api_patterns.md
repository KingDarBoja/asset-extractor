# Common API Patterns

## find() vs find_value()

Both are defined on `NamedElement` and available on `Asset`, `Property`, `ListItem`, and all `Attribute` subclasses.

- **`find(path)`** — returns the `NamedElement` at the dotted path or `None`. Use when you need the attribute object (metadata, iteration, `.ui_text_id`, `.value`, etc.).
- **`find_value(path)`** — calls `find()` then returns the resolved scalar (`element()` if callable, else raw text). Use as a one-liner when you only need the value.

| Situation | Use |
|---|---|
| Need metadata / iteration / icon | `find()` |
| Quick scalar read | `find_value()` |
| Iterating a `ListAttribute` | `find()` then iterate |

Prefer `find_value` over try/except — bare excepts hide real errors.

## Value checks

```python
if asset.find_value("Path.BoolValue"):           # boolean
value = asset.find_value("Path.NumericValue")
if value and value != 0: ...                     # nonzero
if value and value != 100: ...                   # modified percentage
```

## Iterating lists

```python
attr = asset.find("Path.ListAttribute")
if attr and len(attr._value_list) > 0:
    for item in attr: ...
```

## Number formatting

```python
formatted = f"{int(v)}" if v == int(v) else f"{v}"
signed = ("+" if v > 0 else "") + formatted
```

## Localized names

```python
def get_english_name(asset):
    if asset.text and "english" in asset.text.values:
        return asset.text.values["english"]
    return asset.find_value("Standard.Name")
```

## Template names worth knowing

`Item` / `ItemWithBoost`, `BuildingBuff`, `ShipBuff`, `Tech`, `Participant 3rdParty`, `Objective`, `Expedition`, `RewardPool` / `RegionRewardPool`, `AssetPool`.

## Asset Traversal Patterns

Prefer the high-level traversal helpers over manual attribute walking. They short-circuit on missing paths and handle `ReferenceAttribute` dereferencing for you.

### `find` vs `find_value`

- `element.find("A.B.C")` — returns the `NamedElement` (e.g. `ListAttribute`, `Property`, `ReferenceAttribute`) at the dotted path, or `None`. Use when you need the attribute object itself (e.g. to terate a `ListAttribute`).
- `element.find_value("A.B.C")` — returns the *value* at the path: dereferenced `Asset` for a `ReferenceAttribute`, parsed primitive for a `PrimitiveAttribute`, list of literals for a `FlagsAttribut`, etc. Use when you want the payload, not the attribute wrapper.

Both work on any `NamedElement` (Asset, Property, ListItem). Paths traverse through nested properties transparently — no need to grab intermediate nodes with `getattr`.

### Avoid `getattr`/`hasattr`/`isinstance(ReferenceAttribute)` chains

Anti-pattern (verbose, swallows real errors, doesn't dereference):
```python
trigger_action = getattr(action_item, "TriggerAction", None)
if trigger_action and hasattr(trigger_action, "ActionRegisterTrigger"):
    sub_ref = trigger_action.ActionRegisterTrigger.TriggerAsset
    if isinstance(sub_ref, ReferenceAttribute) and sub_ref.value:
        sub_trigger = sub_ref.value
```

Replacement:
```python
sub_trigger = action_item.find_value("TriggerAction.ActionRegisterTrigger.TriggerAsset")
if not isinstance(sub_trigger, Asset):
    continue
```

`find_value` returns `None` if any path segment is missing, so you only need a single guard.

### Iterating list-of-references

For a `ListAttribute` whose items each contain a `ReferenceAttribute` field, use a helper like `_get_list_guids(asset, list_path, ref_attr_name)` (see `dlc_detection.py`) rather than nested loops:

```python
# Instead of:
ta_attr = trigger.find("Trigger.TriggerActions")
for item in ta_attr:
    ta = getattr(item, "TriggerAction", None)
    if ta and hasattr(ta, "ActionUnlockAsset"):
        for ua in ta.ActionUnlockAsset.UnlockAssets:
            ref = getattr(ua, "Asset", None)
            ...

# Use a helper that takes the full path from the iterated ListItem:
guids = self._get_list_guids(sub_item, "TriggerAction.ActionUnlockAsset.UnlockAssets", "Asset")
```

The helper internally calls `sub_item.find(list_path)` (which traverses through `TriggerAction.ActionUnlockAsset` to reach `UnlockAssets`), iterates the resulting `ListAttribute`, and pulls `getattritem, ref_attr_name)` for the reference. Paths that don't exist return `[]` cleanly.

### When to keep `isinstance(..., ListAttribute)` checks

`find` returns `NamedElement | None`. For list iteration you still need `isinstance(result, ListAttribute)` before iterating — `find_value` would call the attribute and return something useless for  `ListAttribute`.

## Best practices

1. Always display localized text, never internal names.
2. Never hardcode GUIDs — they shift between game versions.
3. Implement cycle detection for recursive structures (pools, functional effects).
4. Use `find` / `find_value` instead of try/except chains.
5. Build reverse indices for repeated lookups (item → pools → sources).
