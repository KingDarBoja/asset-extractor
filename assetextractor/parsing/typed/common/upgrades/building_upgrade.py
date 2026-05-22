from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, TypedDict, cast

from .common import AdditionalAttributesInfo, AssetWithUpgradeBase, FormattedAttributesInfo, UpgradeAttributeJSON

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset
    from assetextractor.parsing.core.attributes import DictAttribute, ListAttribute


class WorkforceUpgradeJSON(TypedDict):
    guid: int
    title: str


class BuildingUpgradeJSON(TypedDict):
    attributes: List[UpgradeAttributeJSON]
    additional_workforces: List[WorkforceUpgradeJSON]


@dataclass(frozen=True)
class BuildingUpgradeInfo:
    """The processed 'BuildingUpgrade' properties as one single object."""

    additional_attributes: AdditionalAttributesInfo
    """Specific attributes from array dataset 'NeedAttributeType'. Comes from
    'BuildingUpgrade.AdditionalAttributes'."""

    formatted_attributes: FormattedAttributesInfo
    """The formatted representation of each attribute, utilizing UI text mapping rules."""

    additional_workforces: List[Asset]
    """A list of resolved Asset references representing extra workforce tiers added to the building."""


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

        # Extract additional workforces block cleanly from this asset domain
        additional_workforces: List[Asset] = []
        workforces_list = cast("ListAttribute | None", self.find("BuildingUpgrade.AdditionalWorkforces"))
        if workforces_list:
            for entry in workforces_list:
                wf_asset = entry.find_ref("WorkforceGUID")
                if wf_asset:
                    additional_workforces.append(wf_asset)

        return BuildingUpgradeInfo(
            additional_attributes=add_attributes,
            formatted_attributes=formatted_attributes,
            additional_workforces=additional_workforces,
        )

    def serialize_building_modifiers(self) -> BuildingUpgradeJSON:
        """Serializes active modifiers to web format."""
        info = self.building_upgrade_info
        attributes: List[UpgradeAttributeJSON] = []
        additional_workforces: List[WorkforceUpgradeJSON] = []

        # Build modifier dictionary mapping
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
            raw_val = getattr(info.additional_attributes, attr_key)
            if raw_val != 0.0:
                fmt_val = getattr(info.formatted_attributes, attr_key)
                attributes.append({"key": attr_key, "label": label, "value": str(fmt_val), "raw": float(raw_val)})

        # Map the cached workforce assets to their final JSON representation
        for wf in info.additional_workforces:
            additional_workforces.append({"guid": wf.guid, "title": wf.text() if wf.text else wf.name})

        return {"attributes": attributes, "additional_workforces": additional_workforces}

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
