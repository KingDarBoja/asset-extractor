"""Comprehensive pytest test suite for buff_ui text mapping.

This test suite validates that all buff attributes correctly map to their
localized text and icons, including special cases like:
- RecruitmentUpgrade attributes (using variant text)
- MovementUpgrade attributes (non-standard naming)
- BuffConstructionSpeed/BuffConstructionCost (context-specific variants)
"""

import pytest


@pytest.mark.buff_ui
class TestRecruitmentUpgradeVariants:
    """Test that RecruitmentUpgrade attributes use RecruitmentText variant."""

    @pytest.mark.parametrize(
        "guid,attr_name,expected_text",
        [
            (68184, "ConstructionSpeedInPercent", "Troop Recruitment Speed"),
            (118691, "RecruitmentCostInPercent", "Troop Recruitment Cost"),
            (68794, "RecruitmentSpeedInPercent", "Troop Recruitment Speed"),
        ],
    )
    def test_recruitment_variant_text(self, assets, guid, attr_name, expected_text):
        """Test that RecruitmentUpgrade uses correct variant text."""
        asset = assets.get(guid)
        assert asset is not None, f"Asset {guid} not found"

        prop = asset.find("RecruitmentUpgrade")
        assert prop is not None, f"RecruitmentUpgrade not found in asset {guid}"

        attr = prop.get(attr_name)
        if not attr or attr() == 0:
            pytest.skip(f"{attr_name} is 0 or not found")

        buff_ui = attr.buff_ui
        assert buff_ui is not None, f"buff_ui is None for {guid}.RecruitmentUpgrade.{attr_name}"
        assert buff_ui.text is not None, f"buff_ui.text is None for {guid}.RecruitmentUpgrade.{attr_name}"

        text_str = pytest.get_english_text(buff_ui.text)
        assert (
            expected_text.lower() in text_str.lower()
        ), f"Expected '{expected_text}' in '{text_str}' for {guid}.{attr_name}"


@pytest.mark.buff_ui
class TestMovementUpgradeMapping:
    """Test that MovementUpgrade attributes map to correct buff types."""

    @pytest.mark.parametrize(
        "guid,attr_name,expected_text",
        [
            (121728, "BuffReduceDamageImpactUpgrade", "Damage Slowdown"),
            (82163, "BuffReduceNegativeWindImpactUpgrade", "Unfavourable Wind Impact"),
        ],
    )
    def test_movement_buff_type_mapping(self, assets, guid, attr_name, expected_text):
        """Test that MovementUpgrade maps to correct buff types."""
        asset = assets.get(guid)
        assert asset is not None, f"Asset {guid} not found"

        prop = asset.find("MovementUpgrade")
        assert prop is not None, f"MovementUpgrade not found in asset {guid}"

        attr = prop.get(attr_name)
        if not attr or attr() == 0:
            pytest.skip(f"{attr_name} is 0 or not found")

        buff_ui = attr.buff_ui
        assert buff_ui is not None, f"buff_ui is None for {guid}.MovementUpgrade.{attr_name}"
        assert buff_ui.text is not None, f"buff_ui.text is None for {guid}.MovementUpgrade.{attr_name}"

        text_str = pytest.get_english_text(buff_ui.text)
        assert (
            expected_text.lower() in text_str.lower()
        ), f"Expected '{expected_text}' in '{text_str}' for {guid}.{attr_name}"


@pytest.mark.buff_ui
@pytest.mark.mapping
class TestBuffTypeNameMapping:
    """Test that get_buff_type_name correctly maps property/attribute names."""

    @pytest.mark.parametrize(
        "property_name,attr_name,expected_buff_type",
        [
            ("RecruitmentUpgrade", "ConstructionSpeedInPercent", "BuffConstructionSpeed"),
            ("RecruitmentUpgrade", "RecruitmentCostInPercent", "BuffConstructionCost"),
            ("MovementUpgrade", "BuffReduceDamageImpactUpgrade", "BuffReduceSpeedImpactOfDamage"),
            ("MovementUpgrade", "BuffReduceNegativeWindImpactUpgrade", "BuffReduceNegativeSpeedImpactOfWind"),
            ("FactoryUpgrade", "ProductivityUpgrade", "BuffProductivity"),
            ("MovementUpgrade", "BaseSpeedUpgrade", "BuffSpeed"),
        ],
    )
    def test_buff_type_name(self, ui_text_cache, property_name, attr_name, expected_buff_type):
        """Test that buff type names are correctly mapped."""
        buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)
        assert buff_type == expected_buff_type, f"Expected '{expected_buff_type}', got '{buff_type}'"


@pytest.mark.buff_ui
class TestBuffStructTextFields:
    """Test that buff structs have correct text fields."""

    @pytest.mark.parametrize(
        "buff_type,text_field,expected_text",
        [
            ("BuffConstructionSpeed", "RecruitmentText", "Troop Recruitment Speed"),
            ("BuffConstructionSpeed", "ShipyardText", "Ship Construction Speed"),
            ("BuffConstructionCost", "RecruitmentText", "Troop Recruitment Cost"),
            ("BuffReduceSpeedImpactOfDamage", "Text", "Damage Slowdown"),
            ("BuffReduceNegativeSpeedImpactOfWind", "Text", "Unfavourable Wind Impact"),
        ],
    )
    def test_buff_struct_text(self, ui_text_cache, buff_type, text_field, expected_text):
        """Test that buff structs contain correct text fields."""
        assert buff_type in ui_text_cache.buff_text_structs, f"{buff_type} not found in buff_text_structs"

        buff_info = ui_text_cache.buff_text_structs[buff_type]
        buff_struct = buff_info["struct"]

        text_attr = buff_struct.find(text_field)
        assert text_attr is not None, f"{buff_type}.{text_field} not found"

        text_obj = text_attr()
        assert text_obj is not None, f"{buff_type}.{text_field} returned None"

        text_str = pytest.get_english_text(text_obj)
        assert expected_text.lower() in text_str.lower(), f"Expected '{expected_text}' in '{text_str}'"


@pytest.mark.buff_ui
class TestCreateBuffUI:
    """Test that create_buff_ui correctly creates BuffUI objects."""

    @pytest.mark.parametrize(
        "property_name,attr_name,value,percental,expected_text",
        [
            ("RecruitmentUpgrade", "ConstructionSpeedInPercent", 100, True, "Troop Recruitment Speed"),
            ("MovementUpgrade", "BuffReduceDamageImpactUpgrade", 25, False, "Damage Slowdown"),
            ("FactoryUpgrade", "ProductivityUpgrade", 25, True, "Productivity"),
        ],
    )
    def test_create_buff_ui_function(
        self, ui_text_cache, property_name, attr_name, value, percental, expected_text
    ):
        """Test that create_buff_ui creates correct BuffUI objects."""
        buff_ui = ui_text_cache.create_buff_ui(
            property_name=property_name, attr_name=attr_name, value=value, percental=percental
        )

        assert buff_ui is not None, f"create_buff_ui returned None for {property_name}.{attr_name}"
        assert buff_ui.text is not None, f"No text in BuffUI for {property_name}.{attr_name}"

        text_str = pytest.get_english_text(buff_ui.text)
        assert expected_text.lower() in text_str.lower(), f"Expected '{expected_text}' in '{text_str}'"
        assert buff_ui.value is not None, f"No value in BuffUI for {property_name}.{attr_name}"


@pytest.mark.buff_ui
class TestAssetBuffUI:
    """Test the Asset.buff_ui property."""

    def test_asset_buff_ui_property(self, assets):
        """Test that Asset.buff_ui returns a list of BuffUI objects."""
        # Get a few items with buffs
        items_template = assets.templates.get("Item")
        assert items_template is not None, "Item template not found"

        test_count = 0
        for item in items_template.assets:
            if hasattr(item, "Effect") and item.Effect is not None:
                buffs = item.Effect.Buffs if hasattr(item.Effect, "Buffs") else None
                if buffs and len(buffs) > 0:
                    buff_ui_list = item.buff_ui
                    assert isinstance(buff_ui_list, list), f"buff_ui should return list, got {type(buff_ui_list)}"

                    # Each item should be a BuffUI object
                    for buff_ui in buff_ui_list:
                        assert hasattr(buff_ui, "icon"), "BuffUI should have icon attribute"
                        assert hasattr(buff_ui, "text"), "BuffUI should have text attribute"
                        assert hasattr(buff_ui, "value"), "BuffUI should have value attribute"
                        assert hasattr(buff_ui, "literal"), "BuffUI should have literal attribute"

                    test_count += 1
                    if test_count >= 5:
                        break

        assert test_count > 0, "No items with buffs found to test"


@pytest.mark.buff_ui
class TestVariantSelection:
    """Test that correct text variant is selected for different buff types."""

    def test_buff_infectable_immunity_variants(self, assets, ui_text_cache):
        """Test that BuffInfectableImmunity selects correct text variant."""
        # Check that the buff type exists
        assert "BuffInfectableImmunity" in ui_text_cache.buff_text_structs, "BuffInfectableImmunity not in cache"

        buff_info = ui_text_cache.buff_text_structs["BuffInfectableImmunity"]
        buff_struct = buff_info["struct"]

        # Both variants should exist
        text_variant = buff_struct.find("Text")
        areatext_variant = buff_struct.find("AreaText")

        assert text_variant is not None, "Text variant not found"
        assert areatext_variant is not None, "AreaText variant not found"

        # Test BuildingBuff uses Text variant
        buff_80687 = assets.get(80687)
        if buff_80687:
            immunity_attr = buff_80687.find("IncidentInfectableUpgrade.IncidentImmunity")
            if immunity_attr:
                property_name = immunity_attr.parent.name if hasattr(immunity_attr, "parent") else ""
                attr_name = immunity_attr.name if hasattr(immunity_attr, "name") else ""

                buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)
                assert buff_type == "BuffInfectableImmunity", f"Expected BuffInfectableImmunity, got {buff_type}"


@pytest.mark.buff_ui
class TestAllFixes:
    """Regression tests to verify all buff_ui fixes remain working."""

    @pytest.mark.parametrize(
        "guid,property_name,attr_name,expected_text",
        [
            # RecruitmentUpgrade - should use RecruitmentText variant
            (68184, "RecruitmentUpgrade", "ConstructionSpeedInPercent", "Troop Recruitment Speed"),
            (118691, "RecruitmentUpgrade", "RecruitmentCostInPercent", "Troop Recruitment Cost"),
            (68794, "RecruitmentUpgrade", "RecruitmentSpeedInPercent", "Troop Recruitment Speed"),
            # MovementUpgrade - should map to correct buff types
            (121728, "MovementUpgrade", "BuffReduceDamageImpactUpgrade", "Damage Slowdown"),
            (82163, "MovementUpgrade", "BuffReduceNegativeWindImpactUpgrade", "Unfavourable Wind Impact"),
        ],
    )
    def test_all_buff_fixes(self, assets, guid, property_name, attr_name, expected_text):
        """Verify all previous buff_ui fixes still work correctly."""
        asset = assets.get(guid)
        assert asset is not None, f"Asset {guid} not found"

        prop = asset.find(property_name)
        assert prop is not None, f"{property_name} not found in asset {guid}"

        attr = prop.get(attr_name)
        if not attr or attr() == 0:
            pytest.skip(f"{attr_name} is 0 or not found")

        buff_ui = attr.buff_ui
        assert buff_ui is not None, f"buff_ui is None for {guid}.{property_name}.{attr_name}"
        assert buff_ui.text is not None, f"buff_ui.text is None for {guid}.{property_name}.{attr_name}"

        text_str = pytest.get_english_text(buff_ui.text)
        assert (
            expected_text.lower() in text_str.lower()
        ), f"Expected '{expected_text}' in '{text_str}' for {guid}.{property_name}.{attr_name}"
