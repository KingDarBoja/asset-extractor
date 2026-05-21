from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, cast

from assetextractor.parsing.core.assets import Asset

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import DictAttribute
    from assetextractor.parsing.typed.common.fertility_base import AssetWithFertilityBase


@dataclass(frozen=True)
class AdditionalAttributesInfo:
    """The raw numeric attribute values (typically floats/ints)."""

    population: float
    money: float
    happiness: float
    health: float
    fire_safety: float
    belief: float
    knowledge: float
    prestige: float


@dataclass(frozen=True)
class FormattedAttributesInfo:
    """The localized and formatted string values (e.g., '+50', '+25%', '-10')."""

    population: str
    money: str
    happiness: str
    health: str
    fire_safety: str
    belief: str
    knowledge: str
    prestige: str


class AssetWithUpgradeBase(Asset):
    """Common base class providing shared extraction and formatting utilities for upgrades."""

    def _get_val_and_percent(
        self, raw_attributes_dict: Dict[str, DictAttribute | None], attr_key: str
    ) -> tuple[float, bool]:
        """Safely extracts raw float values and automatically detects if they represent percentages."""
        attr = raw_attributes_dict.get(attr_key)
        val = 0.0
        is_percent = False

        if attr is not None:
            amount_or_percent_attr = attr.find("AmountOrPercent")
            if amount_or_percent_attr is not None:
                raw_val = amount_or_percent_attr()
                if raw_val is not None:
                    val = float(raw_val)

                # Inspect string representation from the parser
                attr_str = str(amount_or_percent_attr)

                if "%" in attr_str:
                    is_percent = True

        return val, is_percent

    def _format_attribute(self, val: float, is_percent: bool) -> str:
        """Formats the parsed numeric attribute using the UI text cache mappings."""
        if val == 0.0:
            return "0"

        # Resolve formatting mappings from the active UI Text Cache
        ui_mappings = self.cache.properties.ui_text_cache

        if ui_mappings:
            # Pass the explicit percental parameter to avoid incorrect auto-detection
            return str(ui_mappings._format_value(val, percental=is_percent))

        # Fallback formatting if UITextCache is not yet loaded in context
        if is_percent:
            percent = val * 100 if -1 < val < 1 and val != 0 else val
            if percent == int(percent):
                percent_int = int(percent)
                return f"+{percent_int}%" if percent_int > 0 else f"{percent_int}%"
            return f"+{percent:.1f}%" if percent > 0 else f"{percent:.1f}%"
        else:
            if val == int(val):
                val_int = int(val)
                return f"+{val_int}" if val_int > 0 else str(val_int)
            return f"+{val:.1f}" if val > 0 else f"{val:.1f}"

    def _print_upgrade_info_base(
        self,
        raw: AdditionalAttributesInfo,
        fmt: FormattedAttributesInfo,
        title_prefix: str,
        width: int = 100,
        indent: str = "",
    ) -> None:
        """Unified internal printer shared across building and residence upgrade types."""
        # Fast exit: check if all numeric attributes are exactly zero using asdict and all()
        if all(val == 0.0 for val in asdict(raw).values()):
            return

        # Bundle everything into visual entries for cleaner filtering
        attributes_list = [
            ("Population", raw.population, fmt.population),
            ("Money", raw.money, fmt.money),
            ("Happiness", raw.happiness, fmt.happiness),
            ("Health", raw.health, fmt.health),
            ("Fire Safety", raw.fire_safety, fmt.fire_safety),
            ("Belief", raw.belief, fmt.belief),
            ("Knowledge", raw.knowledge, fmt.knowledge),
            ("Prestige", raw.prestige, fmt.prestige),
        ]

        # Filter out inactive properties
        active_entries = [entry for entry in attributes_list if entry[1] != 0.0]

        if not active_entries:
            return

        if indent:
            # We are rendering nested within an active tree hierarchy
            # Print a neat sub-header block connected directly to the parent tree line
            print(f"{indent}├── [{title_prefix} Attributes]:")
            sub_indent = indent + "│   "
            for i, (name, raw_val, fmt_val) in enumerate(active_entries):
                is_last_item = i == len(active_entries) - 1
                connector = "└── " if is_last_item else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})")
        else:
            # Standalone layout format utilizing clean, double-lined box drawing characters
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ {title_prefix} Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
            print(f"╠{border}╣")
            for name, raw_val, fmt_val in active_entries:
                print(f"║  |- {f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})".ljust(width + 1) + "║")
            print(f"╚{border}╝")


@dataclass(frozen=True)
class BuildingUpgradeInfo:
    """The processed 'BuildingUpgrade' properties as one single object."""

    additional_attributes: AdditionalAttributesInfo
    """Specific attributes from array dataset 'NeedAttributeType'. Comes from
    'BuildingUpgrade.AdditionalAttributes'."""

    formatted_attributes: FormattedAttributesInfo
    """The formatted representation of each attribute, utilizing UI text mapping rules."""


class AssetWithBuildingUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'BuildingUpgrade' property.
    This consolidates the extraction, formatting, and printing of additional building attributes.
    """

    @cached_property
    def building_upgrade_info(self) -> BuildingUpgradeInfo:
        """The structured 'BuildingUpgrade' data containing modified resource amounts."""
        # Retrieve the dictionary representing structural game modifiers
        raw_attributes_dict = cast(
            "Dict[str, DictAttribute | None]", self.find_value("BuildingUpgrade.AdditionalAttributes")
        )

        # Extract values and determine percentage statuses using shared class method
        population_val, population_is_percent = self._get_val_and_percent(raw_attributes_dict, "Population")
        money_val, money_is_percent = self._get_val_and_percent(raw_attributes_dict, "Money")
        happiness_val, happiness_is_percent = self._get_val_and_percent(raw_attributes_dict, "Happiness")
        health_val, health_is_percent = self._get_val_and_percent(raw_attributes_dict, "Health")
        fire_safety_val, fire_safety_is_percent = self._get_val_and_percent(raw_attributes_dict, "FireSafety")
        belief_val, belief_is_percent = self._get_val_and_percent(raw_attributes_dict, "Belief")
        knowledge_val, knowledge_is_percent = self._get_val_and_percent(raw_attributes_dict, "Knowledge")
        prestige_val, prestige_is_percent = self._get_val_and_percent(raw_attributes_dict, "Prestige")

        # Build raw numeric dataset
        add_attributes = AdditionalAttributesInfo(
            population=population_val,
            money=money_val,
            happiness=happiness_val,
            health=health_val,
            fire_safety=fire_safety_val,
            belief=belief_val,
            knowledge=knowledge_val,
            prestige=prestige_val,
        )

        # Build UI-ready formatted string dataset using correct percental hints
        formatted_attributes = FormattedAttributesInfo(
            population=self._format_attribute(population_val, population_is_percent),
            money=self._format_attribute(money_val, money_is_percent),
            happiness=self._format_attribute(happiness_val, happiness_is_percent),
            health=self._format_attribute(health_val, health_is_percent),
            fire_safety=self._format_attribute(fire_safety_val, fire_safety_is_percent),
            belief=self._format_attribute(belief_val, belief_is_percent),
            knowledge=self._format_attribute(knowledge_val, knowledge_is_percent),
            prestige=self._format_attribute(prestige_val, prestige_is_percent),
        )

        return BuildingUpgradeInfo(additional_attributes=add_attributes, formatted_attributes=formatted_attributes)

    def print_building_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper debugging method to print the active building upgrade information.

        Args:
            width: Global separation boundary width.
            indent: Optional string prefix to align perfectly with target layout structures.
        """
        info = self.building_upgrade_info
        if not info:
            return

        self._print_upgrade_info_base(
            raw=info.additional_attributes,
            fmt=info.formatted_attributes,
            title_prefix="Building Upgrade",
            width=width,
            indent=indent,
        )


@dataclass(frozen=True)
class ResidenceUpgradeInfo:
    """The processed 'ResidenceUpgrade' properties as one single object."""

    additional_need_attributes: AdditionalAttributesInfo
    """Specific attributes from array dataset 'NeedAttributeType'. Comes from
    'BuildingUpgrade.AdditionalAttributes'."""

    formatted_need_attributes: FormattedAttributesInfo
    """The formatted representation of each attribute, utilizing UI text mapping rules."""


class AssetWithResidenceUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'ResidenceUpgrade' property.
    This consolidates the extraction, formatting, and printing of additional building attributes.
    """

    @cached_property
    def residence_upgrade_info(self) -> ResidenceUpgradeInfo:
        """The structured 'ResidenceUpgrade' data containing modified resource amounts."""
        raw_attributes_dict = cast(
            "Dict[str, DictAttribute | None]",
            self.find_value("ResidenceUpgrade.NeedProvidedNeedAttributes.AdditionalNeedAttributes"),
        )

        # Extract values and determine percentage statuses using shared class method
        population_val, population_is_percent = self._get_val_and_percent(raw_attributes_dict, "Population")
        money_val, money_is_percent = self._get_val_and_percent(raw_attributes_dict, "Money")
        happiness_val, happiness_is_percent = self._get_val_and_percent(raw_attributes_dict, "Happiness")
        health_val, health_is_percent = self._get_val_and_percent(raw_attributes_dict, "Health")
        fire_safety_val, fire_safety_is_percent = self._get_val_and_percent(raw_attributes_dict, "FireSafety")
        belief_val, belief_is_percent = self._get_val_and_percent(raw_attributes_dict, "Belief")
        knowledge_val, knowledge_is_percent = self._get_val_and_percent(raw_attributes_dict, "Knowledge")
        prestige_val, prestige_is_percent = self._get_val_and_percent(raw_attributes_dict, "Prestige")

        # Build raw numeric dataset
        add_attributes = AdditionalAttributesInfo(
            population=population_val,
            money=money_val,
            happiness=happiness_val,
            health=health_val,
            fire_safety=fire_safety_val,
            belief=belief_val,
            knowledge=knowledge_val,
            prestige=prestige_val,
        )

        # Build UI-ready formatted string dataset using shared class formatting method
        formatted_attributes = FormattedAttributesInfo(
            population=self._format_attribute(population_val, population_is_percent),
            money=self._format_attribute(money_val, money_is_percent),
            happiness=self._format_attribute(happiness_val, happiness_is_percent),
            health=self._format_attribute(health_val, health_is_percent),
            fire_safety=self._format_attribute(fire_safety_val, fire_safety_is_percent),
            belief=self._format_attribute(belief_val, belief_is_percent),
            knowledge=self._format_attribute(knowledge_val, knowledge_is_percent),
            prestige=self._format_attribute(prestige_val, prestige_is_percent),
        )

        return ResidenceUpgradeInfo(
            additional_need_attributes=add_attributes, formatted_need_attributes=formatted_attributes
        )

    def print_residence_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper debugging method to print the active residence upgrade information.

        Args:
            width: Global separation boundary width.
            indent: Optional string prefix to align perfectly with target layout structures.
        """
        info = self.residence_upgrade_info
        if not info:
            return
        self._print_upgrade_info_base(
            raw=info.additional_need_attributes,
            fmt=info.formatted_need_attributes,
            title_prefix="Residence Upgrade",
            width=width,
            indent=indent,
        )


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
