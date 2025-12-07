"""Test just the mapping without loading assets."""

# Force reimport
import sys
if 'assetextractor.parsing.core.uitext' in sys.modules:
    del sys.modules['assetextractor.parsing.core.uitext']
if 'assetextractor.parsing.core' in sys.modules:
    del sys.modules['assetextractor.parsing.core']

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json('config.json')
print("Loading assets (this may take a moment)...")
assets = AssetCache.load(config)
ui_cache = assets.properties.ui_text_cache

# Test the specific mapping
property_name = "AreaBuff"
attr_name = "RadiusEffectRangeUpgrade"

print(f"\nTesting: property='{property_name}', attr='{attr_name}'")

# Call the method
buff_type = ui_cache.get_buff_type_name(property_name, attr_name)
print(f"Result: {buff_type}")

if buff_type == "BuffEffectRadius":
    print("SUCCESS - Mapping works!")
else:
    print(f"FAILED - Expected 'BuffEffectRadius', got '{buff_type}'")

    # Try to understand why it failed
    print("\nDebugging:")

    # Check if BuffEffectRadius exists
    exists = "BuffEffectRadius" in ui_cache.buff_text_structs
    print(f"  'BuffEffectRadius' in buff_text_structs: {exists}")

    # Manually check the pattern
    property_base = "Area"
    attr_base = "RadiusEffectRange"
    print(f"  Expected key: ('{property_base}', '{attr_base}')")

    # Try the patterns
    pattern1 = f"Buff{attr_base}"
    pattern2 = f"Buff{property_base}{attr_base}"
    pattern3 = f"Buff{attr_base}Upgrade"

    print(f"  Pattern 1: Buff + attr_base = '{pattern1}'")
    print(f"    Exists: {pattern1 in ui_cache.buff_text_structs}")
    print(f"  Pattern 2: Buff + property + attr = '{pattern2}'")
    print(f"    Exists: {pattern2 in ui_cache.buff_text_structs}")
    print(f"  Pattern 3: Buff + attr + Upgrade = '{pattern3}'")
    print(f"    Exists: {pattern3 in ui_cache.buff_text_structs}")
