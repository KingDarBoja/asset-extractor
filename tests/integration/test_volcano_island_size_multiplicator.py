"""Verify default values from properties-meta DefaultContainerValues.

VolcanoEruptionBalancing (GUID 144830) defines
``LimitedLodeIslandSizeMultiplicator`` for Small/Medium/XL/Continental but
omits Large. properties-meta.xml declares a DefaultContainerValue of 1 for
this array, so the parser must surface 1.0 for the missing Large entry
rather than the type-default 0.0.
"""

import pytest

from assetextractor.parsing.core.assets import AssetCache

VOLCANO_BALANCING_GUID = 144830
EXPECTED_MULTIPLIERS = {"Small": 0.8, "Medium": 0.9, "Large": 1.0, "XL": 1.1, "Continental": 1.2}


def _get_multiplicator(assets: AssetCache):
    balancing = assets.elements.get(VOLCANO_BALANCING_GUID)
    assert balancing is not None, f"Asset {VOLCANO_BALANCING_GUID} not found"

    config_per_region = balancing.find("VolcanoEruptionBalancing.ConfigPerRegion")
    assert config_per_region is not None, "ConfigPerRegion list missing"
    assert len(config_per_region) > 0, "ConfigPerRegion is empty"

    region_entry = next(iter(config_per_region))
    multiplicator = region_entry.find("LimitedLodeIslandSizeMultiplicator")
    assert multiplicator is not None, "LimitedLodeIslandSizeMultiplicator missing"
    return multiplicator


def test_large_island_uses_default_container_value(assets: AssetCache):
    """Large is omitted in assets.xml; properties-meta defines default 1."""
    multiplicator = _get_multiplicator(assets)

    value = multiplicator.find_value("Large.Value")
    assert value == pytest.approx(1.0), (
        f"Large multiplier should default to 1.0 from properties-meta DefaultContainerValues, got {value}"
    )


@pytest.mark.parametrize(("size", "expected"), list(EXPECTED_MULTIPLIERS.items()))
def test_island_size_multipliers(assets: AssetCache, size: str, expected: float):
    """All ConstructionAreaSize entries resolve to their intended values."""
    multiplicator = _get_multiplicator(assets)

    value = multiplicator.find_value(f"{size}.Value")
    assert value == pytest.approx(expected), f"{size} multiplier expected {expected}, got {value}"
