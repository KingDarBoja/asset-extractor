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

## Attribute Inheritance
- **Strict Type Assumption**: The `resolve_inheritance` method in `Attribute` subclasses (in `attributes.py`) strictly assumes that the `default` parameter is an instance of the same subclass.
- **Type Hinting**: Use `t.Self` for the `default` parameter to enforce this assumption.
- **LSP Violation**: This pattern technically violates the Liskov Substitution Principle (LSP) by narrowing the input type of overridden methods.
- **Pyright Suppression**: Always use `# pyright: ignore[reportIncompatibleMethodOverride]` on these methods to suppress static analysis errors, as the project architecture guarantees type compatibility at runtime.
