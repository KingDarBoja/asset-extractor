"""Test the new create_buff_ui_dict method."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Find a BuildingBuff with AdditionalAttributes
for template_name in ["BuildingBuff"]:
    if template_name not in assets.templates:
        continue

    for buff in assets.templates[template_name].assets:
        # Check if it has BuildingUpgrade.AdditionalAttributes
        if not hasattr(buff, "BuildingUpgrade"):
            continue

        building_upgrade = buff.BuildingUpgrade
        if not hasattr(building_upgrade, "AdditionalAttributes"):
            continue

        additional_attrs = building_upgrade.AdditionalAttributes

        # Test the buff_ui property (which now uses create_buff_ui_dict)
        buff_ui_list = additional_attrs.buff_ui

        if buff_ui_list:
            print(f"\nBuff GUID: {buff.guid}")
            print(f"Number of BuffUI objects: {len(buff_ui_list)}")
            for buff_ui in buff_ui_list:
                print(f"  - {buff_ui}")

            # Only show first example
            break
    else:
        continue
    break

print("\n✓ Test completed successfully!")
