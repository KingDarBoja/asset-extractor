"""Test NeedAttributeType UI text mapping."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


def test_need_attribute_mapping():
    """Test get_ui_text for NeedAttributeType literals."""
    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    ui_cache = assets.properties.ui_text_cache

    # Test all NeedAttributeType literals
    literals = ["Population", "Money", "Happiness", "Health", "FireSafety", "Belief", "Knowledge", "Prestige"]

    print(f"\nTesting {len(literals)} NeedAttributeType literals:")

    for literal in literals:
        mapping = ui_cache.get_ui_text("NeedAttributeType", literal)
        print(f"\nLiteral: {literal}")
        print(f"  Mapping: {mapping}")
        if mapping:
            print(f"  Text ID: {mapping.text_id}")
            print(f"  Icon: {mapping.icon}")
            print(f"  Text: {mapping.text}")
            if mapping.text and hasattr(mapping.text, "values"):
                print(f"  English: {mapping.text.values.get('english', 'N/A')}")

        # Assert mapping exists
        assert mapping is not None, f"No mapping for {literal}"
        assert mapping.text is not None, f"No text for {literal}"
        assert mapping.icon is not None, f"No icon for {literal}"

    print("\n[OK] All NeedAttributeType literals have valid mappings")


if __name__ == "__main__":
    test_need_attribute_mapping()
