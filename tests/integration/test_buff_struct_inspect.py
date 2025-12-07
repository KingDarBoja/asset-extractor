"""Inspect BuffInfectableImmunity structure."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


def inspect_buff_infectable_immunity():
    """Inspect the BuffInfectableImmunity buff struct."""
    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    ui_cache = assets.properties.ui_text_cache

    # Check if BuffInfectableImmunity is loaded
    if "BuffInfectableImmunity" in ui_cache.buff_text_structs:
        print("BuffInfectableImmunity found in buff_text_structs")

        buff_info = ui_cache.buff_text_structs["BuffInfectableImmunity"]
        print(f"\nBuff info keys: {buff_info.keys()}")
        print(f"Variants: {buff_info.get('variants', [])}")

        buff_struct = buff_info["struct"]
        print(f"\nBuff struct type: {type(buff_struct).__name__}")

        # Try to list all fields in buff_struct
        if hasattr(buff_struct, 'value'):
            print(f"\nBuff struct fields (value dict keys): {list(buff_struct.value.keys())}")

            # Check for Text
            text_field = buff_struct.find("Text")
            print(f"\nText field: {text_field}")
            if text_field:
                print(f"  Type: {type(text_field).__name__}")
                try:
                    text_value = text_field()
                    print(f"  Value: {text_value}")
                    if hasattr(text_value, 'values'):
                        print(f"  English: {text_value.values.get('english', 'N/A')}")
                except Exception as e:
                    print(f"  Error calling: {e}")

            # Check for AreaText
            areatext_field = buff_struct.find("AreaText")
            print(f"\nAreaText field: {areatext_field}")
            if areatext_field:
                print(f"  Type: {type(areatext_field).__name__}")
                try:
                    areatext_value = areatext_field()
                    print(f"  Value: {areatext_value}")
                    if hasattr(areatext_value, 'values'):
                        print(f"  English: {areatext_value.values.get('english', 'N/A')}")
                except Exception as e:
                    print(f"  Error calling: {e}")
    else:
        print("BuffInfectableImmunity NOT found in buff_text_structs")


if __name__ == "__main__":
    inspect_buff_infectable_immunity()
