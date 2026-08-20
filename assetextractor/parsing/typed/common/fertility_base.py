from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import cast

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.typed.common.enums import SlotType


@dataclass(frozen=True)
class FertilityBaseInfo:
    """The processed 'Fertility' properties as one single object."""

    water_fertility: bool
    """Flag that controls if the fertility product requires water. Comes from
    'Fertility.WaterFertility'."""

    needs_slot: SlotType
    """Specific slot type from dataset 'SlotType'. Comes from 'Fertility.NeedsSlot'."""


class AssetWithFertilityBase(Asset):
    """
    Base class for assets that contain a 'Fertility' property.
    This consolidates the extraction, formatting, and printing of additional attributes.
    """

    @cached_property
    def fertility_info(self) -> FertilityBaseInfo:
        """The structured 'Fertility' data."""
        # Obtain the basic info nodes.
        water_fertility = cast("bool | None", self.find_value("Fertility.WaterFertility"))
        needs_slot = cast("SlotType | None", self.find_value("Fertility.NeedsSlot"))

        return FertilityBaseInfo(water_fertility=water_fertility or False, needs_slot=needs_slot or SlotType.NONE)
