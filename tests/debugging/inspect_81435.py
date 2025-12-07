from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json('config.json')
assets = AssetCache.load(config)
item = assets.get(81435)

print('Asset Name:', item.text.values.get('english') if item.text else 'N/A')
print('\n--- AreaBuff Structure ---')
area_buff = item.find('AreaBuff')
print('Has AreaBuff:', area_buff is not None)

if area_buff:
    # Check RadiusEffectRangeUpgrade
    if hasattr(area_buff, 'RadiusEffectRangeUpgrade'):
        upgrade_attr = area_buff.RadiusEffectRangeUpgrade
        print('\nRadiusEffectRangeUpgrade:')
        print('  Value:', upgrade_attr())
        print('  Type:', type(upgrade_attr).__name__)
        print('  Has percental:', hasattr(upgrade_attr, 'percental'))
        if hasattr(upgrade_attr, 'percental'):
            print('  Percental:', upgrade_attr.percental)

    # Check RadiusEffectRangeTarget
    if hasattr(area_buff, 'RadiusEffectRangeTarget'):
        targets = area_buff.RadiusEffectRangeTarget
        print('\nRadiusEffectRangeTarget:')
        print('  Type:', type(targets).__name__)
        print('  Has _value_list:', hasattr(targets, '_value_list'))

        if hasattr(targets, '_value_list'):
            print('  List length:', len(targets._value_list))

            # Inspect first item structure
            if len(targets._value_list) > 0:
                for idx, item in enumerate(targets):
                    print(f'\n  Item {idx}:')
                    print(f'    Type: {type(item).__name__}')
                    print(f'    Dir: {[x for x in dir(item) if not x.startswith("_")]}')

                    # Try common attribute names
                    if hasattr(item, 'Target'):
                        target = item.Target()
                        print(f'    Target: {target}')
                        if target and hasattr(target, 'text'):
                            print(f'    Target name: {target.text.values.get("english") if target.text else "N/A"}')
                        if target:
                            print(f'    Target GUID: {target.guid}')

                    # Check for other possible attributes
                    for attr_name in ['Range', 'Radius', 'Value', 'Amount']:
                        if hasattr(item, attr_name):
                            val = getattr(item, attr_name)()
                            print(f'    {attr_name}: {val}')

# Check buff_ui current behavior
print('\n--- Current buff_ui behavior ---')
if hasattr(area_buff, 'RadiusEffectRangeUpgrade'):
    print('RadiusEffectRangeUpgrade.buff_ui:', area_buff.RadiusEffectRangeUpgrade.buff_ui)

if hasattr(area_buff, 'RadiusEffectRangeTarget'):
    print('RadiusEffectRangeTarget.buff_ui:', area_buff.RadiusEffectRangeTarget.buff_ui)
