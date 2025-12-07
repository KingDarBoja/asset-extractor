"""Test BuffPassiveTradeBonus formatting with buff 77648."""

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


def test_passive_trade_bonus_formatting():
    """Test BuffPassiveTradeBonus formatting with buff 77648."""
    # Load assets
    config = Config.from_json("config.json")
    assets = AssetCache.load(config)

    # Get the buff asset
    buff = assets[77648]
    assert buff is not None, "Buff 77648 not found"

    print(f"Buff: {buff}")
    print(f"Template: {buff.template.name}")

    # Navigate to PassiveTradeReward list
    passive_trade = buff.find("AreaPassiveTradeUpgrade.PassiveTradeReward")
    assert passive_trade is not None, "PassiveTradeReward not found"
    assert len(passive_trade._value_list) > 0, "No items in PassiveTradeReward"

    print(f"\nPassiveTradeReward has {len(passive_trade._value_list)} item(s)")

    # Test the first item
    item = passive_trade[0]
    print(f"\nItem 0:")
    print(f"  RewardProduct: {item.RewardProduct() if hasattr(item, 'RewardProduct') else 'N/A'}")
    print(f"  RewardAmount: {item.RewardAmount() if hasattr(item, 'RewardAmount') else 'N/A'}")
    print(f"  SoldProduct: {item.SoldProduct() if hasattr(item, 'SoldProduct') else 'N/A'}")
    print(f"  SoldAmount: {item.SoldAmount() if hasattr(item, 'SoldAmount') else 'N/A'}")

    # Test buff_ui property
    buff_ui = item.buff_ui
    assert buff_ui is not None, "buff_ui is None"
    print(f"\nBuffUI result:")
    print(f"  Icon: {buff_ui.icon}")
    print(f"  Text: {buff_ui.text}")
    print(f"  Value: {buff_ui.value}")
    print(f"  String representation: {str(buff_ui)}")

    # Validate text content
    assert buff_ui.text is not None, "buff_ui.text is None"
    text_str = str(buff_ui.text)
    print(f"\nText string: {text_str}")

    # Check that text contains expected elements
    # Note: Product names might be in different languages, so we check the structure
    assert "1" in text_str, "Text should contain reward amount '1'"
    assert "10" in text_str, "Text should contain sold amount '10'"

    # Get English text specifically
    if hasattr(buff_ui.text, 'values') and 'english' in buff_ui.text.values:
        english_text = buff_ui.text.values['english']
        print(f"\nEnglish text: {english_text}")

        # More specific checks for English text
        assert "1" in english_text, "English text should contain '1'"
        assert "10" in english_text, "English text should contain '10'"
        assert "Garum" in english_text or "garum" in english_text.lower(), "English text should contain product 'Garum'"
        assert "Rope" in english_text or "rope" in english_text.lower(), "English text should contain product 'Rope'"

        print(f"\n[PASS] Test passed! Formatted text: {english_text}")
    else:
        print(f"\n[PASS] Test passed! Text object created: {buff_ui.text}")


if __name__ == "__main__":
    test_passive_trade_bonus_formatting()
