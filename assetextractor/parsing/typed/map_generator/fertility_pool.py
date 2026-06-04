from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, cast

from assetextractor.parsing.typed.common.asset_pool_base import AssetPoolBase

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import ListAttribute
    from assetextractor.parsing.typed.economy.fertility import Fertility


class FertilityPool(AssetPoolBase, template_names="FertilityPool"):
    """Specialized Asset for 'FertilityPool' with pre-computed data."""

    @cached_property
    def fertility_pool(self) -> list[Fertility]:
        """The structured 'FertilityPool' object.

        Returns
        -------
        List[Fertility]
            A list of 'Fertility' assets contained within this pool.
        """
        fert_list = cast("ListAttribute | None", self.find_value("FertilityPool.FertilityList"))
        if not fert_list:
            return []

        resolved_fertilities = (fert.find_ref("Fertility") for fert in fert_list)
        return [cast("Fertility", f) for f in resolved_fertilities if f is not None]
