#!/usr/bin/env python
"""Investigate attributes with missing buff_ui mappings in detail."""

import logging
logging.basicConfig(level=logging.WARNING)

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache
from assetextractor.parsing.core.attributes import (
    ReferenceAttribute,
    ListAttribute,
    DictAttribute,
    FlagsAttribute,
    PrimitiveAttribute,
    UpgradeAttribute,
)

# Load assets
print("Loading assets...")
config = Config.from_json("config.json")
assets = AssetCache.load(config)
ui_text_cache = assets.properties.ui_text_cache

# Attributes with missing buff_ui (from test_missing_buff_ui.py results)
MISSING_BUFF_UI = [
    ("AreaBuff", "AreaFestivalAttributeUpgrade", "AdditionalPercentage", 109676),
    ("AreaBuff", "AreaMaintenanceUpgrade", "MeshGraphUpkeep", 62152),
    ("AreaBuff", "AreaPassiveTradeUpgrade", "PassiveTradeProfitModifier", 68767),
    ("BuildingBuff", "DistributionUpgrade", "AddDeltas", 71192),
    ("BuildingBuff", "FactoryUpgrade", "FertilityPercent", 42658),
    ("BuildingBuff", "IrrigationUpgrade", "PipeCapacityUpgrade", 29210),
    ("ShipBuff", "MaintenanceUpgrade", "MaintenanceFactorUpgrade", 52116),
    ("BuildingBuff", "ModuleOwnerUpgrade", "ModuleLimitPercent", 43610),
    ("ShipBuff", "MovementUpgrade", "BuffReduceCargoImpactUpgrade", 71184),
    ("DefenseBuildingBuff", "RepairCraneUpgrade", "HealPerMinuteUpgrade", 71148),
    ("BuildingBuff", "ResidenceUpgrade", "GoodConsumptionUpgrade", 51356),
    ("BuildingBuff", "WarehouseUpgrade", "StorageCapacityModifier", 80548),
]

print("=" * 80)
print("INVESTIGATING MISSING BUFF_UI MAPPINGS")
print("=" * 80)
print()

for template_name, property_name, attr_name, guid in MISSING_BUFF_UI:
    print("=" * 80)
    print(f"Template: {template_name}")
    print(f"Property: {property_name}")
    print(f"Attribute: {attr_name}")
    print(f"Sample GUID: {guid}")
    print("-" * 80)

    # Get the asset
    asset = assets.get(guid)
    if not asset:
        print(f"ERROR: Asset {guid} not found!")
        print()
        continue

    # Get the attribute
    attr_path = f"{property_name}.{attr_name}"
    attr = asset.find(attr_path)

    if attr is None:
        print(f"ERROR: Attribute {attr_path} not found in asset!")
        print()
        continue

    # Print attribute details
    print(f"Attribute type: {attr.__class__.__name__}")
    print(f"Attribute path: {attr.property_path}")

    # Print value
    print(f"Value: {attr.value}")

    # Check if has is_default
    if hasattr(attr, 'is_default'):
        print(f"is_default: {attr.is_default}")

    # Check if has percental flag
    if hasattr(attr, 'percental'):
        print(f"percental: {attr.percental}")

    # Print meta information
    if hasattr(attr, 'meta'):
        print(f"\nMeta info:")
        print(f"  Name: {attr.meta.name}")
        if hasattr(attr.meta, 'data_type'):
            print(f"  Data type: {attr.meta.data_type}")
        if hasattr(attr.meta, 'dataset') and attr.meta.dataset:
            print(f"  Dataset: {attr.meta.dataset.name}")

    # Check buff_ui
    print(f"\nbuff_ui: {attr.buff_ui}")

    # Special case: FertilityPercent
    if attr_name == "FertilityPercent":
        fertility_value = attr() if callable(attr) else attr.value
        print(f"\n[SPECIAL CASE] FertilityPercent handling:")
        print(f"  Default value is 100 (represents 100% fertility)")
        print(f"  Current value: {fertility_value}")

        # Check if AddedFertility is set
        factory_upgrade = asset.find(property_name)
        if factory_upgrade:
            added_fertility = factory_upgrade.AddedFertility if hasattr(factory_upgrade, 'AddedFertility') else None
            if added_fertility:
                added_fertility_value = added_fertility()
                print(f"  AddedFertility: {added_fertility_value}")
                if added_fertility_value and added_fertility_value != 0:
                    print(f"  [OK] FertilityPercent is relevant (AddedFertility is set)")
                else:
                    print(f"  [NOTE] AddedFertility is not set - FertilityPercent has no effect")
            else:
                print(f"  [NOTE] AddedFertility attribute not found")

        if fertility_value == 100:
            print(f"  [NOTE] Value is at default (100) - buff_ui correctly returns None")
            print(f"  This is expected behavior - only non-default values need UI display")

    # Try to get buff type name from ui_text_cache
    property_base = property_name.replace("Upgrade", "")
    attr_base = attr_name.replace("Upgrade", "")
    buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)
    print(f"\nAutomatic buff type mapping:")
    print(f"  Property (base): {property_base}")
    print(f"  Attribute (base): {attr_base}")
    print(f"  Buff type name: {buff_type}")

    if buff_type:
        # Check if buff type exists in cache
        if buff_type in ui_text_cache.buff_text_structs:
            print(f"  [OK] Buff type EXISTS in cache")
            buff_struct = ui_text_cache.buff_text_structs[buff_type]
            print(f"  Buff struct: {buff_struct}")
        else:
            print(f"  [X] Buff type NOT FOUND in cache")
    else:
        print(f"  [X] No automatic mapping found")

    # For ListAttribute and DictAttribute, show more details
    if isinstance(attr, ListAttribute):
        print(f"\nList contents ({len(attr)} items):")
        for i, item in enumerate(attr):
            if i >= 3:  # Limit to first 3 items
                print(f"  ... and {len(attr) - 3} more items")
                break
            print(f"  Item {i}: {item}")
            # Check if item has buff_ui
            if hasattr(item, 'buff_ui'):
                print(f"    Item buff_ui: {item.buff_ui}")

    elif isinstance(attr, DictAttribute):
        print(f"\nDict contents ({len(attr.value)} entries):")
        for key, value in list(attr.value.items())[:5]:  # Limit to first 5
            print(f"  {key}: {value}")
            if hasattr(value, 'buff_ui'):
                print(f"    Value buff_ui: {value.buff_ui}")

    print()
