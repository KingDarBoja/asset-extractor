from dataclasses import dataclass
from functools import cached_property
from typing import List, TypedDict, cast

from .common import AssetWithUpgradeBase, UpgradeAttributeJSON


@dataclass(frozen=True)
class MovementUpgradeInfo:
    """The processed 'MovementUpgrade' properties as one single object."""

    buff_base_speed_upgrade: float
    buff_reduce_cargo_impact_upgrade: float
    buff_reduce_damage_impact_upgrade: float
    buff_reduce_negative_wind_impact_upgrade: float
    buff_reduce_positive_wind_impact_upgrade: float
    buff_favorable_wind_angle: float
    buff_transfer_speed_upgrade: float


class MovementUpgradeJSON(TypedDict):
    attributes: List[UpgradeAttributeJSON]


class AssetWithMovementUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'MovementUpgrade' property.
    Consolidates the extraction, formatting, and printing of movement modifications.
    """

    @cached_property
    def movement_upgrade_info(self) -> MovementUpgradeInfo:
        """The structured 'MovementUpgrade' data."""
        base_speed = cast("float | None", self.find_value("MovementUpgrade.BuffBaseSpeedUpgrade")) or 0.0
        cargo_impact = cast("float | None", self.find_value("MovementUpgrade.BuffReduceCargoImpactUpgrade")) or 0.0
        damage_impact = cast("float | None", self.find_value("MovementUpgrade.BuffReduceDamageImpactUpgrade")) or 0.0
        neg_wind = cast("float | None", self.find_value("MovementUpgrade.BuffReduceNegativeWindImpactUpgrade")) or 0.0
        pos_wind = cast("float | None", self.find_value("MovementUpgrade.BuffReducePositiveWindImpactUpgrade")) or 0.0
        wind_angle = cast("float | None", self.find_value("MovementUpgrade.BuffFavorableWindAngle")) or 0.0
        transfer_speed = cast("float | None", self.find_value("MovementUpgrade.BuffTransferSpeedUpgrade")) or 0.0

        return MovementUpgradeInfo(
            buff_base_speed_upgrade=base_speed,
            buff_reduce_cargo_impact_upgrade=cargo_impact,
            buff_reduce_damage_impact_upgrade=damage_impact,
            buff_reduce_negative_wind_impact_upgrade=neg_wind,
            buff_reduce_positive_wind_impact_upgrade=pos_wind,
            buff_favorable_wind_angle=wind_angle,
            buff_transfer_speed_upgrade=transfer_speed,
        )

    def serialize_movement_modifiers(self) -> MovementUpgradeJSON:
        """Serializes naval movement speed adjustment modifiers."""
        info = self.movement_upgrade_info
        attributes: List[UpgradeAttributeJSON] = []

        mapping = {
            "buff_base_speed_upgrade": ("Base Speed", True),
            "buff_reduce_cargo_impact_upgrade": ("Cargo Impact Reduc.", True),
            "buff_reduce_damage_impact_upgrade": ("Damage Impact Reduc.", True),
            "buff_reduce_negative_wind_impact_upgrade": ("Neg. Wind Reduc.", True),
            "buff_reduce_positive_wind_impact_upgrade": ("Pos. Wind Reduc.", True),
            "buff_favorable_wind_angle": ("Fav. Wind Angle", False),
            "buff_transfer_speed_upgrade": ("Transfer Speed", True),
        }

        for attr_key, (label, is_pct) in mapping.items():
            val = getattr(info, attr_key)
            if val != 0.0:
                attributes.append(
                    {
                        "key": attr_key,
                        "label": label,
                        "value": str(self._format_attribute(val, is_pct)),
                        "raw": float(val),
                    }
                )

        return {"attributes": attributes}

    def print_movement_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper method to format and print MovementUpgrade values in both tree or boxed layouts."""
        info = self.movement_upgrade_info
        if not info:
            return

        active_entries: List[tuple[str, float, str]] = []
        if info.buff_base_speed_upgrade != 0.0:
            active_entries.append(
                ("Base Speed", info.buff_base_speed_upgrade, self._format_attribute(info.buff_base_speed_upgrade, True))
            )
        if info.buff_reduce_cargo_impact_upgrade != 0.0:
            active_entries.append(
                (
                    "Cargo Impact Reduc.",
                    info.buff_reduce_cargo_impact_upgrade,
                    self._format_attribute(info.buff_reduce_cargo_impact_upgrade, True),
                )
            )
        if info.buff_reduce_damage_impact_upgrade != 0.0:
            active_entries.append(
                (
                    "Damage Impact Reduc.",
                    info.buff_reduce_damage_impact_upgrade,
                    self._format_attribute(info.buff_reduce_damage_impact_upgrade, True),
                )
            )
        if info.buff_reduce_negative_wind_impact_upgrade != 0.0:
            active_entries.append(
                (
                    "Neg. Wind Reduc.",
                    info.buff_reduce_negative_wind_impact_upgrade,
                    self._format_attribute(info.buff_reduce_negative_wind_impact_upgrade, True),
                )
            )
        if info.buff_reduce_positive_wind_impact_upgrade != 0.0:
            active_entries.append(
                (
                    "Pos. Wind Reduc.",
                    info.buff_reduce_positive_wind_impact_upgrade,
                    self._format_attribute(info.buff_reduce_positive_wind_impact_upgrade, True),
                )
            )
        if info.buff_favorable_wind_angle != 0.0:
            active_entries.append(
                ("Fav. Wind Angle", info.buff_favorable_wind_angle, str(info.buff_favorable_wind_angle))
            )
        if info.buff_transfer_speed_upgrade != 0.0:
            active_entries.append(
                (
                    "Transfer Speed",
                    info.buff_transfer_speed_upgrade,
                    self._format_attribute(info.buff_transfer_speed_upgrade, True),
                )
            )

        if not active_entries:
            return

        if indent:
            print(f"{indent}├── [Movement Upgrade Attributes]:")
            sub_indent = indent + "│   "
            for i, (name, raw_val, fmt_val) in enumerate(active_entries):
                is_last = i == len(active_entries) - 1
                connector = "└── " if is_last else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<20} {fmt_val:<10} (Raw: {raw_val})")
        else:
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ Movement Upgrade Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
            print(f"╠{border}╣")
            for name, raw_val, fmt_val in active_entries:
                print(f"║  |- {f'[{name}]:':<20} {fmt_val:<10} (Raw: {raw_val})".ljust(width + 1) + "║")
            print(f"╚{border}╝")
