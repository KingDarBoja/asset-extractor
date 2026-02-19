"""Test that ProductivityUpgrade buff values include the % sign.

Regression test for Anno 1.4 game data change: ProductivityUpgrade XML nodes
changed from <Percental>1</Percental> to <Percental>0</Percental> for positive
productivity buffs.  Our code must override this to always display productivity
as a percentage (e.g. "+20%" not "+20").
"""

import pytest


@pytest.mark.buff_ui
class TestProductivityUpgradePercent:
    """ProductivityUpgrade must always be formatted as a percentage."""

    @pytest.mark.parametrize(
        "item_guid, buff_guid, expected_value",
        [
            # Elephant Handler: ProductivityUpgrade 20 → "+20%"
            (44431, 44432, "+20%"),
            # Servia Bellia, Lily of the Coast: ProductivityUpgrade 25 → "+25%"
            (95403, None, "+25%"),
            # Virtuous Volunteer: ProductivityUpgrade 15 → "+15%"
            (96819, None, "+15%"),
        ],
    )
    def test_productivity_has_percent_sign(self, assets, item_guid, buff_guid, expected_value):
        """ProductivityUpgrade buff_ui value must contain a '%' sign."""
        item = assets.get(item_guid)
        assert item is not None, f"Item {item_guid} not found"

        # Collect all buff_ui values labelled 'Productivity' reachable from the item
        productivity_values: list[str] = []

        effect_buffs = item.find("Effect.Buffs")
        assert effect_buffs is not None, f"No Effect.Buffs on item {item_guid}"

        for entry in effect_buffs:
            guid_attr = entry.find("GUID")  # type: ignore[arg-type]
            if guid_attr is None:
                continue
            buff_asset = assets.get(guid_attr.guid)
            if buff_asset is None:
                continue

            for bui in buff_asset.buff_ui:
                text_str = bui.text() if callable(bui.text) else str(bui.text or "")
                if "productivity" in text_str.lower() and bui.value:
                    productivity_values.append(bui.value)

        assert productivity_values, (
            f"No Productivity buff_ui found for item {item_guid}. "
            "Check that the item has a FactoryUpgrade.ProductivityUpgrade buff."
        )

        for val in productivity_values:
            assert "%" in val, (
                f"Productivity buff value {val!r} for item {item_guid} is missing the '%%' sign. "
                "Expected a value like '+20%%'."
            )
            assert val == expected_value or expected_value in val, (
                f"Expected productivity value {expected_value!r} for item {item_guid}, got {val!r}"
            )

    def test_productivity_upgrade_attribute_percental(self, assets):
        """UpgradeAttribute.buff_ui for ProductivityUpgrade must include '%' regardless of XML Percental flag."""
        # Buff 44432 has <Percental>0</Percental> in 1.4 XML but must still format as %
        buff = assets.get(44432)
        assert buff is not None, "Buff 44432 (Elephant Handler buff) not found"

        prod_attr = buff.find("FactoryUpgrade.ProductivityUpgrade")
        assert prod_attr is not None, "ProductivityUpgrade not found in buff 44432"
        assert prod_attr.value == 20.0, f"Expected ProductivityUpgrade value 20.0, got {prod_attr.value!r}"

        bui = prod_attr.buff_ui
        assert bui is not None, "buff_ui is None for ProductivityUpgrade"
        assert bui.value is not None, "buff_ui.value is None for ProductivityUpgrade"
        assert "%" in bui.value, (
            f"ProductivityUpgrade buff_ui value {bui.value!r} is missing '%%'. "
            "The XML has <Percental>0</Percental> in 1.4, but productivity is always a percentage."
        )
        assert bui.value == "+20%", f"Expected '+20%%', got {bui.value!r}"
