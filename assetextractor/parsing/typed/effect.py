from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, Sequence

from assetextractor.parsing.typed.asset_pool_named import AssetPoolNamed
from assetextractor.parsing.typed.common.asset_pool_base import AssetPoolBase
from assetextractor.parsing.typed.common.effect_base import AssetWithEffect
from assetextractor.parsing.typed.factories import BuildingFactoriesGroup
from assetextractor.parsing.typed.production_chain import ProductionChain, ProductionChainBase

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset


class Effect(AssetWithEffect, template_names="Effect"):
    """Specialized Asset for Effect with pre-computed data."""

    @cached_property
    def production_chains_by_target(
        self,
    ) -> Dict[ProductionChain | AssetPoolBase | BuildingFactoriesGroup, Dict[int, BuildingFactoriesGroup]]:
        """
        Dynamically clusters this effect's targets structurally.
        - Identifies structurally active complete production chains in the target pools first.
        - Binds loose regional variations and incomplete structures back into their
          parent chain contexts via factory product output/input profiles.
        - Standalone components (such as side fuel buildings) fall through safely.
        """
        mapping: Dict[ProductionChain | AssetPoolBase | BuildingFactoriesGroup, Dict[int, BuildingFactoriesGroup]] = {}

        def _get_chain_buildings(chain: ProductionChain) -> List[BuildingFactoriesGroup]:
            buildings: List[BuildingFactoriesGroup] = []

            def _traverse(node: ProductionChainBase):
                if node.building:
                    buildings.append(node.building)
                for sub in node.tier:
                    _traverse(sub)

            if hasattr(chain, "production_chain") and chain.production_chain:
                _traverse(chain.production_chain)
            return buildings

        def _find_production_chains(building: Asset) -> List[ProductionChain]:
            chains: List[ProductionChain] = []
            referenced_by = getattr(building, "referenced_by", None)
            if referenced_by:
                for ref in referenced_by.values():
                    source = getattr(ref, "source", None)
                    if source and isinstance(source, ProductionChain):
                        chains.append(source)
            return chains

        def _process_flat_buildings(pool_buildings: List[BuildingFactoriesGroup]) -> None:
            """
            Clusters a flat sequence of building factory groups by looking for
            structural production chains, regional variants, and individual singletons.
            """
            pool_guids = {b.guid for b in pool_buildings}

            # Step 1: Discover and map completely intact structural production chains
            active_chains_in_pool: List[ProductionChain] = []
            for building in pool_buildings:
                chains = _find_production_chains(building)
                for chain in chains:
                    chain_buildings = _get_chain_buildings(chain)
                    chain_guids = {b.guid for b in chain_buildings}

                    if len(chain_guids) > 0 and chain_guids.issubset(pool_guids):
                        if chain not in mapping:
                            mapping[chain] = {}
                        mapping[chain][building.guid] = building
                        if chain not in active_chains_in_pool:
                            active_chains_in_pool.append(chain)

            # Step 2: Tie regional variants and incomplete chains to discovered chains
            for building in pool_buildings:
                # Allow common foundational ingredients (like standard Pig Farms) to map across multiple chains
                already_mapped = any(
                    chain in mapping and building.guid in mapping[chain] for chain in active_chains_in_pool
                )

                fb_info = building.factory_base_info
                building_outputs = [out.product.guid for out in fb_info.outputs if out.product]

                assigned_to_chain = False

                for chain in active_chains_in_pool:
                    chain_buildings = _get_chain_buildings(chain)
                    chain_output_guids: set[int] = set()

                    for cb in chain_buildings:
                        cb_fb = cb.factory_base_info
                        for out in cb_fb.outputs:
                            if out.product:
                                chain_output_guids.add(out.product.guid)

                    # Match Condition A: Incomplete regional chain structure outputs the same underlying product GUID
                    has_shared_product = any(p_guid in chain_output_guids for p_guid in building_outputs)

                    # Match Condition B: Variant ingredient shares a matching localized text description structure
                    has_structural_counterpart = False
                    if not has_shared_product and building.text:
                        building_text_val = building.text()
                        for cb in chain_buildings:
                            if cb.text:
                                cb_text_val = cb.text()
                                if cb_text_val == building_text_val:
                                    has_structural_counterpart = True
                                    break

                    if has_shared_product or has_structural_counterpart:
                        if chain not in mapping:
                            mapping[chain] = {}
                        mapping[chain][building.guid] = building
                        assigned_to_chain = True

                # Step 3: Absolute fallback layout frame for standalone individual singletons (e.g. Charcoal Burners)
                if not assigned_to_chain and not already_mapped:
                    if building not in mapping:
                        mapping[building] = {}
                    mapping[building][building.guid] = building

        # Temporary collection for direct BuildingFactoriesGroup targets
        flat_targeted_buildings: List[BuildingFactoriesGroup] = []

        for target_pool in self.targets:
            if isinstance(target_pool, AssetPoolNamed):
                pool_named_asset = target_pool
                nested_pools = [sub for sub in pool_named_asset.asset_pool_list if isinstance(sub, AssetPoolBase)]

                if nested_pools:
                    # Vulcan Case: Nested sub-pools context (Mines & Quarries)
                    for active_pool in nested_pools:
                        pool_buildings = [
                            b for b in active_pool.asset_pool_list if isinstance(b, BuildingFactoriesGroup)
                        ]
                        pool_guids = {b.guid for b in pool_buildings}

                        for building in pool_buildings:
                            chains = _find_production_chains(building)
                            has_complete_chain = False

                            for chain in chains:
                                chain_buildings = _get_chain_buildings(chain)
                                chain_guids = {b.guid for b in chain_buildings}
                                all_present = len(chain_guids) > 0 and chain_guids.issubset(pool_guids)

                                if all_present:
                                    if chain not in mapping:
                                        mapping[chain] = {}
                                    mapping[chain][building.guid] = building
                                    has_complete_chain = True

                            if not has_complete_chain:
                                if active_pool not in mapping:
                                    mapping[active_pool] = {}
                                mapping[active_pool][building.guid] = building
                else:
                    # Neptune/Ceres/Minerva/Mars Case: Direct building pool listings
                    pool_buildings = [
                        b for b in pool_named_asset.asset_pool_list if isinstance(b, BuildingFactoriesGroup)
                    ]
                    _process_flat_buildings(pool_buildings)

            elif isinstance(target_pool, BuildingFactoriesGroup):  # type: ignore
                # Save flat BuildingFactoriesGroup targets to process collectively
                flat_targeted_buildings.append(target_pool)

        # Process all flat-targeted BuildingFactoriesGroup elements together
        if flat_targeted_buildings:
            _process_flat_buildings(flat_targeted_buildings)

        return mapping

    def print_affected_chains(self, scenario_b_only: bool = True) -> None:
        """
        Debug utility to quickly print the structural layout mappings for this effect.
        Skips execution if the effect contains no active targets.
        """
        affected_chains = self.production_chains_by_target

        # Verify if there is actually anything to print across all clusters
        if not affected_chains or all(not targets for targets in affected_chains.values()):
            return

        def _is_in_effect_targets(tgt: BuildingFactoriesGroup, targets_to_match: Sequence[Asset]) -> bool:
            """Helper to recursively check if building is part of the effect target pools."""

            def _has_asset_recursive(current: Asset, target: BuildingFactoriesGroup) -> bool:
                if current == target:
                    return True
                if isinstance(current, AssetPoolBase):
                    return any(_has_asset_recursive(sub, target) for sub in current.asset_pool_list)
                return False

            return any(_has_asset_recursive(et, tgt) for et in targets_to_match)

        def _get_chain_building_guids(chain: Asset) -> List[int]:
            """Helper to retrieve expected GUIDs for layout structure verification."""
            if isinstance(chain, AssetPoolBase):
                return [b.guid for b in chain.asset_pool_list]
            if not isinstance(chain, ProductionChain):
                return [chain.guid] if hasattr(chain, "guid") else []
            guids: List[int] = []

            def _traverse(node: ProductionChainBase) -> None:
                if node.building:
                    guids.append(node.building.guid)
                for sub in node.tier:
                    _traverse(sub)

            if hasattr(chain, "production_chain") and chain.production_chain:
                _traverse(chain.production_chain)
            return guids

        # Build Scenario B collections beforehand to check if Scenario B printing is empty
        scenario_b_output: List[
            tuple[ProductionChain | AssetPoolBase | BuildingFactoriesGroup, List[BuildingFactoriesGroup], List[int]]
        ] = []
        for chain, targets in affected_chains.items():
            active_production_assets = [
                tgt_asset for tgt_asset in targets.values() if _is_in_effect_targets(tgt_asset, self.targets)
            ]
            active_guids = {asset.guid for asset in active_production_assets}
            required_guids = _get_chain_building_guids(chain)

            if required_guids and all(b_guid in active_guids for b_guid in required_guids):
                scenario_b_output.append((chain, active_production_assets, required_guids))

        # If we only care about complete layouts (Scenario B) and none were found, skip printing entirely
        if scenario_b_only and not scenario_b_output:
            return

        # Print standard Header since we confirmed there is active output data to show
        print(f"{'=' * 100}")
        print(f" EFFECT: (Asset GUID: {self.guid})".center(100))
        print(f"{'=' * 100}")

        # --- Scenario A Printing ---
        if not scenario_b_only:
            print(" SCENARIO A: All Associated Chain/Pool Clusters ".center(100, "-"))
            for chain, targets in affected_chains.items():
                if not targets:
                    continue

                chain_text = chain.text() if chain.text else "N/A"
                print(f"Cluster: {chain.name} (GUID: {chain.guid}) -> Text: {chain_text}")
                print(f"  Affects {len(targets)} total target assets:")
                for target_guid, target_asset in targets.items():
                    print(f"    |- Target Asset: {target_asset.name} (GUID: {target_guid})")
                print("-" * 100)

        # --- Scenario B Printing ---
        print(" SCENARIO B: Structurally Complete Layouts Only ".center(100, "-"))
        for chain, active_production_assets, required_guids in scenario_b_output:
            chain_text = chain.text() if chain.text else "N/A"
            print(f"Chain GUID: {chain.guid} -> Text: {chain_text}")
            print(f"   Affects {len(active_production_assets)} active target assets inside layout:")
            for target_asset in active_production_assets:
                print(f"     |- Target Asset: {target_asset.name} (GUID: {target_asset.guid})")
            print("-" * 100)
