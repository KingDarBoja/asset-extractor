from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, cast

from assetextractor.parsing.core.texts import Text
from assetextractor.parsing.typed.common.effect_base import AssetWithEffect
from assetextractor.parsing.typed.common.enums import (
    ItemAllocation,
    ItemOrigin,
    NicheVisualization,
    RarityVisualization,
)

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import WandImageProto


@dataclass(frozen=True)
class ItemStandardInfo:
    """The processed 'Standard' properties as one single object."""

    std_name: str
    """The original asset name. Comes from the parent class 'name' property."""
    title: str
    """The localized asset name. Comes from the parent class 'text' property."""
    description: str
    """The localized asset description. Comes from 'Standard.InfoDescription'."""
    icon: WandImageProto | None


@dataclass(frozen=True)
class ItemInfo:
    """The processed 'Item' properties as one single object."""

    allocation: ItemAllocation
    """Specific item allocation type from dataset 'ItemAllocation'. Comes from
    'Item.Allocation'."""

    rarity: RarityVisualization
    """Specific item rarity type from dataset 'RarityVisualization'. Comes from
    'Item.Rarity'."""

    niche: NicheVisualization
    """Specific item rarity type from dataset 'NicheVisualization'. Comes from
    'Item.Niche'."""

    trade_price: int

    origin: ItemOrigin
    """Specific item origin type from dataset 'ItemOrigin'. Comes from
    'Item.Origin'."""


class Item(AssetWithEffect, template_names="Item"):
    """
    Specialized Asset for 'ItemWithBoost' (Specialists) with
    pre-computed data.
    """

    @cached_property
    def item_standard_info(self) -> ItemStandardInfo:
        """The structured 'Standard' (property) data."""
        desc_text = cast("Text | None", self.find_value("Standard.InfoDescription"))
        icon_node = self.icon

        return ItemStandardInfo(
            std_name=self.name,
            title=self.text() if self.text else "No title",
            description=desc_text() if desc_text else "No Description",
            icon=icon_node.get_image() if icon_node else None,
        )

    @cached_property
    def item_info(self) -> ItemInfo:
        """The structured 'Item' (property) data."""
        # Get the literal of allocation, rarity and niche.
        allocation_text = cast("ItemAllocation | None", self.find_value("Item.Allocation"))
        rarity_text = cast("RarityVisualization | None", self.find_value("Item.Rarity"))
        niche_text = cast("NicheVisualization | None", self.find_value("Item.Niche"))

        # Get the other properties.
        trade_value = cast("int | None", self.find_value("Item.TradePrice")) or 0
        origin_text = cast("ItemOrigin | None", self.find_value("Item.Origin"))

        return ItemInfo(
            allocation=allocation_text or ItemAllocation.VILLA,
            rarity=rarity_text or RarityVisualization.COMMON,
            niche=niche_text or NicheVisualization.NONE,
            trade_price=trade_value,
            origin=origin_text or ItemOrigin.BASE_RELEASE,
        )


class ItemWithBoost(Item, template_names="ItemWithBoost"):
    """
    Specialized Asset for 'ItemWithBoost' (Specialists with extra perks) with
    pre-computed data. These shared all the properties of a normal 'Item' but
    have an additional config called 'ItemWithBoost' where boost conditions are
    stored.
    """

    pass
