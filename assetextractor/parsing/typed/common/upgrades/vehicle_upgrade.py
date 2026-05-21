from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import List, cast

from assetextractor.parsing.typed.common.upgrades.common import AssetWithUpgradeBase


@dataclass(frozen=True)
class VehicleUpgradeInfo:
    """The processed 'VehicleUpgrade' properties as one single object."""

    activate_white_flag: bool
    """Flag to avoid conflict with hostile forces."""

    activate_pirate_flag: bool
    """Flag enabling pirate state (hostile to neutral ships)."""


class AssetWithVehicleUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'VehicleUpgrade' property.
    Consolidates the extraction, formatting, and printing of naval vehicle behaviors.
    """

    @cached_property
    def vehicle_upgrade_info(self) -> VehicleUpgradeInfo:
        """The structured 'VehicleUpgrade' data."""
        white_flag = cast("bool | None", self.find_value("VehicleUpgrade.ActivateWhiteFlag")) or False
        pirate_flag = cast("bool | None", self.find_value("VehicleUpgrade.ActivatePirateFlag")) or False

        return VehicleUpgradeInfo(activate_white_flag=white_flag, activate_pirate_flag=pirate_flag)

    def print_vehicle_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper method to format and print VehicleUpgrade behaviors."""
        info = self.vehicle_upgrade_info
        if not info:
            return

        active_entries: List[tuple[str, bool, str]] = []
        if info.activate_white_flag:
            active_entries.append(("White Flag", True, "Active"))
        if info.activate_pirate_flag:
            active_entries.append(("Pirate Flag", True, "Active"))

        if not active_entries:
            return

        if indent:
            print(f"{indent}├── [Vehicle Upgrade Attributes]:")
            sub_indent = indent + "│   "
            for i, (name, raw_val, fmt_val) in enumerate(active_entries):
                is_last = i == len(active_entries) - 1
                connector = "└── " if is_last else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})")
        else:
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ Vehicle Upgrade Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
            print(f"╠{border}╣")
            for name, raw_val, fmt_val in active_entries:
                print(f"║  |- {f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})".ljust(width + 1) + "║")
            print(f"╚{border}╝")
