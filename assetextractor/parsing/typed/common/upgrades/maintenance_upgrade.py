from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, List, cast

from assetextractor.parsing.typed.common.upgrades import AssetWithUpgradeBase

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset


@dataclass(frozen=True)
class ReplaceWorkforceInfo:
    """The workforce replacement assets."""

    old_workforce: Asset
    """The original workforce asset being replaced."""

    new_workforce: Asset
    """The new workforce asset replacing the old one."""


@dataclass(frozen=True)
class MaintenanceUpgradeInfo:
    """The processed 'MaintenanceUpgrade' properties as one single object."""

    maintenance_factor_upgrade: float
    """Added/subtracted maintenance cost factor (percentage)."""

    workforce_maintenance_factor_upgrade: float
    """Added/subtracted workforce maintenance factor (percentage)."""

    replace_workforce: ReplaceWorkforceInfo | None
    """Details about workforce replacement, if any."""

    encamped_unit_scaling_factor_upgrade: float
    """Scaling factor upgrade for encamped military units."""


class AssetWithMaintenanceUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'MaintenanceUpgrade' property.
    Consolidates the extraction, formatting, and printing of maintenance modifications.
    """

    @cached_property
    def maintenance_upgrade_info(self) -> MaintenanceUpgradeInfo:
        """The structured 'MaintenanceUpgrade' data."""
        m_factor = cast("float | None", self.find_value("MaintenanceUpgrade.MaintenanceFactorUpgrade")) or 0.0
        wf_factor = cast("float | None", self.find_value("MaintenanceUpgrade.WorkforceMaintenanceFactorUpgrade")) or 0.0
        scaling_factor = (
            cast("float | None", self.find_value("MaintenanceUpgrade.EncampedUnitScalingFactorUpgrade")) or 0.0
        )

        # Extract workforce replacements
        old_wf = self.find_ref("MaintenanceUpgrade.ReplaceWorkforce.OldWorkforce")
        new_wf = self.find_ref("MaintenanceUpgrade.ReplaceWorkforce.NewWorkforce")

        replace_info = None
        if old_wf is not None and new_wf is not None:
            replace_info = ReplaceWorkforceInfo(old_workforce=old_wf, new_workforce=new_wf)

        return MaintenanceUpgradeInfo(
            maintenance_factor_upgrade=m_factor,
            workforce_maintenance_factor_upgrade=wf_factor,
            replace_workforce=replace_info,
            encamped_unit_scaling_factor_upgrade=scaling_factor,
        )

    def print_maintenance_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper method to format and print MaintenanceUpgrade values in both tree or boxed layouts."""
        info = self.maintenance_upgrade_info
        if not info:
            return

        active_entries: List[tuple[str, float | str]] = []

        if info.maintenance_factor_upgrade != 0.0:
            active_entries.append(
                ("Maintenance Factor", self._format_attribute(info.maintenance_factor_upgrade, is_percent=True))
            )
        if info.workforce_maintenance_factor_upgrade != 0.0:
            active_entries.append(
                ("Workforce Factor", self._format_attribute(info.workforce_maintenance_factor_upgrade, is_percent=True))
            )
        if info.encamped_unit_scaling_factor_upgrade != 0.0:
            active_entries.append(
                (
                    "Encamped Unit Scaling",
                    self._format_attribute(info.encamped_unit_scaling_factor_upgrade, is_percent=False),
                )
            )

        # Check if there are active numeric attributes or any workforce replacements
        if not active_entries and info.replace_workforce is None:
            return

        if indent:
            print(f"{indent}├── [Maintenance Upgrade Attributes]:")
            sub_indent = indent + "│   "

            # Print basic active entries first
            for i, (name, fmt_val) in enumerate(active_entries):
                is_last = (i == len(active_entries) - 1) and info.replace_workforce is None
                connector = "└── " if is_last else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<25} {fmt_val}")

            # Print nested workforce replacements
            if info.replace_workforce is not None:
                rw = info.replace_workforce
                print(f"{sub_indent}└── [Replace Workforce]:")
                replace_indent = sub_indent + "    "

                # Format Old Workforce
                old_name = rw.old_workforce.name if rw.old_workforce else "None"
                old_text = (
                    rw.old_workforce.text()
                    if rw.old_workforce and hasattr(rw.old_workforce, "text") and rw.old_workforce.text
                    else "N/A"
                )
                old_desc = f"{old_name} (GUID: {rw.old_workforce.guid}) - {old_text}" if rw.old_workforce else "None"

                # Format New Workforce
                new_name = rw.new_workforce.name if rw.new_workforce else "None"
                new_text = (
                    rw.new_workforce.text()
                    if rw.new_workforce and hasattr(rw.new_workforce, "text") and rw.new_workforce.text
                    else "N/A"
                )
                new_desc = f"{new_name} (GUID: {rw.new_workforce.guid}) - {new_text}" if rw.new_workforce else "None"

                print(f"{replace_indent}├── Old Workforce: {old_desc}")
                print(f"{replace_indent}└── New Workforce: {new_desc}")
        else:
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ Maintenance Upgrade Attributes (GUID: {self.guid})".ljust(width + 1) + "║")

            if active_entries:
                print(f"╠{border}╣")
                for name, fmt_val in active_entries:
                    print(f"║  |- {f'[{name}]:':<25} {fmt_val}".ljust(width + 1) + "║")

            if info.replace_workforce is not None:
                rw = info.replace_workforce
                print(f"╠{border}╣")
                print(f"║  [Replace Workforce]:".ljust(width + 1) + "║")  # noqa: F541

                old_name = rw.old_workforce.name if rw.old_workforce else "None"
                old_desc = f"{old_name} (GUID: {rw.old_workforce.guid})" if rw.old_workforce else "None"
                new_name = rw.new_workforce.name if rw.new_workforce else "None"
                new_desc = f"{new_name} (GUID: {rw.new_workforce.guid})" if rw.new_workforce else "None"

                print(f"║    |- Old Workforce: {old_desc}".ljust(width + 1) + "║")
                print(f"║    |- New Workforce: {new_desc}".ljust(width + 1) + "║")

            print(f"╚{border}╝")
