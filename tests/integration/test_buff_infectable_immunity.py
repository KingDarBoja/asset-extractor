"""Test BuffInfectableImmunity variant selection with buffs 80687 and 120101."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


def test_infectable_immunity_variants():
    """Test BuffInfectableImmunity uses correct text variants."""
    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    # Test buff 80687
    buff_80687 = assets[80687]
    print(f"\n=== Buff 80687 Test ===")
    print(f"Buff: {buff_80687}")
    print(f"Template: {buff_80687.template.name}")

    # Check for IncidentInfectableUpgrade.IncidentImmunity (BuildingBuff)
    immunity_attr = buff_80687.find("IncidentInfectableUpgrade.IncidentImmunity")
    if immunity_attr:
        print(f"\nFound IncidentInfectableUpgrade.IncidentImmunity")
        print(f"  Attribute type: {type(immunity_attr).__name__}")
        print(f"  Value: {immunity_attr.value if hasattr(immunity_attr, 'value') else 'N/A'}")

        buff_ui_list = immunity_attr.buff_ui
        if buff_ui_list:
            print(f"  BuffUI list count: {len(buff_ui_list)}")
            for i, buff_ui in enumerate(buff_ui_list):
                print(f"\n  BuffUI[{i}]:")
                print(f"    Text: {buff_ui.text}")
                if hasattr(buff_ui.text, 'values') and 'english' in buff_ui.text.values:
                    print(f"    English: {buff_ui.text.values['english']}")
                print(f"    Icon: {buff_ui.icon}")
                print(f"    Value: {buff_ui.value}")
                print(f"    Literal: {buff_ui.literal}")
        else:
            print(f"  buff_ui returned None")
    else:
        print(f"  IncidentInfectableUpgrade.IncidentImmunity not found")

    # Check for BlockedIncidentType (AreaBuff)
    blocked_attr = buff_80687.find("BlockedIncidentType")
    if blocked_attr:
        print(f"\nFound BlockedIncidentType")
        print(f"  Attribute type: {type(blocked_attr).__name__}")
        print(f"  Value: {blocked_attr.value if hasattr(blocked_attr, 'value') else 'N/A'}")

        buff_ui_list = blocked_attr.buff_ui
        if buff_ui_list:
            print(f"  BuffUI list count: {len(buff_ui_list)}")
            for i, buff_ui in enumerate(buff_ui_list):
                print(f"\n  BuffUI[{i}]:")
                print(f"    Text: {buff_ui.text}")
                if hasattr(buff_ui.text, 'values') and 'english' in buff_ui.text.values:
                    print(f"    English: {buff_ui.text.values['english']}")
                print(f"    Icon: {buff_ui.icon}")
                print(f"    Value: {buff_ui.value}")
                print(f"    Literal: {buff_ui.literal}")
        else:
            print(f"  buff_ui returned None")
    else:
        print(f"  BlockedIncidentType not found")

    # Test buff 120101
    buff_120101 = assets[120101]
    print(f"\n\n=== Buff 120101 Test ===")
    print(f"Buff: {buff_120101}")
    print(f"Template: {buff_120101.template.name}")

    # Check for IncidentInfectableUpgrade.IncidentImmunity (BuildingBuff)
    immunity_attr = buff_120101.find("IncidentInfectableUpgrade.IncidentImmunity")
    if immunity_attr:
        print(f"\nFound IncidentInfectableUpgrade.IncidentImmunity")
        print(f"  Attribute type: {type(immunity_attr).__name__}")
        print(f"  Value: {immunity_attr.value if hasattr(immunity_attr, 'value') else 'N/A'}")

        buff_ui_list = immunity_attr.buff_ui
        if buff_ui_list:
            print(f"  BuffUI list count: {len(buff_ui_list)}")
            for i, buff_ui in enumerate(buff_ui_list):
                print(f"\n  BuffUI[{i}]:")
                print(f"    Text: {buff_ui.text}")
                if hasattr(buff_ui.text, 'values') and 'english' in buff_ui.text.values:
                    print(f"    English: {buff_ui.text.values['english']}")
                print(f"    Icon: {buff_ui.icon}")
                print(f"    Value: {buff_ui.value}")
                print(f"    Literal: {buff_ui.literal}")
        else:
            print(f"  buff_ui returned None")
    else:
        print(f"  IncidentInfectableUpgrade.IncidentImmunity not found")

    # Check for BlockedIncidentType (AreaBuff)
    blocked_attr = buff_120101.find("BlockedIncidentType")
    if blocked_attr:
        print(f"\nFound BlockedIncidentType")
        print(f"  Attribute type: {type(blocked_attr).__name__}")
        print(f"  Value: {blocked_attr.value if hasattr(blocked_attr, 'value') else 'N/A'}")

        buff_ui_list = blocked_attr.buff_ui
        if buff_ui_list:
            print(f"  BuffUI list count: {len(buff_ui_list)}")
            for i, buff_ui in enumerate(buff_ui_list):
                print(f"\n  BuffUI[{i}]:")
                print(f"    Text: {buff_ui.text}")
                if hasattr(buff_ui.text, 'values') and 'english' in buff_ui.text.values:
                    print(f"    English: {buff_ui.text.values['english']}")
                print(f"    Icon: {buff_ui.icon}")
                print(f"    Value: {buff_ui.value}")
                print(f"    Literal: {buff_ui.literal}")
        else:
            print(f"  buff_ui returned None")
    else:
        print(f"  BlockedIncidentType not found")

    print(f"\n\n=== Summary ===")
    print(f"Test completed. Check output above to verify:")
    print(f"  - BuildingBuff.IncidentInfectableUpgrade.IncidentImmunity uses 'Text' variant")
    print(f"  - AreaBuff.BlockedIncidentType uses 'AreaText' variant")


if __name__ == "__main__":
    test_infectable_immunity_variants()
