"""Pytest test suite for automatic buff type name mapping.

Tests the UITextCache mapping functionality.
"""

import pytest


@pytest.mark.mapping
class TestBuffTypeMapping:
    """Test automatic buff type name mapping."""

    def test_buff_text_structs_loaded(self, ui_text_cache):
        """Test that buff text structs are loaded."""
        assert len(ui_text_cache.buff_text_structs) > 0, "No buff text structs loaded"
        assert "BuffProductivity" in ui_text_cache.buff_text_structs, "BuffProductivity not found"

    def test_common_buff_types_present(self, ui_text_cache):
        """Test that common buff types are present in the cache."""
        common_buff_types = [
            "BuffProductivity",
            "BuffSpeed",
            "BuffHitpoints",
            "BuffMaintenance",
            "BuffConstructionSpeed",
            "BuffConstructionCost",
        ]

        for buff_type in common_buff_types:
            assert buff_type in ui_text_cache.buff_text_structs, f"{buff_type} not found in buff_text_structs"

    def test_buff_type_name_derivation(self, ui_text_cache):
        """Test that buff type names can be derived from property/attribute names."""
        test_cases = [
            ("FactoryUpgrade", "ProductivityUpgrade", "BuffProductivity"),
            ("MovementUpgrade", "BaseSpeedUpgrade", "BuffSpeed"),
            ("MaintenanceUpgrade", "MaintenanceFactorUpgrade", "BuffMaintenance"),
        ]

        for property_name, attr_name, expected_buff_type in test_cases:
            buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)
            assert (
                buff_type == expected_buff_type
            ), f"Expected {expected_buff_type} for {property_name}.{attr_name}, got {buff_type}"

    def test_special_case_mappings(self, ui_text_cache):
        """Test special case mappings (RecruitmentUpgrade, MovementUpgrade)."""
        special_cases = [
            ("RecruitmentUpgrade", "ConstructionSpeedInPercent", "BuffConstructionSpeed"),
            ("RecruitmentUpgrade", "RecruitmentCostInPercent", "BuffConstructionCost"),
            ("MovementUpgrade", "BuffReduceDamageImpactUpgrade", "BuffReduceSpeedImpactOfDamage"),
            ("MovementUpgrade", "BuffReduceNegativeWindImpactUpgrade", "BuffReduceNegativeSpeedImpactOfWind"),
        ]

        for property_name, attr_name, expected_buff_type in special_cases:
            buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)
            assert (
                buff_type == expected_buff_type
            ), f"Expected {expected_buff_type} for {property_name}.{attr_name}, got {buff_type}"


@pytest.mark.mapping
class TestBuffMapping:
    """Test buff mapping on actual buff assets."""

    @pytest.mark.parametrize(
        "guid,description",
        [
            (51283, "Building Buff - Casponia Casta, Sacerdos Cereris"),
            (42621, "Ship Buff"),
            (80568, "Unit Buff"),
        ],
    )
    def test_buff_asset_mapping_coverage(self, assets, ui_text_cache, guid, description):
        """Test that buff assets have good mapping coverage."""
        buff_asset = assets.get(guid)
        if not buff_asset:
            pytest.skip(f"Asset {guid} not found")

        matched_count = 0
        total_count = 0

        for prop in buff_asset:
            if prop.name.endswith("Upgrade"):
                property_name = prop.name

                for attr in prop:
                    attr_name = attr.name
                    total_count += 1

                    # Get buff type name using the automatic mapping
                    buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)

                    if buff_type:
                        matched_count += 1

        # We expect at least 50% mapping coverage
        if total_count > 0:
            coverage = matched_count / total_count
            assert coverage >= 0.5, f"Mapping coverage {coverage:.1%} below 50% for {description}"

    def test_buff_mapping_comprehensive(self, assets, ui_text_cache):
        """Test buff mapping across multiple assets."""
        test_guids = [51283, 42621, 80568]
        all_matched = 0
        all_total = 0

        for guid in test_guids:
            buff_asset = assets.get(guid)
            if not buff_asset:
                continue

            for prop in buff_asset:
                if prop.name.endswith("Upgrade"):
                    property_name = prop.name

                    for attr in prop:
                        attr_name = attr.name
                        all_total += 1

                        buff_type = ui_text_cache.get_buff_type_name(property_name, attr_name)
                        if buff_type:
                            all_matched += 1

        # Overall coverage should be good
        if all_total > 0:
            coverage = all_matched / all_total
            assert coverage >= 0.6, f"Overall mapping coverage {coverage:.1%} below 60%"


@pytest.mark.mapping
class TestUITextMapping:
    """Test UI text mapping for dataset literals."""

    def test_rarity_mapping(self, ui_text_cache):
        """Test that rarity values are mapped."""
        rarities = ["Common", "Rare", "Epic", "Legendary"]

        for rarity in rarities:
            mapping = ui_text_cache.get_ui_text("Rarity", rarity)
            assert mapping is not None, f"No mapping found for Rarity.{rarity}"
            assert mapping.text_id is not None, f"No text_id for Rarity.{rarity}"

    def test_item_niche_mapping(self, ui_text_cache):
        """Test that ItemNiche values are mapped."""
        niches = ["Finance", "Religion", "Research", "Culture", "Military"]

        for niche in niches:
            mapping = ui_text_cache.get_ui_text("ItemNiche", niche)
            assert mapping is not None, f"No mapping found for ItemNiche.{niche}"
            assert mapping.text_id is not None, f"No text_id for ItemNiche.{niche}"

    def test_scope_mapping(self, ui_text_cache):
        """Test that Scope values are mapped."""
        scopes = ["Local", "Radius", "Session", "Island"]

        for scope in scopes:
            mapping = ui_text_cache.get_ui_text("Scope", scope)
            assert mapping is not None, f"No mapping found for Scope.{scope}"
            assert mapping.text_id is not None, f"No text_id for Scope.{scope}"

    def test_ui_text_cache_size(self, ui_text_cache):
        """Test that UI text cache has reasonable size."""
        assert len(ui_text_cache) > 40, f"UI text cache too small: {len(ui_text_cache)} mappings"


@pytest.mark.mapping
class TestAttributeUIProperties:
    """Test that attributes have correct UI properties."""

    def test_choice_attribute_ui_text_id(self, assets):
        """Test that Choice attributes have ui_text_id property."""
        # Get an item with Rarity attribute
        items_template = assets.templates.get("Item")
        if not items_template:
            pytest.skip("Item template not found")

        item = next(iter(items_template.assets))
        if not hasattr(item.Item, "Rarity"):
            pytest.skip("No Rarity attribute found")

        rarity_attr = item.Item.Rarity
        assert hasattr(rarity_attr, "ui_text_id"), "Choice attribute should have ui_text_id property"

        # The property should be accessible without errors
        text_id = rarity_attr.ui_text_id
        # Text ID can be None or an integer
        assert text_id is None or isinstance(text_id, int), f"ui_text_id should be int or None, got {type(text_id)}"

    def test_choice_attribute_ui_icon_guid(self, assets):
        """Test that Choice attributes have ui_icon_guid property."""
        items_template = assets.templates.get("Item")
        if not items_template:
            pytest.skip("Item template not found")

        item = next(iter(items_template.assets))
        if not hasattr(item.Item, "Rarity"):
            pytest.skip("No Rarity attribute found")

        rarity_attr = item.Item.Rarity
        assert hasattr(rarity_attr, "ui_icon_guid"), "Choice attribute should have ui_icon_guid property"

        # The property should be accessible without errors
        icon_guid = rarity_attr.ui_icon_guid
        # Icon GUID can be None or an integer
        assert (
            icon_guid is None or isinstance(icon_guid, int)
        ), f"ui_icon_guid should be int or None, got {type(icon_guid)}"

    def test_attribute_ui_text_variants(self, assets, ui_text_cache):
        """Test that attributes with variants have ui_text_variants property."""
        # Find a buff with BuffConstructionSpeed (has variants)
        buff_guid = 68184
        buff_asset = assets.get(buff_guid)

        if not buff_asset:
            pytest.skip(f"Buff asset {buff_guid} not found")

        attr = buff_asset.find("RecruitmentUpgrade.ConstructionSpeedInPercent")
        if not attr:
            pytest.skip("ConstructionSpeedInPercent not found")

        # Should have ui_text_variants property
        assert hasattr(attr, "ui_text_variants"), "Attribute should have ui_text_variants property"

        variants = attr.ui_text_variants
        # Variants can be None or a dict
        assert variants is None or isinstance(variants, dict), (
            f"ui_text_variants should be dict or None, got {type(variants)}"
        )
