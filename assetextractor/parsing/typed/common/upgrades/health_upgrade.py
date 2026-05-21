from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import List, cast

from assetextractor.parsing.typed.common.upgrades.common import AssetWithUpgradeBase


@dataclass(frozen=True)
class HealthUpgradeInfo:
    """The processed 'HealthUpgrade' properties as one single object."""

    base_health_upgrade: int
    """Baseline raw HP increase/decrease."""

    self_heal_upgrade: int
    """Regeneration rate of ship."""

    self_heal_paused_time_if_attacked_upgrade: int
    """Delay cooldown (seconds) before self healing restarts after taking damage."""

    passive_ruin_repair_speed_upgrade: int
    """Passive repair speed multiplier applied to damaged structures."""

    encamped_unit_self_heal_multiplier_upgrade: int
    """Extra multiplier of self healing inside friendly territories."""


class AssetWithHealthUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'HealthUpgrade' property.
    Consolidates the extraction, formatting, and printing of ship health modifications.
    """

    @cached_property
    def health_upgrade_info(self) -> HealthUpgradeInfo:
        """The structured 'HealthUpgrade' data."""
        base_hp = cast("int | None", self.find_value("HealthUpgrade.BaseHealthUpgrade")) or 0
        self_heal = cast("int | None", self.find_value("HealthUpgrade.SelfHealUpgrade")) or 0
        paused_time = cast("int | None", self.find_value("HealthUpgrade.SelfHealPausedTimeIfAttackedUpgrade")) or 0
        repair_speed = cast("int | None", self.find_value("HealthUpgrade.PassiveRuinRepairSpeedUpgrade")) or 0
        encamped_mult = cast("int | None", self.find_value("HealthUpgrade.EncampedUnitSelfHealMultiplierUpgrade")) or 0

        return HealthUpgradeInfo(
            base_health_upgrade=base_hp,
            self_heal_upgrade=self_heal,
            self_heal_paused_time_if_attacked_upgrade=paused_time,
            passive_ruin_repair_speed_upgrade=repair_speed,
            encamped_unit_self_heal_multiplier_upgrade=encamped_mult,
        )

    def print_health_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper method to format and print HealthUpgrade values in both tree or boxed layouts."""
        info = self.health_upgrade_info
        if not info:
            return

        active_entries: List[tuple[str, int, str]] = []
        if info.base_health_upgrade != 0:
            active_entries.append(
                ("Base HP", info.base_health_upgrade, self._format_attribute(info.base_health_upgrade, False))
            )
        if info.self_heal_upgrade != 0:
            active_entries.append(
                ("Self Heal", info.self_heal_upgrade, self._format_attribute(info.self_heal_upgrade, False))
            )
        if info.self_heal_paused_time_if_attacked_upgrade != 0:
            active_entries.append(
                (
                    "Heal Delay Sec",
                    info.self_heal_paused_time_if_attacked_upgrade,
                    str(info.self_heal_paused_time_if_attacked_upgrade),
                )
            )
        if info.passive_ruin_repair_speed_upgrade != 0:
            active_entries.append(
                (
                    "Repair Speed",
                    info.passive_ruin_repair_speed_upgrade,
                    self._format_attribute(info.passive_ruin_repair_speed_upgrade, False),
                )
            )
        if info.encamped_unit_self_heal_multiplier_upgrade != 0:
            active_entries.append(
                (
                    "Encamped Mult",
                    info.encamped_unit_self_heal_multiplier_upgrade,
                    self._format_attribute(info.encamped_unit_self_heal_multiplier_upgrade, False),
                )
            )

        if not active_entries:
            return

        if indent:
            print(f"{indent}├── [Health Upgrade Attributes]:")
            sub_indent = indent + "│   "
            for i, (name, raw_val, fmt_val) in enumerate(active_entries):
                is_last = i == len(active_entries) - 1
                connector = "└── " if is_last else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})")
        else:
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ Health Upgrade Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
            print(f"╠{border}╣")
            for name, raw_val, fmt_val in active_entries:
                print(f"║  |- {f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})".ljust(width + 1) + "║")
            print(f"╚{border}╝")
