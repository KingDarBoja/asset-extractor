from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, cast

from assetextractor.parsing.core.assets import Asset

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import ListAttribute
    from assetextractor.parsing.typed.common.enums import (
        IslandDifficulty,
        IslandSize,
        IslandType,
        Region,
        ResourceAmount,
    )
    from assetextractor.parsing.typed.economy.fertility import Fertility
    from assetextractor.parsing.typed.map_generator.fertility_pool import FertilityPool


@dataclass(frozen=True)
class ResourceSetCondition:
    """Dataclass holding environmental and generational constraints for a resource set.

    Attributes
    ----------
    region : list[Region]
        Regions where this resource set is permitted to generate.
    island_type : list[IslandType]
        Types of islands (e.g., Starter, Pirate) this condition applies to.
    island_diff : list[IslandDifficulty]
        Difficulty constraints allowed for this set.
    res_amounts : list[ResourceAmount]
        Allowed resource densities or quantifiers (e.g., Low, High).
    island_size : list[IslandSize]
        Allowed physical configurations or map generator slot sizes.
    """

    region: list[Region]
    island_type: list[IslandType]
    island_diff: list[IslandDifficulty]
    res_amounts: list[ResourceAmount]
    island_size: list[IslandSize]


class FertilitySet(Asset, template_names="FertilitySet"):
    """Specialized Asset representing a 'FertilitySet' configurations mapping.

    This asset binds environmental generation constraints (ResourceSetCondition)
    to concrete fertility asset tables (FertilityPool).
    """

    @cached_property
    def resource_set_condition(self) -> ResourceSetCondition:
        """The structured environmental rules required to deploy this fertility set.

        Returns
        -------
        ResourceSetCondition
            A frozen container parsing out all valid regions, island types,
            difficulties, resource quantities, and dimensions.
        """
        region = cast("list[Region] | None", self.find_value("ResourceSetCondition.AllowedRegion"))
        island_type = cast("list[IslandType] | None", self.find_value("ResourceSetCondition.AllowedIslandType"))
        island_diff = cast(
            "list[IslandDifficulty] | None", self.find_value("ResourceSetCondition.AllowedIslandDifficulty")
        )
        res_amounts = cast(
            "list[ResourceAmount] | None", self.find_value("ResourceSetCondition.AllowedResourceAmounts")
        )
        island_size = cast("list[IslandSize] | None", self.find_value("ResourceSetCondition.AllowedIslandSize"))

        return ResourceSetCondition(
            region=region or [],
            island_type=island_type or [],
            island_diff=island_diff or [],
            res_amounts=res_amounts or [],
            island_size=island_size or [],
        )

    @cached_property
    def fertility_set(self) -> list[FertilityPool | Fertility]:
        """The collection of fertility pools associated with this set configuration.

        Returns
        -------
        list[FertilityPool]
            A list of valid, resolved 'FertilityPool' assets filtered to exclude
            any unresolvable references.
        """
        fertilities = cast("ListAttribute | None", self.find_value("FertilitySet.Fertilities"))
        if not fertilities:
            return []

        resolved_fertilities = (fert.find_ref("Fertility") for fert in fertilities)
        return [cast("FertilityPool | Fertility", f) for f in resolved_fertilities if f is not None]
