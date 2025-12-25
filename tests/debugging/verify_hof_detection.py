"""Verify Hall of Fame detection works correctly."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

config = Config.from_json("config.json")
assets = AssetCache.load(config)

# Hall of Fame item GUIDs from manual CSV
hof_item_guids = [42625, 42049, 42050, 91415, 91417, 91419, 91421]

print("=" * 80)
print("Verifying Hall of Fame Detection")
print("=" * 80)

detected_count = 0
for guid in hof_item_guids:
    item = assets[guid]
    has_halloffame = "HallOfFame" in item.name if item.name else False

    print(f"\n{guid} - {item.name}")
    print(f"  Localized name: {item.text() if item.text else 'N/A'}")
    print(f"  Has 'HallOfFame' in name: {has_halloffame}")

    if has_halloffame:
        # Get the Hall of Fame text
        hall_of_fame_text_id = -6906945524005841361
        hof_text = assets.texts.get(hall_of_fame_text_id)
        if hof_text:
            print(f"  Hall of Fame text (English): {hof_text.values.get('english', 'N/A')}")
        print(f"  [OK] Should be detected as Hall of Fame source")
        detected_count += 1
    else:
        print(f"  [WARNING] No 'HallOfFame' in name - detection will fail!")

print("\n" + "=" * 80)
print(f"Verification complete! {detected_count}/{len(hof_item_guids)} items detected")
print("=" * 80)
