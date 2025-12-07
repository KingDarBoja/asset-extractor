#!/usr/bin/env python
"""Test script for formatted buff texts with placeholders."""

import logging
logging.basicConfig(level=logging.INFO)
# Enable debug logging for specific modules
logging.getLogger("parsing").setLevel(logging.DEBUG)
logging.getLogger("parsing.uitext").setLevel(logging.DEBUG)

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
print("Loading assets...")
assets = AssetCache.load(config)

# Test with asset 51283 (Casponia Casta, Sacerdos Cereris)
# This buff has ProductivityUpgrade: 25% and AdditionalOutput
buff_asset = assets[51283]

print(f"\nBuff Asset: {buff_asset.guid}")
print(f"Name: {buff_asset.text.values.get('english') if buff_asset.text else 'N/A'}")

# Check FactoryUpgrade
if hasattr(buff_asset, "FactoryUpgrade"):
    factory = buff_asset.FactoryUpgrade

    # Check ProductivityUpgrade
    if hasattr(factory, "ProductivityUpgrade"):
        prod_value = factory.ProductivityUpgrade()
        print(f"\nProductivityUpgrade: {prod_value}")

        # Check ui_text on the attribute
        if hasattr(factory.ProductivityUpgrade, "ui_text"):
            ui_text = factory.ProductivityUpgrade.ui_text
            if ui_text:
                print(f"UI Text (via ui_text): {ui_text.values.get('english')}")

    # Check AdditionalOutput
    if hasattr(factory, "AdditionalOutput"):
        add_output = factory.AdditionalOutput
        print(f"\nAdditionalOutput list has {len(add_output._value_list)} items")

        for i, output_entry in enumerate(add_output):
            print(f"\nAdditionalOutput[{i}]:")

            # Get values directly
            product = output_entry.Product()
            amount = output_entry.Amount()
            cycle = output_entry.AdditionalOutputCycle()
            force_same = output_entry.ForceProductSameAsFactoryOutput()

            product_name = product.text.values.get('english', '') if product and product.text else str(product.guid if product else 'None')

            print(f"  Product: {product_name}")
            print(f"  Amount: {amount}")
            print(f"  Cycle: {cycle}")
            print(f"  ForceSame: {force_same}")

            # Test the ui_text property
            if hasattr(output_entry, "ui_text"):
                formatted_text = output_entry.ui_text
                print(f"  Formatted text (ui_text): {formatted_text}")
            else:
                print("  ERROR: ui_text property not found on output_entry")

print("\n✓ Test completed")
