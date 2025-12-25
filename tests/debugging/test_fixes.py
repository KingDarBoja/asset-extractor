"""Test the bug fixes for quest deduplication and colosseum sources."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache
from assetextractor.conversion.statistics.item_extractor import ItemExtractor

print("Loading assets...")
config = Config.from_json("config.json")
assets = AssetCache.load(config)

print("Creating extractor...")
extractor = ItemExtractor(assets, language="english")

print("\n=== Testing Quest Deduplication (should allow duplicates) ===")
# Test item 71438 - Gaius Julius Lupus, should have "Quest: Gemini In The Rough" twice
item_71438 = assets[71438]
sources_71438 = extractor.source_tracker.find_all_sources(item_71438)
print(f"Item 71438 quest sources: {sources_71438.get('quest', [])}")
print(f"Number of quest sources: {len(sources_71438.get('quest', []))}")

print("\n=== Testing Colosseum Source Naming ===")
# Test item 96815 - Gigantulas, should have proper colosseum decision name
item_96815 = assets[96815]
sources_96815 = extractor.source_tracker.find_all_sources(item_96815)
print(f"Item 96815 colosseum sources: {sources_96815.get('colosseum', [])}")
if sources_96815.get('colosseum'):
    colosseum_source = sources_96815['colosseum'][0]
    print(f"Colosseum name: {colosseum_source.get('name')}")

print("\n=== Test Complete ===")
