from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, TypedDict, cast

from assetextractor.parsing.typed.common.upgrades import (
    AdditionalAttributesInfo,
    AssetWithUpgradeBase,
    FormattedAttributesInfo,
    UpgradeAttributeJSON,
)

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import DictAttribute


@dataclass(frozen=True)
class AreaNeedAttributeBuffInfo:
    """The processed 'ResidenceUpgrade' properties as one single object."""

    additional_bonus_attributes: AdditionalAttributesInfo
    """Specific attributes from array dataset 'NeedAttributeType'. Comes from
    'AreaNeedAttributeBuff.BonusAttributes'."""

    formatted_bonus_attributes: FormattedAttributesInfo
    """The formatted representation of each attribute, utilizing UI text mapping rules."""


class AreaNeedAttributeBuffJSON(TypedDict):
    attributes: List[UpgradeAttributeJSON]


class AreaBuff(AssetWithUpgradeBase, template_names="AreaBuff"):
    """Specialized Asset for 'AreaBuff'."""

    @cached_property
    def area_need_attribute_buff_info(self) -> AreaNeedAttributeBuffInfo:
        """The structured 'AreaNeedAttributeBuff' data containing modified resource amounts."""
        raw_attributes_dict = cast(
            "Dict[str, DictAttribute | None]", self.find_value("AreaNeedAttributeBuff.BonusAttributes")
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

        return AreaNeedAttributeBuffInfo(
            additional_bonus_attributes=add_attributes, formatted_bonus_attributes=formatted_attributes
        )

    def serialize_area_buff_modifiers(self) -> AreaNeedAttributeBuffJSON:
        """Serializes area adjustments to Web Format."""
        info = self.area_need_attribute_buff_info
        attributes: List[UpgradeAttributeJSON] = []

        mapping = {
            "population": "Population",
            "money": "Money",
            "happiness": "Happiness",
            "health": "Health",
            "fire_safety": "Fire Safety",
            "belief": "Belief",
            "knowledge": "Knowledge",
            "prestige": "Prestige",
        }

        for attr_key, label in mapping.items():
            raw_val = getattr(info.additional_bonus_attributes, attr_key)
            if raw_val != 0.0:
                fmt_val = getattr(info.formatted_bonus_attributes, attr_key)
                attributes.append({"key": attr_key, "label": label, "value": str(fmt_val), "raw": float(raw_val)})

        return {"attributes": attributes}

    def print_area_need_attribute_buff_info(self, width: int = 100, indent: str = "") -> None:
        """Helper debugging method to print the active area need attribute buff information.

        Args:
            width: Global separation boundary width.
            indent: Optional string prefix to align perfectly with target layout structures.
        """
        info = self.area_need_attribute_buff_info
        if not info:
            return

        self._print_upgrade_info_base(
            raw=info.additional_bonus_attributes,
            fmt=info.formatted_bonus_attributes,
            title_prefix="Area Need Attribute Buff",
            width=width,
            indent=indent,
        )
