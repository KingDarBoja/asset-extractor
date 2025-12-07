"""Test incident type mapping."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


def test_incident_mapping():
    """Test get_ui_text for IncidentType literals."""
    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    ui_cache = assets.properties.ui_text_cache

    # Test the literals from buff 80687
    literals = ["Disease", "Plague"]

    for literal in literals:
        mapping = ui_cache.get_ui_text("IncidentType", literal)
        print(f"\nLiteral: {literal}")
        print(f"  Mapping: {mapping}")
        if mapping:
            print(f"  Text ID: {mapping.text_id}")
            print(f"  Icon GUID: {mapping.icon_guid}")
            print(f"  Text: {mapping.text}")
            if mapping.text and hasattr(mapping.text, 'values'):
                print(f"  English: {mapping.text.values.get('english', 'N/A')}")


if __name__ == "__main__":
    test_incident_mapping()
