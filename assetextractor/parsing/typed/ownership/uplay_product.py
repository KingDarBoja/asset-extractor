from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, List, cast

from assetextractor.parsing.core.assets import Asset

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import ListAttribute
    from assetextractor.parsing.typed.common.enums import UplayProductType


@dataclass(frozen=True)
class UplayProductInfo:
    product_type: UplayProductType
    product_unlocks: List[Asset]


class UplayProduct(Asset, template_names="UplayProduct"):
    """Specialized Asset for 'UplayProduct' with pre-computed data."""

    @cached_property
    def uplay_product_info(self) -> UplayProductInfo:
        """
        The product info like type and list of assets unlocked via this 'Uplay'
        product.
        """
        prod_type = cast("UplayProductType", self.find_value("UplayProduct.ProductType"))
        prod_unlocks: List[Asset] = []
        for item in cast("ListAttribute", self.find("UplayProduct.UplayProductUnlocks")):
            asset = item.find_ref("UplayProductUnlock")
            if asset is not None:
                prod_unlocks.append(asset)

        return UplayProductInfo(product_type=prod_type, product_unlocks=prod_unlocks)
