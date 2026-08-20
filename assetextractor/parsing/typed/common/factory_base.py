from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, List, cast

from assetextractor.parsing.core.assets import Asset

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import ListAttribute


@dataclass(frozen=True)
class FactoryOutput:
    product: Asset
    """The factory output 'Product' asset. For the time being, it is a generic asset."""
    amount: int
    """The 'Amount' field within this list item."""
    storage_amount: int
    """The 'StorageAmount' field within this list item."""


@dataclass(frozen=True)
class FactoryBase:
    """The 'FactoryBase' info."""

    outputs: List[FactoryOutput]
    """The list of output products assigned within this factory."""
    fuel_storage_amount: int
    cycle_time: int
    is_main_factory: bool
    needs_fuel_input: bool
    """Defines whenever a production building requires input fuel (In this case, coal)."""


class AssetWithFactoryBase(Asset):
    """Base class for assets that contain a 'AssetWithFactoryBase' info."""

    @cached_property
    def factory_base_info(self) -> FactoryBase:
        """The associated 'FactoryBase.FactoryOutputs' list of assets."""
        outputs: List[FactoryOutput] = []

        for entry in cast("ListAttribute", self.find("FactoryBase.FactoryOutputs")):
            product_asset = entry.find_ref("Product")
            amount = cast("int", entry.find_value("Amount") or 0)
            storage_amount = cast("int", entry.find_value("StorageAmount") or 0)
            if product_asset is not None:
                outputs.append(FactoryOutput(product=product_asset, amount=amount, storage_amount=storage_amount))

        fuel_storage_amount = cast("int", self.find_value("FactoryBase.FuelStorageAmount") or 0)
        cycle_time = cast("int", self.find_value("FactoryBase.CycleTime") or 0)
        is_main_factory = cast("bool", self.find_value("FactoryBase.IsMainFactory") or False)
        needs_fuel_input = cast("bool", self.find_value("FactoryBase.NeedsFuelInput") or False)

        return FactoryBase(
            outputs=outputs,
            fuel_storage_amount=fuel_storage_amount,
            cycle_time=cycle_time,
            is_main_factory=is_main_factory,
            needs_fuel_input=needs_fuel_input,
        )
