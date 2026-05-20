from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, Sequence, Union, cast

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.typed.asset_pool_named import AssetPoolNamed
from assetextractor.parsing.typed.buffs import BuildingBuff, ShipBuff
from assetextractor.parsing.typed.common.asset_pool_base import AssetPoolBase
from assetextractor.parsing.typed.common.building import AssetWithBuilding
from assetextractor.parsing.typed.common.cost import AssetWithCosts
from assetextractor.parsing.typed.common.enums import BuffCategory, ScopeVisualization
from assetextractor.parsing.typed.common.maintenance import AssetWithMaintenance

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import ListAttribute
    from assetextractor.parsing.typed.factories import BuildingFactoriesGroup
    from assetextractor.parsing.typed.production_chain import ProductionChain


@dataclass(frozen=True)
class EffectInfo:
    """The processed 'Effect' properties as one single object."""

    effect_scope: ScopeVisualization
    """Specific effect scope type from dataset 'Scope'. Comes from 'Effect.EffectScope'."""

    source_category: BuffCategory
    """Specific effect source category type from dataset 'BuffCategory'. Comes from 'Effect.SourceCategory'."""

    buffs: List[BuffKey]
    """List of buffs applied to the targets."""

    targets: List[AssetPoolNamed]
    """List of targets to apply the buffs."""


# Shared type definition for all valid buff template assets.
BuffKey = Union["BuildingBuff", "ShipBuff"]
"""TODO: Add the other asset classes into this list (if applies)."""

# Shared type definition for the production chain mapping keys to avoid repetition and errors
ChainKey = Union["ProductionChain", "AssetPoolBase", "BuildingFactoriesGroup"]
ChainMapping = Dict[ChainKey, Dict[int, "BuildingFactoriesGroup"]]


class AssetWithEffect(Asset):
    """
    Base class for assets that contain a 'Effect' property (this is NOT the
    same as the Template 'Effect').
    """

    @cached_property
    def effect_info(self) -> EffectInfo:
        """The structured 'Effect' (property) data."""
        # Get the literal of this effect scope and category.
        scope_text = cast("ScopeVisualization | None", self.find_value("Effect.EffectScope"))
        cat_text = cast("BuffCategory | None", self.find_value("Effect.SourceCategory"))

        return EffectInfo(
            effect_scope=scope_text or ScopeVisualization.RADIUS,
            source_category=cat_text or BuffCategory.ITEM,
            buffs=self.buffs,
            targets=self.targets,
        )

    @cached_property
    def buffs(self) -> List[BuffKey]:
        """
        Return a list of Assets that can be either 'BuildingBuff', 'ShipBuff'
        and so on.
        """
        # Populate the output list of asset buffs.
        out: List[BuffKey] = []
        for entry in cast("ListAttribute", self.find("Effect.Buffs")):
            buff = entry.find_ref("GUID")
            if isinstance(buff, (BuildingBuff, ShipBuff)):
                out.append(buff)
        return out

    @cached_property
    def targets(self) -> List[AssetPoolNamed]:
        """
        Return the list of 'AssetPoolNamed' asset targets whose members are
        impacted by this effect.
        """
        out: List[AssetPoolNamed] = []
        for entry in cast("ListAttribute", self.find("Effect.Targets")):
            target = entry.find_ref("GUID")
            if isinstance(target, AssetPoolNamed):
                out.append(target)
        return out

    def _get_text(self, asset: Asset, def_text: str = "N/A") -> str:
        """Safely extracts localized text from an asset."""
        return asset.text() if asset.text else def_text

    def print_buffs(self, buffs: Sequence[Asset]):
        """Private method to process and print buff assets."""
        print(f"{'-' * 100}")
        print(f"Buffs: {len(buffs)}")

        for buff_index, buff_asset in enumerate(buffs, 1):
            print(f"  |- {buff_index} Buff - {buff_asset.name} (GUID: {buff_asset.guid})")

    def print_targets(self, targets: Sequence[Asset], chains_mapping: ChainMapping, level: int = 0) -> None:
        """Private method to process and print target assets and asset pools recursively.

        Args:
            targets: The sequence of target assets to loop over.
            chains_mapping: The patron's production_chains_by_target property dictionary.
            level: Recursion depth formatting level.
        """
        # Print the header only at the root level
        if level == 0:
            print(f"{'-' * 100}")
            print(f"Targets: {len(targets)}")

        # Calculate indentation based on recursion depth
        indent = "  " * level

        for target_index, target_asset in enumerate(targets, 1):
            if target_index > 1:
                print(f"{'-' * 100}")

            # Print the current target with proper indentation
            print(f"{indent}  |- {target_index} Target: {target_asset.name} (GUID: {target_asset.guid})")

            # 1. Handle Recursion First
            if isinstance(target_asset, AssetPoolBase):
                self.print_targets(target_asset.asset_pool_list, chains_mapping, level + 1)
                continue  # Move to next target in loop

            # 2. Handle Construction Costs (Common to Buildings and Units)
            if isinstance(target_asset, AssetWithCosts):
                costs = target_asset.formatted_costs
                if costs:
                    cost_str = ", ".join([f"{c.amount} {c.ingredient}" for c in costs])
                    print(f"{indent}     |- [Costs]: {cost_str}")

            # 3. Handle Maintenance (Specific to Units/Ships)
            if isinstance(target_asset, AssetWithMaintenance):
                m_costs = target_asset.formatted_maintenance_costs
                if m_costs:
                    m_str = ", ".join([f"{m.amount} {m.product}" for m in m_costs])
                    print(f"{indent}     |- [Maintenance]: {m_str}")

            # 4. Handle the list of affected buildings / units assets from this target.
            if isinstance(target_asset, AssetWithBuilding):
                build_cat_name = target_asset.building_info.category_name
                print(f"{indent}     |- [Category Name]: {build_cat_name}")

            # 5. Reverse-lookup associated Production Chains matching this specific target's GUID
            for chain, targets_dict in chains_mapping.items():
                if target_asset.guid in targets_dict:
                    chain_text = self._get_text(chain)
                    print(f"{indent}     |- [Production Chain]: {chain.name} (GUID: {chain.guid}) - {chain_text}")
