from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, List, cast

from assetextractor.parsing.core.assets import Asset

if TYPE_CHECKING:
    from assetextractor.parsing.core.texts import Text
    from assetextractor.parsing.typed.factories import AssetFactoryBase


@dataclass(frozen=True)
class ProductionChainBase:
    building: AssetFactoryBase
    """The final output production building. Obtained from
    'ProductionChain.Building'. This can be nested as each tier has its own
    'Building' asset."""
    tier: List[ProductionChainBase]
    """The inner list of this chain level."""


class ProductionChain(Asset, template_names="ProductionChain"):
    """Specialized Asset for 'ProductionChain' with pre-computed data."""

    @cached_property
    def localized_description(self) -> str:
        """Returns the ingame description of this building."""
        info_desc = cast("Text | None", self.find_value("Standard.InfoDescription"))

        return info_desc() if info_desc else "No Description"

    @cached_property
    def production_chain(self) -> ProductionChainBase:
        # 1. Get the top-level final output building of this entire chain
        final_building_asset = cast("AssetFactoryBase", self.find_ref("ProductionChain.Building"))

        # 2. Extract the starting root Tier 1 nodes
        raw_tier_one = self.find_value("ProductionChain.Tier1")
        tier_one_nodes = cast("List[AssetFactoryBase]", raw_tier_one) if raw_tier_one else []

        # 3. Hand off execution to the recursive parser starting at level 1
        final_tier = self._parse_tier_nodes(tier_one_nodes, level=1)

        return ProductionChainBase(building=final_building_asset, tier=final_tier)

    def _parse_tier_nodes(self, nodes: List[AssetFactoryBase], level: int) -> List[ProductionChainBase]:
        """Recursively evaluates inner production chain supplier branches."""
        parsed_elements: List[ProductionChainBase] = []

        for item in nodes:
            # Resolve the individual supplier factory building reference for this item node
            building_ref = cast("AssetFactoryBase", item.find_ref("Building"))
            if not building_ref:
                continue

            # Calculate the lookup string name for the next nested layer (e.g., 'Tier2', 'Tier3', etc.)
            next_level = level + 1
            next_tier_key = f"Tier{next_level}"

            # Look up if deeper sub-nodes are nested beneath this element
            raw_next_nodes = item.find_value(next_tier_key)
            next_nodes_list = cast("List[AssetFactoryBase] | None", raw_next_nodes)

            # If inner elements are found, dive recursively; otherwise, terminate the branch cleanly
            sub_tier = self._parse_tier_nodes(next_nodes_list, next_level) if next_nodes_list else []

            # Append the constructed hierarchy node
            parsed_elements.append(ProductionChainBase(building=building_ref, tier=sub_tier))

        return parsed_elements
