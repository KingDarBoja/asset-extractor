# Core Parsing Logic Memory

## DLC Unlock Mechanism (post patch 1.4)

The DLC unlock mechanism changed direction in patch 1.4. The old `Locked.DLCDependency` attribute (a `ReferenceAttribute` pointing from each locked asset to its DLC) was removed. The new mechanism is reversed:

- **`UplayProduct` assets** now carry a `UplayProductUnlocks` vector (`ListAttribute`) where each item has a `UplayProductUnlock` `ReferenceAttribute` (DataType=Asset) pointing to an unlocked asset.
- **Locked assets** only have `<Locked><Scope>Account</Scope></Locked>` — no DLC reference of their own.

### Asset fields (both populated by `resolve_dlc_unlocks()`)
- `asset.unlocked_by_dlcs: dict[int, WeightedReference]` — on unlocked asset; key = DLC GUID, `source=dlc_asset, target=unlocked_asset`
- `asset.dlc_unlocks: dict[int, WeightedReference]` — on DLC asset; key = unlocked asset GUID, `source=unlocked_asset, target=dlc_asset`

### WeightedReference convention (assetbrowser template rule)
The `render_reference_table` macro always renders `ref.source` as the displayed asset. Therefore:
- `source` = **the asset you want to show** in the reference table (the "external" link)
- `target` = the local asset that owns the dict (self-reference, not displayed)
- The two dicts use **separate** `WeightedReference` objects with **swapped** `source`/`target`.

This is consistent with pool references: `in_reward_pool` stores `source=pool, target=leaf_asset` on `leaf_asset` → shows the pool on the leaf_asset page.

### Access pattern
```python
uplay_template = assets.templates["UplayProduct"]
for dlc in uplay_template.assets:
    unlocks = dlc.find("UplayProduct.UplayProductUnlocks")  # ListAttribute
    for item in unlocks:
        unlock_ref = item.UplayProductUnlock  # ReferenceAttribute
        unlocked_asset = unlock_ref.value
```

### Known DLC GUIDs (as of patch 1.4)
| GUID  | Name         | Type        | Unlocks |
|-------|--------------|-------------|---------|
| 67902 | DLC1         | DLC         | 0 (game content, not asset-level) |
| 67903 | DLC2         | DLC         | 0 |
| 67904 | DLC3         | DLC         | 0 |
| 67901 | YearOnePass  | DLC         | 5 |
| 67906 | CDLC1        | CosmeticDLC | 34 |
| 67907 | CDLC2        | CosmeticDLC | 0 |
| 67908 | CDLC3        | CosmeticDLC | 0 |
| 93584 | PreorderBonus| DLC         | 4 |

## UIText Special Mappings: Workforce Context

`BuildingUpgrade.WorkforceModifierInPercent` always targets **residence buildings** (not factories). It means "workforce provided by residents", not "workforce needed as maintenance". Therefore:

- `("Building", "WorkforceModifier")` → maps to **`BuffOutputWorkforce`** (text: "Workforce from residents")
- NOT `BuffWorkforceAmount` (text: "Workforce Needed") — that is for `MaintenanceUpgrade.WorkforceMaintenanceFactor`

This was verified by checking all items in the game: every item using `BuildingUpgrade.WorkforceModifierInPercent` has its `Effect.Targets` set to residence asset pools exclusively.

**Pitfall**: When adding new `special_mappings` in `get_buff_type_name()`, always verify whether an attribute is exclusively used in one context. Attributes like `WorkforceModifier` look like a maintenance cost but are semantically different for residences.

## Tech.Rewards.Unlocks — Reward Types

`Tech.Rewards.Unlocks[i].UnlockReward` is a `ReferenceAttribute` that can point to different asset types — **not** exclusively `TechFeatureUnlock`:

| Reward template | Meaning | Example |
|----------------|---------|---------|
| `TechFeatureUnlock` | Flag asset; enables BFS ConditionUnlocked chaining | 145339 "Tech Unlock ObsidianGathering" |
| `AssetPool` / `AssetPoolNamed` | Pool of assets directly unlocked by the tech | 145234 "Asset Pool Roman Idols" → buildings [145229, ...] |
| Other (Patron, Effect, etc.) | Mark as DLC; no BFS extension | 144800 Vulcan patron |

**Pitfall**: Only add a reward to `fu_dlcs` (BFS state) if its template is `FeatureUnlock` or `TechFeatureUnlock`. Adding AssetPools to `fu_dlcs` is incorrect (they have no `Trigger.TriggerCondition`).

## Patron Asset Structure

`Patron` assets have two AssetPool-typed reference fields relevant to DLC tracking:

- `Patron.Wonder` → `ReferenceAttribute` → `AssetPoolNamed` of wonder buildings
- `Patron.Shrine` → `ReferenceAttribute` → `AssetPoolNamed` of shrine buildings

Both pools are DLC-locked when the Patron itself is DLC-locked (e.g. Vulcan patron GUID 144800, unlocked via Tech DLC01 Patron Vulcan). Flatten with `AssetPool.AssetList[i].Asset`.

## Attribute Inheritance
- **Strict Type Assumption**: The `resolve_inheritance` method in `Attribute` subclasses (in `attributes.py`) strictly assumes that the `default` parameter is an instance of the same subclass.
- **Type Hinting**: Use `t.Self` for the `default` parameter to enforce this assumption.
- **LSP Violation**: This pattern technically violates the Liskov Substitution Principle (LSP) by narrowing the input type of overridden methods.
- **Pyright Suppression**: Always use `# pyright: ignore[reportIncompatibleMethodOverride]` on these methods to suppress static analysis errors, as the project architecture guarantees type compatibility at runtime.

## Labeled GUID Values in assets.xml (post patch 1.4+)

Some `ReferenceAttribute` values in `assets.xml` are no longer plain integers. They may include a human-readable label, e.g.:
```
Province Egyptian Aegyptus - 149679
```
**Fix** (`attributes.py:865`): When parsing `ReferenceAttribute`, if the value is not a plain integer and contains ` - `, split on the last ` - ` and parse the trailing part as the GUID. This is already handled in the code.

## Unnamed Groups in properties-meta.xml Causing Missing Initializations

`properties-meta.xml` has many `<Group>` elements with no `<Name>` (or `<Name>` with null text). In `PropertyGroup.__init__`, all such groups are stored under key `"None"` in `subgroups`, so only the LAST sibling group at each nesting level is retained. This affects up to 35 groups at one level.

**Symptom**: `ValueError: AutoCreateAsset X [properties-meta:N] not initialized.` during `AssetCache.load()`.

**Root cause**: A `DefaultContainerValues` entry sets `template_name` on a vector-item's `ValueDefinition.default` (a `TemplateAttribute`). Because the owning `MetaProperty` is in a group that was overwritten, `TemplateCache._process_property_group` never calls `_process_meta_property` for it, so `_process_default` is never called, leaving `_is_initialized = False`.

**Fix** (`templates.py`, `TemplateCache.__init__`): After `_process_property_group`, also iterate `self.properties.elements.values()` (the global `MetaPropertyCache` registry, which contains all `MetaProperty` objects regardless of group hierarchy) and call `_process_meta_property` on each. The `_processed_defaults` set prevents double-processing.

**Pattern**: This only triggers when a `DefaultContainerValues` entry sets a `template_name` on a vector item's default in an overwritten group. If no `DefaultContainerValues` applies, the default's `template_name` stays `None` and the early-return `if self.is_default and self.template_name is None: _is_initialized = True` handles it harmlessly.

## Typed Asset Subclass Registry

`Asset` supports game-domain subclasses (in `assetextractor/parsing/typed/`). A subclass declares `class Foo(Asset, template_names="TemplateName")`; `Asset.__init_subclass__` records it in `Asset._registry`. During construction every node goes through `Asset.create(node, cache)`, which looks up the subclass by template name. `AssetCache.load()` does `import assetextractor.parsing.typed` (lazy, inside `load()`) so the registry is populated before the cache is built — after a load, `template.assets` and `assets.elements` hold the correct subclass instances (verified: ~5.8k of ~41k assets become subclasses).

- **Backward compatible**: `isinstance(x, Asset)` still holds; only `type(x) is Asset` checks are affected.
- **`BaseAssetGUID` assets** (no `<Template>` tag) start as plain `Asset` and are re-instantiated as the typed subclass in `AssetCache.resolve_inheritance()` once the base template is known. Do not cache references to such assets taken during load — they go stale.
- **Constructing `AssetCache` directly** (bypassing `load()`) requires importing `assetextractor.parsing.typed` first, or the registry is empty.
- Full guide (writing a subclass, notebook re-wrapping): `assetextractor/parsing/typed/README.md`.

## ColorAttribute Hex / RGBA

`ColorAttribute.get_hex(color_mode="None")` returns `#RRGGBBAA`; `get_rgba(...)` returns an `(r,g,b,a)` tuple. Backed by the `AnnoColor` dataclass (Anno stores colors as signed ints). `color_mode` ∈ `None | Deuteranopia | Protanopia | Tritanopia`.

## Flags Data Type (Literals vs GUIDs)

Attributes with the `Flags` data type (e.g., `Building.AssociatedRegions`, `Product.AssociatedRegion`) are parsed into a **`list[str]` of literals**, not GUIDs or integers.

- **XML Format**: Semicolon-separated strings like `<AssociatedRegions>Meta;Moderate;Colony01;Arctic</AssociatedRegions>`.
- **Python Representation**: `FlagsAttribute` parses these into a Python list: `['Meta', 'Moderate', 'Colony01', 'Arctic']`.
- **Common Values**: Literals from the `Region` dataset, such as `'Roman'`, `'Meta'`, `'Moderate'`, `'Colony01'`, and `'Arctic'`.
- **Pitfall**: When filtering by region, compare against these literal strings (e.g., `if 'Roman' in asset.Building.AssociatedRegions()`). Do not use GUIDs for comparison with `Flags` attributes.
