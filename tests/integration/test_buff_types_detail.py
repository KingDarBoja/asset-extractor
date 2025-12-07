"""Test script to check specific buff types."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

ui_cache = assets.properties.ui_text_cache

# Check the suspected buff types
buff_types_to_check = [
    "BuffReducePositiveSpeedImpactOfDamage",
    "BuffReduceNegativeSpeedImpactOfWind",
    "BuffReduceSpeedImpactOfDamage",
]

print("=" * 80)
print("Checking buff type structs")
print("=" * 80)

for buff_type in buff_types_to_check:
    if buff_type in ui_cache.buff_text_structs:
        print(f"\n{buff_type}:")
        print("-" * 80)

        buff_info = ui_cache.buff_text_structs[buff_type]
        buff_struct = buff_info["struct"]
        variants = buff_info.get("variants", [])

        print(f"Variants: {variants}")

        # Print tree
        if hasattr(buff_struct, "print_tree"):
            buff_struct.print_tree()

        # Check for Text field
        text_attr = buff_struct.find("Text")
        if text_attr:
            text_obj = text_attr()
            print(f"\nText: {text_obj}")
            if hasattr(text_obj, "values"):
                print(f"English: {text_obj.values.get('english', 'N/A')}")
        else:
            print("\nNo Text field found")

        # Check for Icon
        icon_attr = buff_struct.find("Icon")
        if icon_attr:
            print(f"Icon: {icon_attr}")
    else:
        print(f"\n{buff_type}: NOT FOUND")

# List all buff types with "Damage" or "Wind" in the name
print("\n" + "=" * 80)
print("All buff types with 'Damage' or 'Wind' in name:")
print("=" * 80)
for buff_name in sorted(ui_cache.buff_text_structs.keys()):
    if "Damage" in buff_name or "Wind" in buff_name:
        print(f"  {buff_name}")
