"""Debug buff type derivation."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json('config.json')
print("Loading assets...")
assets = AssetCache.load(config)
ui_cache = assets.properties.ui_text_cache
print("Assets loaded\n")

# Test the derivation with debug
property_name = "AreaBuff"
attr_name = "RadiusEffectRangeUpgrade"

print(f"Input: property_name='{property_name}', attr_name='{attr_name}'")
print()

# Manually replicate the derivation logic
# From uitext.py line ~395-410
property_base = property_name
if property_base.endswith("Buff"):
    property_base = property_base[:-4]
elif property_base.endswith("Upgrade"):
    property_base = property_base[:-7]

attr_base = attr_name
if attr_base.endswith("InPercent"):
    attr_base = attr_base[:-len("InPercent")]
elif attr_base.endswith("Percent"):
    attr_base = attr_base[:-len("Percent")]
if attr_base.endswith("Upgrade"):
    attr_base = attr_base[:-len("Upgrade")]
if attr_base.endswith("Upgrage"):
    attr_base = attr_base[:-len("Upgrage")]

if attr_base.startswith("Buff"):
    attr_base = attr_base[4:]

print(f"After processing:")
print(f"  property_base = '{property_base}'")
print(f"  attr_base = '{attr_base}'")
print(f"  key = ('{property_base}', '{attr_base}')")
print()

# Check if the key exists in special mappings
# We need to read the actual special_mappings from the code
# Let's just call the method and see
buff_type = ui_cache.get_buff_type_name(property_name, attr_name)
print(f"Result from get_buff_type_name: {buff_type}")
print()

# Check if BuffEffectRadius exists in buff_text_structs
print(f"'BuffEffectRadius' in buff_text_structs: {'BuffEffectRadius' in ui_cache.buff_text_structs}")

# Try to manually check the special mappings by looking at the source
# Let's check if our edit was saved correctly
import inspect
source = inspect.getsource(ui_cache.get_buff_type_name)
if '("Area", "RadiusEffectRange")' in source:
    print("✓ Special mapping exists in source code")
else:
    print("✗ Special mapping NOT found in source code!")
    print("\nSearching for 'RadiusEffect' in source:")
    if 'RadiusEffect' in source:
        print("  Found 'RadiusEffect'")
        # Find the line
        for line in source.split('\n'):
            if 'RadiusEffect' in line:
                print(f"  {line.strip()}")
    else:
        print("  NOT found")
