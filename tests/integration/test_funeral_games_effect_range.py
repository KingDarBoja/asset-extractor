"""Verify the RadiusEffectRangeTarget BuffUI rendering for AreaBuff 81443.

Asset 81443 (Funeral Games of Tailteann) should render its RadiusEffectRange
buff as: icon_2d_item_scope_radius_0 | Effect range of Recreation Ground | +20%
"""


def test_funeral_games_effect_range(assets):
    asset = assets.get(81443)
    assert asset is not None, "Asset 81443 (Funeral Games of Tailteann) not found"

    area_buff = asset.find("AreaBuff")
    assert area_buff is not None, "AreaBuff property missing"

    assert area_buff.RadiusEffectRangeUpgrade() == 20.0

    target_list = area_buff.RadiusEffectRangeTarget
    assert len(target_list._value_list) == 1

    target_asset = target_list[0].Target()
    assert target_asset.guid == 81447
    assert target_asset.text.values.get("english") == "Recreation Ground"

    # PrimitiveAttribute.buff_ui is intentionally suppressed for the upgrade
    # (rendered via the target list — see attributes.py:450)
    assert area_buff.RadiusEffectRangeUpgrade.buff_ui is None

    buff_uis = target_list.buff_ui
    assert isinstance(buff_uis, list)
    assert len(buff_uis) == 1

    bu = buff_uis[0]
    assert bu is not None
    assert bu.value == "+20%"

    text_str = bu.text.values.get("english") if hasattr(bu.text, "values") else str(bu.text)
    assert text_str == "Effect range of Recreation Ground"

    icon_path = str(bu.icon)
    assert "icon_2d_item_scope_radius_0" in icon_path
