from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import List, TypedDict, cast

from .common import AssetWithUpgradeBase, UpgradeAttributeJSON


@dataclass(frozen=True)
class TradeShipUpgradeInfo:
    """The processed 'TradeShipUpgrade' properties as one single object."""

    active_trade_price_in_percent: float
    """Trading discount/bonus value."""

    loading_speed_upgrade: float
    """Increase in loading or transfer speeds."""


class TradeShipUpgradeJSON(TypedDict):
    attributes: List[UpgradeAttributeJSON]


class AssetWithTradeShipUpgrade(AssetWithUpgradeBase):
    """
    Base class for assets that contain a 'TradeShipUpgrade' property.
    Consolidates the extraction, formatting, and printing of cargo/trading buffs.
    """

    @cached_property
    def trade_ship_upgrade_info(self) -> TradeShipUpgradeInfo:
        """The structured 'TradeShipUpgrade' data."""
        trade_price = cast("float | None", self.find_value("TradeShipUpgrade.ActiveTradePriceInPercent")) or 0.0
        loading_speed = cast("float | None", self.find_value("TradeShipUpgrade.LoadingSpeedUpgrade")) or 0.0

        return TradeShipUpgradeInfo(active_trade_price_in_percent=trade_price, loading_speed_upgrade=loading_speed)

    def serialize_trade_ship_modifiers(self) -> TradeShipUpgradeJSON:
        """Serializes cargo trading price adjustments and terminal loading modifiers."""
        info = self.trade_ship_upgrade_info
        attributes: List[UpgradeAttributeJSON] = []

        if info.active_trade_price_in_percent != 0.0:
            attributes.append(
                {
                    "key": "active_trade_price_in_percent",
                    "label": "Active Trade Price",
                    "value": str(self._format_attribute(info.active_trade_price_in_percent, is_percent=True)),
                    "raw": float(info.active_trade_price_in_percent),
                }
            )
        if info.loading_speed_upgrade != 0.0:
            attributes.append(
                {
                    "key": "loading_speed_upgrade",
                    "label": "Loading Speed",
                    "value": str(self._format_attribute(info.loading_speed_upgrade, is_percent=True)),
                    "raw": float(info.loading_speed_upgrade),
                }
            )

        return {"attributes": attributes}

    def print_trade_ship_upgrade_info(self, width: int = 100, indent: str = "") -> None:
        """Helper method to format and print TradeShip values."""
        info = self.trade_ship_upgrade_info
        if not info:
            return

        active_entries: List[tuple[str, float, str]] = []
        if info.active_trade_price_in_percent != 0.0:
            fmt_price = self._format_attribute(info.active_trade_price_in_percent, True)
            active_entries.append(("Trade Price", info.active_trade_price_in_percent, fmt_price))
        if info.loading_speed_upgrade != 0.0:
            fmt_speed = self._format_attribute(info.loading_speed_upgrade, True)
            active_entries.append(("Loading Speed", info.loading_speed_upgrade, fmt_speed))

        if not active_entries:
            return

        if indent:
            print(f"{indent}├── [Trade Ship Upgrade Attributes]:")
            sub_indent = indent + "│   "
            for i, (name, raw_val, fmt_val) in enumerate(active_entries):
                is_last = i == len(active_entries) - 1
                connector = "└── " if is_last else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})")
        else:
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ Trade Ship Upgrade Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
            print(f"╠{border}╣")
            for name, raw_val, fmt_val in active_entries:
                print(f"║  |- {f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})".ljust(width + 1) + "║")
            print(f"╚{border}╝")
