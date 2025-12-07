"""Test the refactored ListItem.buff_ui implementation."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Test with AdditionalOutput (uses _format_additional_factory_output)
print("Testing AdditionalOutput (should use _format_additional_factory_output):")
for template_name in ["BuildingBuff"]:
    if template_name not in assets.templates:
        continue

    for buff in assets.templates[template_name].assets:
        if not hasattr(buff, "FactoryUpgrade"):
            continue

        factory_upgrade = buff.FactoryUpgrade
        if not hasattr(factory_upgrade, "AdditionalOutput"):
            continue

        additional_output = factory_upgrade.AdditionalOutput
        if len(additional_output._value_list) > 0:
            print(f"\nBuff GUID: {buff.guid}")
            print(f"  Number of items in AdditionalOutput: {len(additional_output._value_list)}")

            # Test individual ListItem.buff_ui
            first_item = additional_output._value_list[0]
            print(f"  First item: {first_item}")
            print(f"  Parent: {first_item.parent}")
            print(f"  Parent property_path: {first_item.parent.property_path if hasattr(first_item.parent, 'property_path') else 'N/A'}")
            print(f"  Has Amount: {hasattr(first_item, 'Amount')}")
            if hasattr(first_item, 'Amount'):
                print(f"  Amount value: {first_item.Amount()}")

            item_buff_ui = first_item.buff_ui
            print(f"  ListItem.buff_ui result: {item_buff_ui}")
            if item_buff_ui:
                print(f"  ListItem.buff_ui: {item_buff_ui}")
            else:
                print("  ListItem.buff_ui returned None")

            # Test ListAttribute.buff_ui (uses create_buff_ui_list)
            list_buff_ui = additional_output.buff_ui
            print(f"  ListAttribute.buff_ui result: {list_buff_ui}")
            if list_buff_ui:
                print(f"  ListAttribute.buff_ui: {len(list_buff_ui)} items")
                for buff_ui in list_buff_ui:
                    print(f"    - {buff_ui}")
            else:
                print("  ListAttribute.buff_ui returned None or empty")

            # Only show first example
            break
    else:
        continue
    break

print("\nTest completed!")
