from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, TypedDict, cast

from assetextractor.parsing.core.assets import Asset

from .common import AdditionalAttributesInfo, AssetWithUpgradeBase, FormattedAttributesInfo, UpgradeAttributeJSON

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import DictAttribute, ListAttribute


@dataclass(frozen=True)
class ResidenceNeedProvidedNeedAttributesInfo:
    """The attributes modified for a specific product inside 'ChangeNeedAttributesOf'."""

    additional_need_attributes: AdditionalAttributesInfo
    """Specific attributes from array dataset 'NeedAttributeType'. Comes from
    'BuildingUpgrade.AdditionalAttributes'."""

    formatted_need_attributes: FormattedAttributesInfo
    """The formatted representation of each attribute, utilizing UI text mapping rules."""

    change_need_attributes: List[Asset]
    """List of product-specific assets parsed from 'ChangeNeedAttributesOf'."""


@dataclass(frozen=True)
class ResidenceUpgradeInfo:
    """The processed 'ResidenceUpgrade' properties as one single object."""

    need_provided_attributes: ResidenceNeedProvidedNeedAttributesInfo
    """The 'NeedProvidedNeedAttributes' processed object."""


class ProductNeedUpgradeJSON(TypedDict):
    guid: int
    title: str


class ResidenceUpgradeJSON(TypedDict):
    attributes: List[UpgradeAttributeJSON]
    product_upgrades: List[ProductNeedUpgradeJSON]


class AssetWithResidenceUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'ResidenceUpgrade' property. This
    consolidates the extraction, formatting, printing and structural linking of
    need modifiers.
    """

    @cached_property
    def residence_upgrade_info(self) -> ResidenceUpgradeInfo:
        """The structured 'ResidenceUpgrade' data containing modified resource amounts."""
        # 1. Read general AdditionalNeedAttributes
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

        # 2. Read nested ChangeNeedAttributesOf list (if available). These are
        #    usually "Product" Assets but we only care about their GUID, name
        #    and text.
        product_upgrades: List[Asset] = []
        change_list = cast(
            "ListAttribute | None", self.find("ResidenceUpgrade.NeedProvidedNeedAttributes.ChangeNeedAttributesOf")
        )
        if change_list:
            for entry in change_list:
                prod_asset = entry.find_ref("ProvidedProduct")
                if prod_asset:
                    product_upgrades.append(prod_asset)

        return ResidenceUpgradeInfo(
            ResidenceNeedProvidedNeedAttributesInfo(
                additional_need_attributes=add_attributes,
                formatted_need_attributes=formatted_attributes,
                change_need_attributes=product_upgrades,
            )
        )

    def serialize_residence_modifiers(self) -> ResidenceUpgradeJSON:
        """Serializes residence need adjustments and product-specific upgrades to web format."""
        info = self.residence_upgrade_info
        attributes: List[UpgradeAttributeJSON] = []
        product_upgrades: List[ProductNeedUpgradeJSON] = []

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

        additional_needs = info.need_provided_attributes.additional_need_attributes
        formatted_needs = info.need_provided_attributes.formatted_need_attributes

        # General modifiers
        for attr_key, label in mapping.items():
            raw_val = cast("float", getattr(additional_needs, attr_key))
            if raw_val != 0.0:
                fmt_val = cast("str", getattr(formatted_needs, attr_key))
                attributes.append({"key": attr_key, "label": label, "value": fmt_val, "raw": float(raw_val)})

        for product_asset in info.need_provided_attributes.change_need_attributes:
            product_upgrades.append(
                {
                    "guid": product_asset.guid,
                    "title": product_asset.text() if product_asset.text else product_asset.name,
                }
            )

        return {"attributes": attributes, "product_upgrades": product_upgrades}

    def print_residence_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper debugging method to print the active residence upgrade information.

        Args:
            width: Global separation boundary width.
            indent: Optional string prefix to align perfectly with target layout structures.
        """
        info = self.residence_upgrade_info
        if not info:
            return

        # 1. Print direct general attributes
        self._print_upgrade_info_base(
            raw=info.need_provided_attributes.additional_need_attributes,
            fmt=info.need_provided_attributes.formatted_need_attributes,
            title_prefix="Residence Upgrade",
            width=width,
            indent=indent,
        )

        # 2. Print product needs list with safe layout connectors
        prods = info.need_provided_attributes.change_need_attributes
        if prods:
            if indent:
                # Use the exact child prefix (indent + "│       ") to align directly under Residence Upgrade Attributes
                sub_indent = indent + "│       "
                print(f"{sub_indent}└── [Changed Need Attributes]:")
                child_indent = sub_indent + "    "
                for i, prod in enumerate(prods):
                    is_last_prod = i == len(prods) - 1
                    connector = "└── " if is_last_prod else "├── "
                    prod_text = prod.text() if hasattr(prod, "text") and prod.text else "N/A"
                    print(f"{child_indent}{connector}{prod.name} (GUID: {prod.guid}) - {prod_text}")
            else:
                border = "═" * width
                print(f"╔{border}╗")
                print(f"║ Changed Need Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
                print(f"╠{border}╣")
                for prod in prods:
                    prod_text = prod.text() if hasattr(prod, "text") and prod.text else "N/A"
                    print(f"║  |- {prod.name} (GUID: {prod.guid}) - {prod_text}".ljust(width + 1) + "║")
                print(f"╚{border}╝")
