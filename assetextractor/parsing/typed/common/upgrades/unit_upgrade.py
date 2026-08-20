from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, List, TypedDict, cast

from .common import AssetWithUpgradeBase

if TYPE_CHECKING:
    from .common import UpgradeAttributeJSON


@dataclass(frozen=True)
class UnitUpgradeInfo:
    """The processed 'UnitUpgrade' properties as one single object."""

    # General & Economic Upgrades
    discovery_radius_upgrade: float
    reward_money_per_destroyed_building_upgrade: float
    reward_money_per_destroyed_ship_upgrade: float

    # Defense Attributes
    defense_upgrade: float
    armor_upgrade: float
    shield_upgrade: float

    # General Accuracy
    accuracy_upgrade: float
    accuracy_archer_module_upgrade: float
    accuracy_catapult_module_upgrade: float
    accuracy_ballista_module_upgrade: float

    # Distance Attack Range Percentages
    distance_attack_range_percentual_upgrade: float
    distance_attack_range_archer_module_percentual_upgrade: float
    distance_attack_range_catapult_module_percentual_upgrade: float
    distance_attack_range_ballista_module_percentual_upgrade: float

    # Offense Attributes
    offense_melee_upgrade: float
    offense_charge_upgrade: float
    offense_ranged_upgrade: float
    offense_archer_module_ranged_upgrade: float
    offense_catapult_module_ranged_upgrade: float
    offense_ballista_module_ranged_upgrade: float

    # Attack Speed Percentages
    attack_speed_archer_module_percentual_upgrade: float
    attack_speed_catapult_module_percentual_upgrade: float
    attack_speed_ballista_module_percentual_upgrade: float
    attack_speed_torch_percentual_upgrade: float
    attack_speed_ranged_percentual_upgrade: float

    # Morale & Special Tactics
    maximum_morale_upgrade: float
    attack_cone_ballista_module: float
    attack_cone_catapult_module: float


class UnitUpgradeJSON(TypedDict):
    attributes: List[UpgradeAttributeJSON]


class AssetWithUnitUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'UnitUpgrade' property.
    Consolidates the extraction, formatting, and printing of military troop upgrades.
    """

    @cached_property
    def unit_upgrade_info(self) -> UnitUpgradeInfo:
        """The structured 'UnitUpgrade' data."""
        # General & Economic
        discovery = cast("float | None", self.find_value("UnitUpgrade.DiscoveryRadiusUpgrade")) or 0.0
        reward_bld = cast("float | None", self.find_value("UnitUpgrade.RewardMoneyPerDestroyedBuildingUpgrade")) or 0.0
        reward_shp = cast("float | None", self.find_value("UnitUpgrade.RewardMoneyPerDestroyedShipUpgrade")) or 0.0

        # Defense
        defense = cast("float | None", self.find_value("UnitUpgrade.DefenseUpgrade")) or 0.0
        armor = cast("float | None", self.find_value("UnitUpgrade.ArmorUpgrade")) or 0.0
        shield = cast("float | None", self.find_value("UnitUpgrade.ShieldUpgrade")) or 0.0

        # Accuracy
        acc = cast("float | None", self.find_value("UnitUpgrade.AccuracyUpgrade")) or 0.0
        acc_arch = cast("float | None", self.find_value("UnitUpgrade.AccuracyArcherModuleUpgrade")) or 0.0
        acc_cat = cast("float | None", self.find_value("UnitUpgrade.AccuracyCatapultModuleUpgrade")) or 0.0
        acc_bal = cast("float | None", self.find_value("UnitUpgrade.AccuracyBallistaModuleUpgrade")) or 0.0

        # Distance Range
        range_gen = cast("float | None", self.find_value("UnitUpgrade.DistanceAttackRangePercentualUpgrade")) or 0.0
        range_arch = (
            cast("float | None", self.find_value("UnitUpgrade.DistanceAttackRangeArcherModulePercentualUpgrade")) or 0.0
        )
        range_cat = (
            cast("float | None", self.find_value("UnitUpgrade.DistanceAttackRangeCatapultModulePercentualUpgrade"))
            or 0.0
        )
        range_bal = (
            cast("float | None", self.find_value("UnitUpgrade.DistanceAttackRangeBallistaModulePercentualUpgrade"))
            or 0.0
        )

        # Offense
        off_melee = cast("float | None", self.find_value("UnitUpgrade.OffenseMeleeUpgrade")) or 0.0
        off_charge = cast("float | None", self.find_value("UnitUpgrade.OffenseChargeUpgrade")) or 0.0
        off_ranged = cast("float | None", self.find_value("UnitUpgrade.OffenseRangedUpgrade")) or 0.0
        off_arch = cast("float | None", self.find_value("UnitUpgrade.OffenseArcherModuleRangedUpgrade")) or 0.0
        off_cat = cast("float | None", self.find_value("UnitUpgrade.OffenseCatapultModuleRangedUpgrade")) or 0.0
        off_bal = cast("float | None", self.find_value("UnitUpgrade.OffenseBallistaModuleRangedUpgrade")) or 0.0

        # Attack Speed
        spd_arch = cast("float | None", self.find_value("UnitUpgrade.AttackSpeedArcherModulePercentualUpgrade")) or 0.0
        spd_cat = cast("float | None", self.find_value("UnitUpgrade.AttackSpeedCatapultModulePercentualUpgrade")) or 0.0
        spd_bal = cast("float | None", self.find_value("UnitUpgrade.AttackSpeedBallistaModulePercentualUpgrade")) or 0.0
        spd_torch = cast("float | None", self.find_value("UnitUpgrade.AttackSpeedTorchPercentualUpgrade")) or 0.0
        spd_ranged = cast("float | None", self.find_value("UnitUpgrade.AttackSpeedRangedPercentualUpgrade")) or 0.0

        # Morale & Special Tactics
        morale = cast("float | None", self.find_value("UnitUpgrade.MaximumMoraleUpgrade")) or 0.0
        cone_bal = cast("float | None", self.find_value("UnitUpgrade.AttackCone_BallistaModule")) or 0.0
        cone_cat = cast("float | None", self.find_value("UnitUpgrade.AttackCone_CatapultModule")) or 0.0

        return UnitUpgradeInfo(
            discovery_radius_upgrade=discovery,
            reward_money_per_destroyed_building_upgrade=reward_bld,
            reward_money_per_destroyed_ship_upgrade=reward_shp,
            defense_upgrade=defense,
            armor_upgrade=armor,
            shield_upgrade=shield,
            accuracy_upgrade=acc,
            accuracy_archer_module_upgrade=acc_arch,
            accuracy_catapult_module_upgrade=acc_cat,
            accuracy_ballista_module_upgrade=acc_bal,
            distance_attack_range_percentual_upgrade=range_gen,
            distance_attack_range_archer_module_percentual_upgrade=range_arch,
            distance_attack_range_catapult_module_percentual_upgrade=range_cat,
            distance_attack_range_ballista_module_percentual_upgrade=range_bal,
            offense_melee_upgrade=off_melee,
            offense_charge_upgrade=off_charge,
            offense_ranged_upgrade=off_ranged,
            offense_archer_module_ranged_upgrade=off_arch,
            offense_catapult_module_ranged_upgrade=off_cat,
            offense_ballista_module_ranged_upgrade=off_bal,
            attack_speed_archer_module_percentual_upgrade=spd_arch,
            attack_speed_catapult_module_percentual_upgrade=spd_cat,
            attack_speed_ballista_module_percentual_upgrade=spd_bal,
            attack_speed_torch_percentual_upgrade=spd_torch,
            attack_speed_ranged_percentual_upgrade=spd_ranged,
            maximum_morale_upgrade=morale,
            attack_cone_ballista_module=cone_bal,
            attack_cone_catapult_module=cone_cat,
        )

    def serialize_unit_modifiers(self) -> UnitUpgradeJSON:
        """Serializes military unit parameters to Web Format."""
        info = self.unit_upgrade_info
        attributes: List[UpgradeAttributeJSON] = []

        mapping = {
            # Key, Label, is_percent
            "discovery_radius_upgrade": ("Discovery Radius", False),
            "reward_money_per_destroyed_building_upgrade": ("Bld Destroy Bounty", False),
            "reward_money_per_destroyed_ship_upgrade": ("Ship Destroy Bounty", False),
            "defense_upgrade": ("Defense", False),
            "armor_upgrade": ("Armor", False),
            "shield_upgrade": ("Shield", False),
            "accuracy_upgrade": ("Accuracy", False),
            "accuracy_archer_module_upgrade": ("Archer Acc", False),
            "accuracy_catapult_module_upgrade": ("Catapult Acc", False),
            "accuracy_ballista_module_upgrade": ("Ballista Acc", False),
            "distance_attack_range_percentual_upgrade": ("Atk Range Boost", True),
            "distance_attack_range_archer_module_percentual_upgrade": ("Archer Range Boost", True),
            "distance_attack_range_catapult_module_percentual_upgrade": ("Catapult Range Boost", True),
            "distance_attack_range_ballista_module_percentual_upgrade": ("Ballista Range Boost", True),
            "offense_melee_upgrade": ("Melee Damage", False),
            "offense_charge_upgrade": ("Charge Damage", False),
            "offense_ranged_upgrade": ("Ranged Damage", False),
            "offense_archer_module_ranged_upgrade": ("Archer Damage", False),
            "offense_catapult_module_ranged_upgrade": ("Catapult Damage", False),
            "offense_ballista_module_ranged_upgrade": ("Ballista Damage", False),
            "attack_speed_archer_module_percentual_upgrade": ("Archer Speed", True),
            "attack_speed_catapult_module_percentual_upgrade": ("Catapult Speed", True),
            "attack_speed_ballista_module_percentual_upgrade": ("Ballista Speed", True),
            "attack_speed_torch_percentual_upgrade": ("Torch Speed", True),
            "attack_speed_ranged_percentual_upgrade": ("Ranged Atk Speed", True),
            "maximum_morale_upgrade": ("Morale Buff", False),
            "attack_cone_ballista_module": ("Ballista Fire Arc", False),
            "attack_cone_catapult_module": ("Catapult Fire Arc", False),
        }

        for field_name, (label, is_pct) in mapping.items():
            val = getattr(info, field_name)
            if val != 0.0:
                attributes.append(
                    {
                        "key": field_name,
                        "label": label,
                        "value": str(self._format_attribute(val, is_pct)),
                        "raw": float(val),
                    }
                )

        return {"attributes": attributes}

    def print_unit_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper method to format and print UnitUpgrade values in both tree or boxed layouts."""
        info = self.unit_upgrade_info
        if not info:
            return

        active_entries: List[tuple[str, float, str]] = []

        # Simple mapping helper for non-percentage attributes
        def add_raw(label: str, val: float):
            if val != 0.0:
                active_entries.append((label, val, self._format_attribute(val, is_percent=False)))

        # Simple mapping helper for percentage attributes
        def add_pct(label: str, val: float):
            if val != 0.0:
                active_entries.append((label, val, self._format_attribute(val, is_percent=True)))

        # Process standard numeric upgrades
        add_raw("Discovery Radius", info.discovery_radius_upgrade)
        add_raw("Bld Destroy Gold", info.reward_money_per_destroyed_building_upgrade)
        add_raw("Shp Destroy Gold", info.reward_money_per_destroyed_ship_upgrade)
        add_raw("Defense", info.defense_upgrade)
        add_raw("Armor", info.armor_upgrade)
        add_raw("Shield", info.shield_upgrade)
        add_raw("Accuracy", info.accuracy_upgrade)
        add_raw("Archer Accuracy", info.accuracy_archer_module_upgrade)
        add_raw("Catapult Acc.", info.accuracy_catapult_module_upgrade)
        add_raw("Ballista Acc.", info.accuracy_ballista_module_upgrade)

        # Process percentage attack range upgrades
        add_pct("Attack Range", info.distance_attack_range_percentual_upgrade)
        add_pct("Archer Range", info.distance_attack_range_archer_module_percentual_upgrade)
        add_pct("Catapult Range", info.distance_attack_range_catapult_module_percentual_upgrade)
        add_pct("Ballista Range", info.distance_attack_range_ballista_module_percentual_upgrade)

        # Process offensive physical damage upgrades
        add_raw("Melee Offense", info.offense_melee_upgrade)
        add_raw("Charge Damage", info.offense_charge_upgrade)
        add_raw("Ranged Damage", info.offense_ranged_upgrade)
        add_raw("Archer Damage", info.offense_archer_module_ranged_upgrade)
        add_raw("Catapult Damage", info.offense_catapult_module_ranged_upgrade)
        add_raw("Ballista Damage", info.offense_ballista_module_ranged_upgrade)

        # Process attack speed percentages
        add_pct("Archer Atk Speed", info.attack_speed_archer_module_percentual_upgrade)
        add_pct("Catapult Speed", info.attack_speed_catapult_module_percentual_upgrade)
        add_pct("Ballista Speed", info.attack_speed_ballista_module_percentual_upgrade)
        add_pct("Torch Speed", info.attack_speed_torch_percentual_upgrade)
        add_pct("Ranged Atk Speed", info.attack_speed_ranged_percentual_upgrade)

        # Morale & Special Tactics
        add_raw("Max Morale", info.maximum_morale_upgrade)
        add_raw("Ballista Cone", info.attack_cone_ballista_module)
        add_raw("Catapult Cone", info.attack_cone_catapult_module)

        if not active_entries:
            return

        if indent:
            print(f"{indent}├── [Unit Upgrade Attributes]:")
            sub_indent = indent + "│   "
            for i, (name, raw_val, fmt_val) in enumerate(active_entries):
                is_last = i == len(active_entries) - 1
                connector = "└── " if is_last else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<22} {fmt_val:<10} (Raw: {raw_val})")
        else:
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ Unit Upgrade Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
            print(f"╠{border}╣")
            for name, raw_val, fmt_val in active_entries:
                print(f"║  |- {f'[{name}]:':<22} {fmt_val:<10} (Raw: {raw_val})".ljust(width + 1) + "║")
            print(f"╚{border}╝")
