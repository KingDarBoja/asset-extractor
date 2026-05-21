from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, List, cast

from assetextractor.parsing.typed.common.upgrades.common import AssetWithUpgradeBase

if TYPE_CHECKING:
    from assetextractor.parsing.typed.common.fertility_base import AssetWithFertilityBase


@dataclass(frozen=True)
class FactoryUpgradeInfo:
    """The processed 'FactoryUpgrade' properties as one single object."""

    productivity_upgrade: float
    """Added production capability, e.g. +20%."""

    added_fertility: AssetWithFertilityBase | None
    """The fertility asset added by this modifier, if any."""

    fertility_percent: int
    """Scale multiplier for the added fertility. Defaults to 100."""

    can_use_marsh: bool
    """Flag to allow building placement/production on Marsh."""

    can_use_forest: bool
    """Flag to allow building placement/production on Forest."""

    can_use_meadow: bool
    """Flag to allow building placement/production on Meadow."""


class AssetWithFactoryUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'FactoryUpgrade' property. This
    consolidates the extraction, formatting, and printing of additional
    attributes.
    """

    @cached_property
    def factory_upgrade_info(self) -> FactoryUpgradeInfo:
        """The structured 'FactoryUpgrade' data."""
        # Productivity info.
        prod_upg = cast("float | None", self.find_value("FactoryUpgrade.ProductivityUpgrade")) or 0
        # Get the fertility percent and asset with fertility info.
        added_fert_asset = cast("AssetWithFertilityBase | None", self.find_ref("FactoryUpgrade.AddedFertility"))
        fert_per = cast("int | None", self.find_value("FactoryUpgrade.FertilityPercent")) or 100

        # Get the other properties.
        can_marsh = cast("bool | None", self.find_value("FactoryUpgrade.CanUseMarsh")) or False
        can_forest = cast("bool | None", self.find_value("FactoryUpgrade.CanUseForest")) or False
        can_meadow = cast("bool | None", self.find_value("FactoryUpgrade.CanUseMeadow")) or False

        return FactoryUpgradeInfo(
            productivity_upgrade=prod_upg,
            added_fertility=added_fert_asset,
            fertility_percent=fert_per,
            can_use_marsh=can_marsh,
            can_use_forest=can_forest,
            can_use_meadow=can_meadow,
        )

    def print_factory_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper debugging method to print the active factory upgrade information.

        Args:
            width: Global separation boundary width.
            indent: Optional string prefix to align perfectly with target layout structures.
        """
        info = self.factory_upgrade_info
        if not info:
            return

        # Build active fields list
        active_entries: List[tuple[str, float | str | bool, str]] = []

        if info.productivity_upgrade != 0.0:
            fmt_prod = self._format_attribute(info.productivity_upgrade, True)
            active_entries.append(("Productivity", info.productivity_upgrade, fmt_prod))

        if info.added_fertility is not None:
            fert_name = info.added_fertility.name if hasattr(info.added_fertility, "name") else "Unknown"
            active_entries.append(("Added Fertility", f"{info.fertility_percent}%", fert_name))

        if info.can_use_marsh:
            active_entries.append(("Can Use Marsh", True, "Yes"))
        if info.can_use_forest:
            active_entries.append(("Can Use Forest", True, "Yes"))
        if info.can_use_meadow:
            active_entries.append(("Can Use Meadow", True, "Yes"))

        if not active_entries:
            return

        if indent:
            # Nested within an active tree hierarchy
            print(f"{indent}├── [Factory Upgrade Attributes]:")
            sub_indent = indent + "│   "
            for i, (name, raw_val, fmt_val) in enumerate(active_entries):
                is_last_item = i == len(active_entries) - 1
                connector = "└── " if is_last_item else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})")
        else:
            # Standalone visual border box
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ Factory Upgrade Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
            print(f"╠{border}╣")
            for name, raw_val, fmt_val in active_entries:
                print(f"║  |- {f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})".ljust(width + 1) + "║")
            print(f"╚{border}╝")
