# Buff System

Items in Anno 117 apply effects through **Buff** assets. Two template families exist:

- **BuildingBuff** — modifies buildings
- **ShipBuff** — modifies ships

## Asset.buff_ui (recommended entry point)

Every `Asset` exposes a `buff_ui` property that recursively walks all nested attributes and returns a `list[BuffUI]`. Each `BuffUI` carries an `icon` (`FileNameAttribute`), `text` (`Text` or `str`), `value` (formatted string like `"+25%"`), and `literal` (dataset literal).

```python
for buff_ui in assets[some_guid].buff_ui:
    name = buff_ui.text.values["english"] if hasattr(buff_ui.text, "values") else buff_ui.text
    print(f"{name}: {buff_ui.value}")
```

Attribute types contributing to `buff_ui`: `PrimitiveAttribute` (Choice + dataset), `UpgradeAttribute`, `FlagsAttribute`, `ListAttribute`, `DictAttribute`, `ListItem`. Use this in preference to manually walking buff paths whenever possible.

## Reaching buffs from an item

```python
for buff_entry in item.Effect.Buffs:
    buff = assets[buff_entry.GUID.guid]
    is_ship = "ShipBuff" in buff.template.name
```

## Upgrade categories

Buff content lives under category properties. Probe with `find()` / `find_value()`.

**BuildingBuff:**
- `BuildingUpgrade.AdditionalAttributes` (Money/Happiness/Prestige), `WorkforceModifierInPercent`, `AdditionalFunctionalEffect`
- `ResidenceUpgrade.ProvidedNeedUpgrade`, `ConsumptionModifierInPercent`, `NeedProvidedNeedAttributes` (conditional bonuses)
- `FactoryUpgrade.ProductivityUpgrade`, `AdditionalOutput`, `ReplaceInputs`
- `MaintenanceUpgrade.MaintenanceFactorUpgrade`, `WorkforceMaintenanceFactorUpgrade`
- Other categories: `ModuleOwnerUpgrade`, `CityInstitutionUpgrade`, `RecruitmentUpgrade`, `AqueductUpgrade`, `WarehouseUpgrade`, `IrrigationUpgrade`

**ShipBuff:**
- `MovementUpgrade.BuffBaseSpeedUpgrade`, `BuffReduceCargoImpactUpgrade`
- `HealthUpgrade.BaseHealthUpgrade`, `SelfHealUpgrade`
- `TradeShipUpgrade.ActiveTradePriceInPercent`, `LoadingSpeedUpgrade`
- `UnitUpgrade.DiscoveryRadiusUpgrade`, `DefenseUpgrade`
- `ItemContainerUpgrade.SlotCountUpgrade`, `SocketCountUpgrade`

## Functional effects (two-level indirection)

`BuildingUpgrade.AdditionalFunctionalEffect` points to another asset whose `Effect.Buffs` must also be processed. Track visited effects to prevent infinite recursion.

## Conditional residence bonuses

`ResidenceUpgrade.NeedProvidedNeedAttributes` holds bonuses gated on a provided need:
- `ChangeNeedAttributesOf[i].ProvidedProduct()` — required need
- `AdditionalNeedAttributes` — bonuses applied while the need is provided
