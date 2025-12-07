"""Test script to inspect BuffConstructionSpeed buff struct."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)

ui_cache = assets.properties.ui_text_cache

# Get BuffConstructionSpeed buff struct
buff_info = ui_cache.buff_text_structs.get("BuffConstructionSpeed")
if not buff_info:
    print("BuffConstructionSpeed not found")
    exit(1)

buff_struct = buff_info["struct"]
variants = buff_info["variants"]

print("BuffConstructionSpeed struct:")
print(f"  Type: {type(buff_struct).__name__}")
print(f"  Variants: {variants}")

# Try to print the tree
if hasattr(buff_struct, "print_tree"):
    print("\nStruct tree:")
    buff_struct.print_tree()

# Try to get "Text" field
text_attr = buff_struct.find("Text")
print(f"\nText attribute: {text_attr}")

# Try to get variant text fields
for variant in variants:
    variant_attr = buff_struct.find(variant)
    print(f"\n{variant}:")
    print(f"  Attribute: {variant_attr}")
    if variant_attr:
        text_obj = variant_attr()
        print(f"  Text object: {text_obj}")
        if hasattr(text_obj, "values"):
            print(f"  English: {text_obj.values.get('english', 'N/A')}")

# Also check BuffConstructionCost
print("\n" + "=" * 80)
print("BuffConstructionCost struct:")
print("=" * 80)

buff_info = ui_cache.buff_text_structs.get("BuffConstructionCost")
if buff_info:
    buff_struct = buff_info["struct"]
    variants = buff_info["variants"]

    print(f"  Type: {type(buff_struct).__name__}")
    print(f"  Variants: {variants}")

    # Try to get "Text" field
    text_attr = buff_struct.find("Text")
    print(f"\nText attribute: {text_attr}")

    # Try to get variant text fields
    for variant in variants:
        variant_attr = buff_struct.find(variant)
        print(f"\n{variant}:")
        print(f"  Attribute: {variant_attr}")
        if variant_attr:
            text_obj = variant_attr()
            print(f"  Text object: {text_obj}")
            if hasattr(text_obj, "values"):
                print(f"  English: {text_obj.values.get('english', 'N/A')}")
