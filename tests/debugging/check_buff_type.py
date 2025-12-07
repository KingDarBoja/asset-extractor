from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json('config.json')
assets = AssetCache.load(config)
ui_cache = assets.properties.ui_text_cache

# Check what buff type name we need
print('--- Checking buff type derivation ---')
property_name = "AreaBuff"
attr_name = "RadiusEffectRangeUpgrade"

# Try to derive the buff type name
buff_type = ui_cache.get_buff_type_name(property_name, attr_name)
print(f'Derived buff type for {property_name}.{attr_name}: {buff_type}')

# Check if this buff type exists in the cache
if buff_type:
    buff_info = ui_cache.buff_text_structs.get(buff_type)
    print(f'\nBuff info exists: {buff_info is not None}')
    if buff_info:
        print(f'Buff struct path: {buff_info["struct_path"]}')
        print(f'Buff struct keys: {list(buff_info.keys())}')

        # Check what fields are available
        struct = buff_info.get("struct")
        if struct:
            print(f'\nAvailable fields in buff struct:')
            print(f'  Dir: {[x for x in dir(struct) if not x.startswith("_")]}')

            # Check for text and icon
            if hasattr(struct, 'Text'):
                text_attr = struct.Text
                print(f'  Text: {text_attr()}')
                text_obj = text_attr()
                if text_obj and hasattr(text_obj, 'values'):
                    print(f'  Text (English): {text_obj.values.get("english", "N/A")}')

            if hasattr(struct, 'Icon'):
                icon = struct.Icon
                print(f'  Icon: {icon()}')

# Also check for variations like BuffRadiusEffectRange
for test_name in ['BuffEffectRadius', 'BuffRadiusEffectRange', 'BuffAreaEffectRange', 'BuffEffectRange']:
    if test_name in ui_cache.buff_text_structs:
        print(f'\n{test_name} FOUND in cache!')
        buff_info = ui_cache.buff_text_structs[test_name]
        struct = buff_info.get("struct")
        if struct and hasattr(struct, 'Text'):
            text_obj = struct.Text()
            if text_obj and hasattr(text_obj, 'values'):
                print(f'  Text: {text_obj.values.get("english", "N/A")}')

# List all buff types containing "Effect" or "Radius"
print('\n--- All buff types with "Effect" or "Radius" ---')
for buff_name in sorted(ui_cache.buff_text_structs.keys()):
    if 'Effect' in buff_name or 'Radius' in buff_name:
        print(f'  {buff_name}')
