from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, Sequence, Union, cast

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.typed.asset_pool_named import AssetPoolNamed
from assetextractor.parsing.typed.buffs import BuildingBuff, ShipBuff
from assetextractor.parsing.typed.buildings import AssetBuildingBase
from assetextractor.parsing.typed.common.asset_pool_base import AssetPoolBase
from assetextractor.parsing.typed.common.building import AssetWithBuilding
from assetextractor.parsing.typed.common.cost import AssetWithCosts
from assetextractor.parsing.typed.common.enums import BuffCategory, ScopeVisualization
from assetextractor.parsing.typed.common.maintenance import AssetWithMaintenance
from assetextractor.parsing.typed.factories import AssetFactoryBase

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import ListAttribute
    from assetextractor.parsing.typed.production_chain import ProductionChain


# Shared type definition for all valid buff template assets.
BuffKey = Union["BuildingBuff", "ShipBuff"]
"""TODO: Add the other asset classes into this list (if applies)."""

# Shared type definition for the production chain mapping keys to avoid repetition and errors
ChainKey = Union["ProductionChain", "AssetPoolBase", "AssetFactoryBase"]
ChainMapping = Dict[ChainKey, Dict[int, "AssetFactoryBase"]]

# Shared type definition for targets.
TargetKey = Union[AssetPoolNamed, AssetFactoryBase, AssetBuildingBase]


@dataclass(frozen=True)
class EffectInfo:
    """The processed 'Effect' properties as one single object."""

    effect_scope: ScopeVisualization
    """Specific effect scope type from dataset 'Scope'. Comes from 'Effect.EffectScope'."""

    source_category: BuffCategory
    """Specific effect source category type from dataset 'BuffCategory'. Comes from 'Effect.SourceCategory'."""

    buffs: List[BuffKey]
    """List of buffs applied to the targets."""

    targets: List[TargetKey]
    """List of targets to apply the buffs."""


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
    def targets(self) -> List[TargetKey]:
        """
        Return the list of 'AssetPoolNamed' asset targets whose members are
        impacted by this effect.
        """
        out: List[TargetKey] = []
        for entry in cast("ListAttribute", self.find("Effect.Targets")):
            target = entry.find_ref("GUID")
            if isinstance(target, (AssetPoolNamed, AssetFactoryBase, AssetBuildingBase)):
                out.append(target)
        return out

    def _get_text(self, asset: Asset, def_text: str = "N/A") -> str:
        """Safely extracts localized text from an asset."""
        return asset.text() if asset.text else def_text

    def print_buffs(self, buffs: Sequence[Asset], prefix: str = "") -> None:
        """Processes and prints buff assets with clean box-drawing tree lines."""
        if not buffs:
            return

        if prefix == "":
            print(f"{'─' * 100}")
            print(f"Buffs ({len(buffs)}):")

        for idx, buff_asset in enumerate(buffs, 1):
            is_last = idx == len(buffs)
            connector = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            print(f"{prefix}{connector}Buff #{idx}: {buff_asset.name} (GUID: {buff_asset.guid})")

            # Handle internal property upgrades if present
            if isinstance(buff_asset, BuildingBuff):
                if hasattr(buff_asset, "print_upgrade_info"):
                    buff_asset.print_upgrade_info(indent=child_prefix)
                if hasattr(buff_asset, "print_residence_upgrade_info"):
                    buff_asset.print_residence_upgrade_info(indent=child_prefix)

    def print_targets(self, targets: Sequence[Asset], chains_mapping: ChainMapping, prefix: str = "") -> None:
        """Processes and prints target assets and structural asset pools recursively.

        Args:
            targets: The sequence of target assets to loop over.
            chains_mapping: The patron's production_chains_by_target property dictionary.
            prefix: Continuous box-drawing indentation string tracking the current tree level.
        """
        if not targets:
            return

        if prefix == "":
            print(f"{'─' * 100}")
            print(f"Targets ({len(targets)}):")

        for idx, target_asset in enumerate(targets, 1):
            is_last = idx == len(targets)
            connector = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            print(f"{prefix}{connector}Target #{idx}: {target_asset.name} (GUID: {target_asset.guid})")

            # Collect available properties to maintain clean node endpoints (└── vs ├──)
            sub_rows: List[str] = []

            # 1. Construction Costs
            if isinstance(target_asset, AssetWithCosts):
                costs = target_asset.formatted_costs
                if costs:
                    sub_rows.append(f"[Costs]: {', '.join([f'{c.amount} {c.ingredient}' for c in costs])}")

            # 2. Maintenance Costs
            if isinstance(target_asset, AssetWithMaintenance):
                m_costs = target_asset.formatted_maintenance_costs
                if m_costs:
                    sub_rows.append(f"[Maintenance]: {', '.join([f'{m.amount} {m.product}' for m in m_costs])}")

            # 3. Building/Category Metadata
            if isinstance(target_asset, AssetWithBuilding):
                sub_rows.append(f"[Category Name]: {target_asset.building_info.category_name}")

            # 4. Associated Production Chain Mappings
            for chain, targets_dict in chains_mapping.items():
                if target_asset.guid in targets_dict:
                    chain_text = self._get_text(chain)
                    sub_rows.append(f"[Production Chain]: {chain.name} (GUID: {chain.guid}) - {chain_text}")

            # Print collected sub-rows with proper dangling branch resolution
            for s_idx, row_text in enumerate(sub_rows, 1):
                # An attribute row is only the true end node if there is no recursive AssetPool under it
                is_last_row = (s_idx == len(sub_rows)) and not isinstance(target_asset, AssetPoolBase)
                row_connector = "└── " if is_last_row else "├── "
                print(f"{child_prefix}{row_connector}{row_text}")

            # 5. Handle AssetPool Recursion Last (Threads perfectly below the target parent)
            if isinstance(target_asset, AssetPoolBase):
                self.print_targets(target_asset.asset_pool_list, chains_mapping, prefix=child_prefix)
