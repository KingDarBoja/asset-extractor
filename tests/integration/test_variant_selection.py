"""Test that correct text variant is selected for BuffInfectableImmunity."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


def test_variant_selection():
    """Test that Text vs AreaText variants are selected correctly."""
    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    ui_cache = assets.properties.ui_text_cache

    # Get the buff struct for BuffInfectableImmunity
    if "BuffInfectableImmunity" not in ui_cache.buff_text_structs:
        print("ERROR: BuffInfectableImmunity not found in buff_text_structs")
        return

    buff_info = ui_cache.buff_text_structs["BuffInfectableImmunity"]
    buff_struct = buff_info["struct"]

    # Get both text variants
    text_variant = buff_struct.find("Text")
    areatext_variant = buff_struct.find("AreaText")

    print("=== BuffInfectableImmunity Text Variants ===")
    if text_variant:
        text_value = text_variant()
        print(f"Text variant: {text_value.values.get('english', 'N/A')}")
    else:
        print("Text variant: NOT FOUND")

    if areatext_variant:
        areatext_value = areatext_variant()
        print(f"AreaText variant: {areatext_value.values.get('english', 'N/A')}")
    else:
        print("AreaText variant: NOT FOUND")

    # Test buff 80687 (BuildingBuff with IncidentInfectableUpgrade.IncidentImmunity)
    buff_80687 = assets[80687]
    print(f"\n\n=== Buff 80687 (BuildingBuff) ===")
    print(f"Template: {buff_80687.template.name}")

    immunity_attr = buff_80687.find("IncidentInfectableUpgrade.IncidentImmunity")
    if immunity_attr:
        print(f"Found IncidentInfectableUpgrade.IncidentImmunity")
        print(f"  Parent name: {immunity_attr.parent.name if hasattr(immunity_attr, 'parent') else 'N/A'}")

        # Manually check which variant would be selected
        property_name = immunity_attr.parent.name if hasattr(immunity_attr, 'parent') else ""
        attr_name = immunity_attr.name if hasattr(immunity_attr, 'name') else ""
        print(f"  property_name={property_name}, attr_name={attr_name}")

        # Check buff type derivation
        buff_type = ui_cache.get_buff_type_name(property_name, attr_name)
        print(f"  Derived buff_type: {buff_type}")

        if buff_type == "BuffInfectableImmunity":
            if property_name == "IncidentInfectableUpgrade":
                print(f"  >>> SHOULD SELECT: Text variant")
                print(f"  >>> Expected text: {text_value.values.get('english', 'N/A')}")
            else:
                print(f"  >>> SHOULD SELECT: AreaText variant")
                print(f"  >>> Expected text: {areatext_value.values.get('english', 'N/A')}")

        # Get actual buff_ui
        buff_ui_list = immunity_attr.buff_ui
        if buff_ui_list and len(buff_ui_list) > 0:
            print(f"  Actual buff_ui text: {buff_ui_list[0].text}")
        else:
            print(f"  Actual buff_ui: None or empty")

    # Test buff 120101 (AreaBuff)
    buff_120101 = assets[120101]
    print(f"\n\n=== Buff 120101 (AreaBuff) ===")
    print(f"Template: {buff_120101.template.name}")

    # Check for BlockedIncidentType
    blocked_attr = buff_120101.find("BlockedIncidentType")
    if blocked_attr:
        print(f"Found BlockedIncidentType")
        print(f"  Parent name: {blocked_attr.parent.name if hasattr(blocked_attr, 'parent') else 'N/A'}")

        property_name = blocked_attr.parent.name if hasattr(blocked_attr, 'parent') else ""
        attr_name = blocked_attr.name if hasattr(blocked_attr, 'name') else ""
        print(f"  property_name={property_name}, attr_name={attr_name}")

        buff_type = ui_cache.get_buff_type_name(property_name, attr_name)
        print(f"  Derived buff_type: {buff_type}")

        if buff_type == "BuffInfectableImmunity":
            if property_name == "IncidentInfectableUpgrade":
                print(f"  >>> SHOULD SELECT: Text variant")
                print(f"  >>> Expected text: {text_value.values.get('english', 'N/A')}")
            else:
                print(f"  >>> SHOULD SELECT: AreaText variant")
                print(f"  >>> Expected text: {areatext_value.values.get('english', 'N/A')}")

        buff_ui_list = blocked_attr.buff_ui
        if buff_ui_list and len(buff_ui_list) > 0:
            print(f"  Actual buff_ui text: {buff_ui_list[0].text}")
        else:
            print(f"  Actual buff_ui: None or empty")
    else:
        print(f"BlockedIncidentType not found on this buff")


if __name__ == "__main__":
    test_variant_selection()
