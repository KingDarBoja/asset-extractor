from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Sequence, TypedDict, Union, cast

from assetextractor.conversion.statistics.icon_processor import IconProcessor
from assetextractor.parsing.core.texts import StandardTextConverter, Text
from assetextractor.parsing.typed.asset_pool_base import AssetPoolBase
from assetextractor.parsing.typed.building import AssetWithBuilding
from assetextractor.parsing.typed.cost import AssetWithCosts
from assetextractor.parsing.typed.maintenance import AssetWithMaintenance
from assetextractor.parsing.typed.patron import Patron
from assetextractor.parsing.typed.production_chain import ProductionChain

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset, AssetCache
    from assetextractor.parsing.typed.effect import Effect
    from assetextractor.parsing.typed.factories import BuildingFactoriesGroup
    from assetextractor.parsing.typed.production_chain import ProductionChainBase

# Define a shared type for the production chain mapping keys to avoid repetition and errors
ChainKey = Union["ProductionChain", "AssetPoolBase", "BuildingFactoriesGroup"]
ChainMapping = Dict[ChainKey, Dict[int, "BuildingFactoriesGroup"]]

# --- Helper JSON Structures ---


class MilestoneJSON(TypedDict):
    devotion: int
    buff_scaling: int


class ProductionAssetInfo(TypedDict):
    guid: int
    name: str
    text: str


class AffectedChainInfo(TypedDict):
    name: str
    text: str
    production_assets: List[ProductionAssetInfo]


class LocalEffectJSON(TypedDict):
    title: str
    description: str
    milestones: List[MilestoneJSON]
    affected_chains: Dict[str, AffectedChainInfo]


class VenerationEffectJSON(TypedDict):
    title: str
    description: str


class ShrineItemJSON(TypedDict):
    guid: int
    title: str


class ShrineEffectJSON(TypedDict):
    title: str
    guid: int
    shrines: List[ShrineItemJSON]


class ExaltationEffectJSON(TypedDict):
    title: str
    description: str


class PortraitJSON(TypedDict):
    big: str
    small: str


class PatronItemJSON(TypedDict):
    """Patron output JSON structure."""

    uid: int
    canon_name: str
    title: str
    description: str
    icon_url: str
    canon_icon_name: str
    local_effects: List[LocalEffectJSON]
    veneration_effect: VenerationEffectJSON
    shrine_effect: ShrineEffectJSON
    exaltation_effects: List[ExaltationEffectJSON]
    portraits: PortraitJSON


class PatronExtractor:
    """Main orchestrator for extracting patrons from Anno 117 assets."""

    # Dynamic format variable controlling visual separation lines globally
    DEFAULT_PRINT_WIDTH = 100

    def __init__(self, assets: AssetCache, language: str = "english"):
        """Initialize the patrons extractor.

        Args:
            assets: Asset cache with loaded assets
            language: Language for text localization (default: "english")
        """
        self.assets = assets
        self.language = language
        self.texts = assets.texts
        self.patrons: Dict[int, Patron] = {}  # Stores results after extract_all()
        self.print_width = self.DEFAULT_PRINT_WIDTH

    def _prepare_converter(self):
        """Ensures the shared cache is using this extractor's language."""
        self.assets.texts.converter = StandardTextConverter(self.language)

    def extract_all(self) -> Dict[int, Patron]:
        """
        Extracts all Patron assets and saves them into self.patrons.

        Returns:
            Dict[int, Patron]: A map of Patron GUID to Patron instance.
        """
        self._prepare_converter()

        template = self.assets.templates.get("Patron")
        if not template:
            self.patrons = {}
            return {}

        # Extract raw assets
        raw_map = {a.guid: a for a in template.assets if isinstance(a, Patron)}

        # Sort by GUID and re-insert into a new dict to lock the order
        self.patrons = {guid: raw_map[guid] for guid in sorted(raw_map.keys())}

        return self.patrons

    def _get_text(self, asset: Asset) -> str:
        """Safely extracts localized text from an asset."""
        if hasattr(asset, "text") and asset.text:
            return asset.text() if asset.text else str(asset.text)
        return "N/A"

    def _is_in_effect_targets(self, tgt: BuildingFactoriesGroup, targets_to_match: Sequence[Asset]) -> bool:
        """
        Recursively checks if a given target asset is found within a sequence of effect targets,
        drilling down into nested AssetPoolBase structures when encountered.
        """

        def _has_asset_recursive(current: Asset, target: BuildingFactoriesGroup) -> bool:
            if current == target:
                return True
            if isinstance(current, AssetPoolBase):
                return any(_has_asset_recursive(sub, target) for sub in current.asset_pool_list)
            return False

        return any(_has_asset_recursive(et, tgt) for et in targets_to_match)

    def _get_chain_building_guids(self, chain: ChainKey) -> List[int]:
        """Extracts all expected structural building GUIDs defined within a chain, pool, or individual factory."""
        if isinstance(chain, AssetPoolBase):
            return [b.guid for b in chain.asset_pool_list if hasattr(b, "guid")]

        # If the "chain" is actually just a single building (fallback case)
        if not isinstance(chain, ProductionChain):
            return [chain.guid] if hasattr(chain, "guid") else []

        guids: List[int] = []

        def _traverse(node: ProductionChainBase) -> None:
            if node.building:
                guids.append(node.building.guid)
            for sub in node.tier:
                _traverse(sub)

        # Check for ProductionChain template structure
        if hasattr(chain, "production_chain") and chain.production_chain:
            _traverse(chain.production_chain)
        return guids

    def _get_unique_chain_texts_for_effect(
        self, effect_targets: Sequence[Asset], chains_mapping: ChainMapping
    ) -> List[str]:
        """
        Helper to find unique production chain text values applicable ONLY to a
        specific effect's targets, ensuring the chain/pool is complete under the
        given active target parameters.
        """
        unique_chain_texts: List[str] = []

        # Use our clean reversed property to loop through active chains
        for chain, targets_dict in chains_mapping.items():
            # Track all matched/active building GUIDs for this chain under the current effect targets
            active_guids = {
                tgt_asset.guid
                for tgt_asset in targets_dict.values()
                if self._is_in_effect_targets(tgt_asset, effect_targets)
            }

            # Enforce completeness rule
            is_complete = False
            if isinstance(chain, AssetPoolBase):
                is_complete = len(active_guids) > 0
            else:
                # Get the total required buildings defined in the chain template layout
                required_guids = self._get_chain_building_guids(chain)
                is_complete = required_guids and all(b_guid in active_guids for b_guid in required_guids)

            if is_complete:
                chain_text = self._get_text(chain)
                if chain_text and chain_text != "N/A" and chain_text not in unique_chain_texts:
                    unique_chain_texts.append(chain_text)

        return unique_chain_texts

    def _build_affected_chains_and_description(
        self, effect: Effect, initial_description: str
    ) -> tuple[Dict[str, AffectedChainInfo], str]:
        """
        Private helper method to resolve the affected production chains layout dictionary
        and build the localized description text listing for a given effect.
        """
        affected_chains_dict: Dict[str, AffectedChainInfo] = {}
        final_description = initial_description

        # Patron property is correctly typed as ChainMapping
        chains_mapping: ChainMapping = effect.production_chains_by_target

        effect_targets = effect.targets if (effect and hasattr(effect, "targets")) else []
        unique_chain_texts = self._get_unique_chain_texts_for_effect(effect_targets, chains_mapping)

        for chain, targets_dict in chains_mapping.items():
            chain_guid_str = str(chain.guid)

            # Gather matched building assets active for this effect's targets
            active_production_assets: List[ProductionAssetInfo] = [
                {"guid": tgt_asset.guid, "name": tgt_asset.name, "text": self._get_text(tgt_asset)}
                for tgt_asset in targets_dict.values()
                if self._is_in_effect_targets(tgt_asset, effect_targets)
            ]

            if active_production_assets:
                active_guids = {asset["guid"] for asset in active_production_assets}

                # Check if it satisfies the structural completeness verification parameters
                is_complete = False
                if isinstance(chain, AssetPoolBase):
                    is_complete = True
                else:
                    required_guids = self._get_chain_building_guids(chain)
                    is_complete = required_guids and all(b_guid in active_guids for b_guid in required_guids)

                if is_complete:
                    chain_info: AffectedChainInfo = {
                        "name": chain.name,
                        "text": self._get_text(chain),
                        "production_assets": active_production_assets,
                    }
                    affected_chains_dict[chain_guid_str] = chain_info

        # Append comma-separated chain strings if present
        if unique_chain_texts:
            chains_string = ", ".join(unique_chain_texts)
            final_description = f"{final_description} {chains_string}"

        return affected_chains_dict, final_description

    # --- Printing Methods ---

    def print_patrons(self, guid: int | None = None):
        """
        Prints details for stored patrons.

        Args:
            guid: If provided, only prints that specific patron.
                  If None, prints all stored patrons.
        """
        if not self.patrons:
            print("No patrons loaded in memory. Call extract_all() first.")
            return

        if guid is not None:
            if patron := self.patrons.get(guid):
                self._print_single_patron(patron)
            else:
                print(f"Patron with GUID {guid} not found in current results.")
        else:
            for patron in self.patrons.values():
                self._print_single_patron(patron)

    def _print_single_patron(self, patron: Patron):
        """Internal helper to print the full details of one patron."""
        print(f"\n{'=' * self.print_width}")
        print(f"PATRON: {patron.name} (GUID: {patron.guid}) ".center(self.print_width))
        print(f"{'=' * self.print_width}")

        # === Shrine Effect ===
        shrine_eff = patron.shrine_effect
        shrine_item = shrine_eff.shrines[0]  # Usually the roman one.
        print(f"Shrine: {shrine_eff.name} (GUID: {shrine_eff.guid})")
        print(f"Name: {shrine_item.text}")

        print(f"{'-' * self.print_width}")

        # === Veneration Effect ===
        veneration_eff = patron.veneration_effect
        print(f"Veneration Effect: {veneration_eff.title} (GUID: {veneration_eff.asset.guid})")
        print(f"{veneration_eff.description}")

        print(f"{'-' * self.print_width}")

        # === Exaltation Effect ===
        exaltation_eff = patron.exaltation_effects[0]  # Usually one item.

        print(f"Exaltation Effect: {exaltation_eff.title} (GUID: {exaltation_eff.asset.guid})")
        print(f"{exaltation_eff.description}")

        print(f"{'=' * self.print_width}")

        print("Portraits ")
        print(f"- Big: {patron.portraits.big.name}")
        print(f"- Small: {patron.portraits.small.name}")

        print(f"{'=' * self.print_width}")

        for eff_index, effect_data in enumerate(patron.local_effects):
            final_description = effect_data.description

            # Resolve unique chain strings using the helper method ONLY for the first effect
            if eff_index == 0:
                effect_targets = (
                    effect_data.asset.targets if (effect_data.asset and hasattr(effect_data.asset, "targets")) else []
                )
                unique_chain_texts = self._get_unique_chain_texts_for_effect(
                    effect_targets, effect_data.asset.production_chains_by_target
                )

                # Append the comma-separated strings to the printed description if unique chains exist
                if unique_chain_texts:
                    chains_string = ", ".join(unique_chain_texts)
                    final_description = f"{final_description} {chains_string}"

            print(f"Title:       {effect_data.title}")
            print(f"Description: {final_description}")

            if effect_data.asset:
                print(f"Asset GUID:  {effect_data.asset.guid}")
                self._print_buffs(effect_data.asset.buffs)

                # Only pass the chains mapping for the first effect to keep target prints clean
                current_chains_mapping = effect_data.asset.production_chains_by_target if eff_index == 0 else {}
                self._print_targets(effect_data.asset.targets, current_chains_mapping)

            print(f"{'-' * self.print_width}")

            if effect_data.milestones:
                print("Milestones:  ")
                for mil_index, mil in enumerate(effect_data.milestones):
                    print(f"  * Milestone {mil_index} - Devotion {mil.devotion} - Buff Scaling {mil.buff_scaling}")
            else:
                print("Milestones:  None")

            if eff_index < len(patron.local_effects) - 1:
                print(f"{'-' * self.print_width}")

    def _print_buffs(self, buffs: List[Asset]):
        """Private method to process and print buff assets."""
        print(f"{'-' * self.print_width}")
        print(f"Buffs: {len(buffs)}")

        for buff_index, buff_asset in enumerate(buffs, 1):
            print(f"  |- {buff_index} Buff - {buff_asset.name} (GUID: {buff_asset.guid})")

    def _print_targets(self, targets: Sequence[Asset], chains_mapping: ChainMapping, level: int = 0) -> None:
        """Private method to process and print target assets and asset pools recursively.

        Args:
            targets: The sequence of target assets to loop over.
            chains_mapping: The patron's production_chains_by_target property dictionary.
            level: Recursion depth formatting level.
        """
        # Print the header only at the root level
        if level == 0:
            print(f"{'-' * self.print_width}")
            print(f"Targets: {len(targets)}")

        # Calculate indentation based on recursion depth
        indent = "  " * level

        for target_index, target_asset in enumerate(targets, 1):
            if target_index > 1:
                print(f"{'-' * self.DEFAULT_PRINT_WIDTH}")

            # Print the current target with proper indentation
            print(f"{indent}  |- {target_index} Target: {target_asset.name} (GUID: {target_asset.guid})")

            # 1. Handle Recursion First
            if isinstance(target_asset, AssetPoolBase):
                self._print_targets(target_asset.asset_pool_list, chains_mapping, level + 1)
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

    # --- Export Methods ---

    def to_json_dict(self, web_base_path: str | None = None, flatten: bool = True) -> Dict[str, PatronItemJSON]:
        """
        Processes the patron map into a flat JSON-ready dictionary keyed by
        patron GUID.

        Args:
            web_base_path: Folder prefix (e.g. 'assets/icons/patrons').
            flatten: If True, uses canon_name. If False, uses the full
                mirrored relative path.
        """
        # Switch the shared cache to THIS extractor's language before processing
        self._prepare_converter()

        export_data: Dict[str, PatronItemJSON] = {}

        # self.patrons is already sorted from extract_all()
        for guid, patron in self.patrons.items():
            # 1. Basic Metadata & Icons

            # 1.A Get the icon package for metadata
            patron_icon = IconProcessor.get_icon_package(patron)

            # 1.B Extract localized text
            patron_title = cast("Text | None", patron.find_value("Patron.PatronName"))
            patron_description = cast("Text | None", patron.find_value("Patron.PatronDescription"))

            title = patron_title() if patron_title else "No Title"
            description = patron_description() if patron_description else "No Description"

            # 1.C. Dynamic URL Logic matching the export structure.
            def _get_final_url(raw_path: str | None, canon_name: str | None) -> str:
                if not raw_path:
                    return ""

                # Determine the filename/path part (matches save_image logic).
                if flatten:
                    file_part = f"{canon_name or patron.canonical_name}.webp"
                else:
                    # Use the mirrored path which preserves icon_content/features/etc
                    file_part = f"{IconProcessor.get_mirrored_path(raw_path)}.webp"

                final_url = f"{web_base_path}/{file_part}" if web_base_path else file_part
                return final_url.replace("\\", "/")

            # 2. Local Effects & Associated Production Chains Map
            local_effects_json: List[LocalEffectJSON] = []

            for eff_idx, e in enumerate(patron.local_effects):
                affected_chains_dict: Dict[str, AffectedChainInfo] = {}
                final_description = e.description

                # Only resolve production chain dependencies for the first local effect
                if eff_idx == 0 and e.asset:
                    # Leverage the cleanly isolated private helper method
                    affected_chains_dict, final_description = self._build_affected_chains_and_description(
                        effect=e.asset, initial_description=e.description
                    )

                local_effects_json.append(
                    {
                        "title": e.title,
                        "description": final_description,
                        "milestones": [{"devotion": m.devotion, "buff_scaling": m.buff_scaling} for m in e.milestones],
                        "affected_chains": affected_chains_dict,
                    }
                )

            # 3. Veneration Effect
            veneration = patron.veneration_effect
            veneration_json: VenerationEffectJSON = {"title": veneration.title, "description": veneration.description}

            # 4. Shrine Effect
            shrine = patron.shrine_effect
            shrine_json: ShrineEffectJSON = {
                "title": shrine.name,
                "guid": shrine.guid,
                "shrines": [{"guid": s.guid, "title": self._get_text(s)} for s in shrine.shrines],
            }

            # 5. Exaltation Effects
            exaltation_json: List[ExaltationEffectJSON] = [
                {"title": e.title, "description": e.description} for e in patron.exaltation_effects
            ]

            # 6. Portraits
            portraits_json: PortraitJSON = {
                "big": _get_final_url(patron.portraits.big.path, patron.portraits.big.name),
                "small": _get_final_url(patron.portraits.small.path, patron.portraits.small.name),
            }

            export_data[str(guid)] = {
                "uid": patron.guid,
                "canon_name": patron.canonical_name,
                "title": title,
                "description": description,
                "icon_url": _get_final_url(patron_icon["path"], patron_icon["canon_name"]),
                "canon_icon_name": patron_icon["canon_name"] or "",
                "local_effects": local_effects_json,
                "veneration_effect": veneration_json,
                "shrine_effect": shrine_json,
                "exaltation_effects": exaltation_json,
                "portraits": portraits_json,
            }
        return export_data

    def save_to_json(self, file_path: Path | str, web_base_path: str | None = None, flatten: bool = True):
        """
        Helper to write the exported dictionary to a physical file.

        Args:
            file_path: Where to save the actual .json file.
            web_base_path: The URL prefix to use for images inside the JSON.
            flatten: If True, uses canon_name. If False, uses the full
                mirrored relative path.
        """
        data = self.to_json_dict(web_base_path=web_base_path, flatten=flatten)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Successfully exported {len(data)} patrons to {file_path}")

    def export_all_patron_assets(self, output_base: Path | str, quality: int = 75, flatten: bool = False):
        """
        Exports all patron-related assets.
        - Patron/Shrine/Effect Icons: 128x128.
        - Big Portraits: 2496px -> 512x512.
        - Small Portraits: 704px -> 128x128.
        """
        output_path = Path(output_base)
        standard_assets: List[Asset] = []

        for patron in self.patrons.values():
            # 1. Main Patron Icon
            standard_assets.append(patron)

            # 2. Sub-Assets (Veneration, Shrines, Exaltation)
            standard_assets.append(patron.veneration_effect.asset)
            standard_assets.extend(patron.shrine_effect.shrines)
            for exalt in patron.exaltation_effects:
                standard_assets.append(exalt.asset)

        # Batch export all standard icons at 128x128
        print(f"Exporting {len(standard_assets)} standard icons (128x128)...")
        IconProcessor.export_icons(
            assets=standard_assets,
            output_base=output_path,
            flatten=flatten,
            quality=quality,
            resize=(128, 128),
            use_canonical_name=True,
        )

        # 3. Specialized Portrait Export (Directly via save_image)
        print("Exporting and resizing specialized portraits...")
        for patron in self.patrons.values():
            p = patron.portraits

            # Big Portrait (512x512)
            if p.big.path and p.big.image:
                IconProcessor.save_image(
                    image=p.big.image,
                    original_path=p.big.path,
                    output_base=output_path,
                    quality=quality,
                    resize=(512, 512),
                    flatten=flatten,
                )

            # Small Portrait (128x128)
            if p.small.path and p.small.image:
                IconProcessor.save_image(
                    image=p.small.image,
                    original_path=p.small.path,
                    output_base=output_path,
                    quality=quality,
                    resize=(128, 128),
                    flatten=flatten,
                )
