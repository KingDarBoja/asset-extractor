from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, cast

from assetextractor.parsing.typed.common.cost import AssetWithCosts
from assetextractor.parsing.typed.common.maintenance import AssetWithMaintenance

if TYPE_CHECKING:
    from assetextractor.parsing.core.texts import Text


class MiniInstitutionBuilding(AssetWithCosts, AssetWithMaintenance, template_names="MiniInstitutionBuilding"):
    """
    Specialized Asset for 'MiniInstitutionBuilding' with pre-computed data.

    Examples:
        - GUID: 81021 -> Public Roman Shrine Ceres
    """

    @cached_property
    def localized_description(self) -> str:
        """Returns the ingame description of this building."""
        info_desc = cast("Text | None", self.find_value("Standard.InfoDescription"))

        return info_desc() if info_desc else "No Description"
