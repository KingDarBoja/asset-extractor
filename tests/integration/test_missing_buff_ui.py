#!/usr/bin/env python
"""Test script to identify buff attributes with missing buff_ui mappings.

This script checks all buff attributes in AreaBuff, MetaBuff, ShipBuff,
BuildingBuff, TroopBuff, and DefenseBuildingBuff templates to find attributes that:
1. Have assets using them (non-default values)
2. Are missing buff_ui mappings (buff_ui property returns None or [])

Output identifies gaps in UITextCache configuration.
"""

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

# Constants
SKIP_ATTRIBUTES = {
    "RadiusEffectRangeUpgrade",  # Explicitly returns None (handled elsewhere)
}

# Context-dependent attributes that only show buff_ui when paired with other attributes
# Format: (property_name, attribute_name, required_sibling_attribute)
CONTEXT_DEPENDENT_ATTRIBUTES = {
    ("FactoryUpgrade", "FertilityPercent"): "AddedFertility",
}

BUFF_TEMPLATES = [
    "AreaBuff",
    "MetaBuff",
    "ShipBuff",
    "BuildingBuff",
    "TroopBuff",
    "DefenseBuildingBuff",
]


def has_non_default_value(attr) -> bool:
    """Check if attribute has a non-default value.

    CRITICAL: For ListAttribute and DictAttribute, must check is_default property
    because default dicts/lists have entries but they are all zero/template values.
    """
    if attr is None:
        return False

    # Skip reference attributes
    if isinstance(attr, ReferenceAttribute):
        return False

    # ListAttribute - check is_default first, then length
    if isinstance(attr, ListAttribute):
        # CRITICAL: Default lists have entries but all zero values
        if hasattr(attr, 'is_default') and attr.is_default:
            return False
        return len(attr) > 0

    # DictAttribute - check is_default first, then length
    if isinstance(attr, DictAttribute):
        # CRITICAL: Default dicts have entries but all zero values
        if hasattr(attr, 'is_default') and attr.is_default:
            return False
        return attr.value is not None and len(attr.value) > 0

    # FlagsAttribute - check if has flags
    if isinstance(attr, FlagsAttribute):
        return attr.value is not None and len(attr.value) > 0

    # PrimitiveAttribute & UpgradeAttribute - check value != 0
    if isinstance(attr, (PrimitiveAttribute, UpgradeAttribute)):
        value = attr.value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value != ""
        return True

    return False


def format_value_summary(value) -> str:
    """Format value for display (truncate if needed)."""
    if value is None:
        return "None"
    if isinstance(value, list):
        return f"[{len(value)} items]"
    if isinstance(value, dict):
        return f"{{{len(value)} entries}}"

    value_str = str(value)
    if len(value_str) > 40:
        return value_str[:37] + "..."
    return value_str


def group_by_property(items):
    """Group items by property name for organized output."""
    grouped = {}
    for item in items:
        prop = item["property"]
        if prop not in grouped:
            grouped[prop] = []
        grouped[prop].append(item)
    return grouped


def print_header(stats):
    """Print header section with statistics."""
    print("=" * 70)
    print("MISSING BUFF_UI MAPPING TEST")
    print("=" * 70)
    print(f"Templates: {', '.join(BUFF_TEMPLATES)}")
    print(f"Total properties scanned: {stats['total_properties']}")
    print(f"Total attributes checked: {stats['total_attributes']}")
    print()
    print("STATISTICS:")

    attrs_with_assets = stats['attributes_with_assets']
    attrs_with_buff_ui = stats['attributes_with_buff_ui']
    attrs_missing_buff_ui = stats['attributes_missing_buff_ui']
    attrs_no_assets = stats['attributes_no_assets']
    total_attrs = stats['total_attributes']

    if total_attrs > 0:
        pct_with_assets = 100 * attrs_with_assets / total_attrs
        print(f"  Attributes with assets using them: {attrs_with_assets:3d} ({pct_with_assets:5.1f}%)")

        if attrs_with_assets > 0:
            pct_with_ui = 100 * attrs_with_buff_ui / attrs_with_assets
            pct_missing_ui = 100 * attrs_missing_buff_ui / attrs_with_assets
            print(f"  Attributes with buff_ui mapping:   {attrs_with_buff_ui:3d} ({pct_with_ui:5.1f}% of used)")
            print(f"  MISSING buff_ui mapping:            {attrs_missing_buff_ui:3d} ({pct_missing_ui:5.1f}% of used)")

        pct_no_assets = 100 * attrs_no_assets / total_attrs
        print(f"  Attributes with no assets:          {attrs_no_assets:3d} ({pct_no_assets:5.1f}%)")
    print()


def print_missing_buff_ui(missing_items):
    """Print section for attributes with missing buff_ui mappings."""
    print("=" * 70)
    print(f"MISSING BUFF_UI MAPPINGS ({len(missing_items)} attributes)")
    print("=" * 70)
    print()

    if not missing_items:
        print("None - all attributes have buff_ui mappings!")
        print()
        return

    # Group by property
    grouped = group_by_property(missing_items)

    for property_name, items in sorted(grouped.items()):
        print(f"{property_name} ({len(items)} attributes):")
        for item in items:
            attr_name = item['attribute']
            attr_class = item['class']
            template = item['template']
            sample_guid = item['sample_guid']
            sample_value = item['sample_value']

            print(f"  - {attr_name:40s} ({attr_class})")
            print(f"    Template: {template} | Sample: GUID {sample_guid} | Value: {sample_value}")
        print()


def print_no_assets(no_asset_items):
    """Print section for attributes with no assets using them."""
    print("=" * 70)
    print(f"ATTRIBUTES WITH NO ASSETS USING THEM ({len(no_asset_items)} attributes)")
    print("=" * 70)
    print()

    if not no_asset_items:
        print("None - all attributes are used by at least one asset!")
        print()
        return

    # Group by property
    grouped = group_by_property(no_asset_items)

    for property_name, items in sorted(grouped.items()):
        print(f"{property_name} ({len(items)} attributes):")
        for item in items:
            attr_name = item['attribute']
            attr_class = item['class']
            template = item['template']
            print(f"  - {attr_name:40s} ({attr_class}) [{template}]")
        print()


def print_summary(stats):
    """Print summary section."""
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("[OK] Scan completed successfully")

    missing_count = stats['attributes_missing_buff_ui']
    no_assets_count = stats['attributes_no_assets']

    if missing_count > 0:
        print(f"[!] Found {missing_count} attributes with missing buff_ui mappings")
    else:
        print("[OK] All attributes with assets have buff_ui mappings")

    if no_assets_count > 0:
        print(f"[i] Found {no_assets_count} unused attributes")

    print("=" * 70)


if __name__ == "__main__":
    # Load assets
    print("Loading assets...")
    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    # Initialize tracking
    missing_buff_ui = []
    no_assets = []
    stats = {
        "total_properties": 0,
        "total_attributes": 0,
        "attributes_with_assets": 0,
        "attributes_with_buff_ui": 0,
        "attributes_missing_buff_ui": 0,
        "attributes_no_assets": 0,
    }

    # Scan all buff templates
    print("Scanning buff templates...")
    for template_name in BUFF_TEMPLATES:
        # Check if template exists
        if template_name not in assets.templates:
            print(f"Warning: Template '{template_name}' not found in assets")
            continue

        template = assets.templates[template_name]

        # Iterate properties in template
        for prop in template:
            # Only check properties ending with "Upgrade"
            if not prop.name.endswith("Upgrade"):
                continue

            stats["total_properties"] += 1
            property_name = prop.name

            # Iterate attributes in property
            for attr in prop:
                # Skip reference attributes (infinite loop risk)
                if isinstance(attr, ReferenceAttribute):
                    continue

                # Skip special attributes
                if attr.name in SKIP_ATTRIBUTES:
                    continue

                stats["total_attributes"] += 1
                attr_name = attr.name
                attr_class = attr.__class__.__name__

                # Search for sample asset with non-default value
                sample_asset_guid = None
                sample_asset_attr = None
                sample_value = None

                # Check if this is a context-dependent attribute
                required_sibling = CONTEXT_DEPENDENT_ATTRIBUTES.get((property_name, attr_name))

                for asset in template.assets:
                    asset_attr = asset.find(attr.property_path)

                    if has_non_default_value(asset_attr):
                        # For context-dependent attributes, verify required context exists
                        if required_sibling:
                            sibling_path = f"{property_name}.{required_sibling}"
                            sibling_attr = asset.find(sibling_path)
                            # Skip if required sibling is missing or None
                            if sibling_attr is None or sibling_attr() is None:
                                continue

                        sample_asset_guid = asset.guid
                        sample_asset_attr = asset_attr
                        sample_value = format_value_summary(asset_attr.value)
                        break  # Found one sample, that's enough

                # Check if attribute has assets using it
                if sample_asset_guid is not None:
                    stats["attributes_with_assets"] += 1

                    # Check if buff_ui is missing
                    buff_ui = sample_asset_attr.buff_ui

                    if buff_ui is None or (isinstance(buff_ui, list) and len(buff_ui) == 0):
                        # Missing mapping!
                        stats["attributes_missing_buff_ui"] += 1
                        missing_buff_ui.append({
                            "template": template_name,
                            "property": property_name,
                            "attribute": attr_name,
                            "class": attr_class,
                            "sample_guid": sample_asset_guid,
                            "sample_value": sample_value
                        })
                    else:
                        # Has mapping
                        stats["attributes_with_buff_ui"] += 1
                else:
                    # No assets use this attribute
                    stats["attributes_no_assets"] += 1
                    no_assets.append({
                        "template": template_name,
                        "property": property_name,
                        "attribute": attr_name,
                        "class": attr_class
                    })

    # Print results
    print()
    print_header(stats)
    print_missing_buff_ui(missing_buff_ui)
    print_no_assets(no_assets)
    print_summary(stats)
