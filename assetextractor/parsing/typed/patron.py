from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, cast

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.core.attributes import FileNameAttribute, WandImageProto
from assetextractor.parsing.typed.asset_pool_base import AssetPoolBase
from assetextractor.parsing.typed.production_chain import ProductionChain, ProductionChainBase
from assetextractor.parsing.typed.factories import BuildingFactoriesGroup

if TYPE_CHECKING:
    from assetextractor.parsing.core.attributes import ListAttribute
    from assetextractor.parsing.core.texts import Text
    from assetextractor.parsing.typed.asset_pool_named import AssetPoolNamed
    from assetextractor.parsing.typed.effect import Effect
    from assetextractor.parsing.typed.mini_institution_building import MiniInstitutionBuilding


@dataclass(frozen=True)
class Milestone:
    devotion: int
    buff_scaling: int


@dataclass(frozen=True)
class LocalEffect:
    asset: Effect
    milestones: List[Milestone]
    title: str
    description: str


@dataclass(frozen=True)
class PatronIcon:
    path: str | None
    name: str | None
    image: WandImageProto | None


@dataclass(frozen=True)
class PatronPortraits:
    """Store the ingame path and name of all the patron portraits."""

    big: PatronIcon
    small: PatronIcon
    background: PatronIcon


@dataclass(frozen=True)
class ExaltationEffect:
    """
    This is the exaltation effect when this patron becomes the top global,
    usually activated when reaching 7K devotion. Only a single patron can have
    it.
    """

    asset: Effect
    title: str
    description: str


@dataclass(frozen=True)
class VenerationEffect:
    """
    This is the veneration effect when this patron reaches 4K global
    devotion. Can be activated by multiple patrons.
    """

    asset: Effect
    """The referenced effect asset, obtained from 'Wonder' path. The icon can be
    extracted from it as it is the same as 'WonderIcon' path."""
    title: str
    """The title of this effect."""
    description: str
    """The 'WonderDescription' text."""


@dataclass(frozen=True)
class ShrineEffect:
    """
    This is the simplest effect when this patron reaches 1K global
    devotion.
    """

    guid: int
    name: str
    """Ingame localized name."""
    shrines: List[MiniInstitutionBuilding]
    """List of shrines assets that belongs to the referenced 'AssetPoolNamed' from 'Shrine' path."""


class Patron(Asset, template_names="Patron"):
    """Specialized Asset for Patron (Deities) with pre-computed data."""

    @cached_property
    def portraits(self) -> PatronPortraits:
        """Maps the 'Portrait' prefixed paths into a dataclass."""

        def _make_icon(key: str) -> PatronIcon:
            val = cast("Path | None", self.find_value(key))
            icon_node = cast("FileNameAttribute | None", self.find(key))

            path_str = str(val) if val is not None else None
            img_obj = (
                icon_node.get_image()
                if isinstance(icon_node, FileNameAttribute)
                and icon_node.is_image
                and path_str
                and Path(path_str).exists()
                else None
            )

            return PatronIcon(path=path_str, name=val.stem if val is not None else None, image=img_obj)

        return PatronPortraits(
            big=_make_icon("Patron.PortraitBig"),
            small=_make_icon("Patron.PortraitSmall"),
            background=_make_icon("Patron.PortraitBackground"),
        )

    @cached_property
    def local_effects(self) -> List[LocalEffect]:
        """
        Maps the local effects into localized title and descriptions along with
        all the milestones and the referenced 'Effect' asset.
        """
        parsed_effects: List[LocalEffect] = []

        # TODO: For the first local effect description, we must build the list
        # of chains or units affected.
        for effect_item in cast("ListAttribute", self.find("Patron.LocalEffects")):
            effect_asset = cast("Effect", effect_item.find_ref("GUID"))

            milestones: List[Milestone] = [
                Milestone(
                    devotion=cast("int", mil.find_value("Devotion") or 0),
                    buff_scaling=cast("int", mil.find_value("BuffScaling") or 0),
                )
                for mil in cast("ListAttribute", effect_item.find("Milestones"))
            ]

            title_text = cast("Text | None", effect_item.find_value("Title"))
            desc_text = cast("Text | None", effect_item.find_value("Description"))

            parsed_effects.append(
                LocalEffect(
                    asset=effect_asset,
                    milestones=milestones,
                    title=title_text() if title_text else "No Title",
                    description=desc_text() if desc_text else "No Description",
                )
            )

        return parsed_effects

    @cached_property
    def exaltation_effects(self) -> List[ExaltationEffect]:
        """
        Maps the 'DominantEffects' list into localized title and description
        along with the referenced 'Effect' asset. This is the ingame exaltation
        effect.
        """
        parsed_effects: List[ExaltationEffect] = []

        for effect_item in cast("ListAttribute", self.find("Patron.DominantEffects")):
            effect_asset = cast("Effect", effect_item.find_ref("GUID"))

            title_text = cast("Text | None", effect_item.find_value("Title"))
            desc_text = cast("Text | None", effect_item.find_value("Description"))
            parsed_effects.append(
                ExaltationEffect(
                    asset=effect_asset,
                    title=title_text() if title_text else "No Title",
                    description=desc_text() if desc_text else "No Description",
                )
            )

        return parsed_effects

    @cached_property
    def veneration_effect(self) -> VenerationEffect:
        """
        Maps the 'Wonder' list into localized title and description along with
        the referenced 'Effect' asset. This is the ingame veneration effect.
        """
        wonder_effect = cast("Effect", self.find_value("Patron.Wonder"))
        wonder_desc_text = cast("Text | None", self.find_value("Patron.WonderDescription"))

        title_text = wonder_effect.text

        return VenerationEffect(
            asset=wonder_effect,
            title=title_text() if title_text else "No Title",
            description=wonder_desc_text() if wonder_desc_text else "No Description",
        )

    @cached_property
    def shrine_effect(self) -> ShrineEffect:
        """
        Maps the 'Shrine' AssedPoolNamed path into a single effect that
        contains the list of shrines 'MiniInstitutionBuilding' assets (usually
        Roman and Celtic region).
        """
        shrines_list: List[MiniInstitutionBuilding] = []

        shrine_asset = cast("AssetPoolNamed", self.find_ref("Patron.Shrine"))
        shrine_buildings = shrine_asset.asset_pool_list

        for building in cast("List[MiniInstitutionBuilding]", shrine_buildings):
            shrines_list.append(building)

        return ShrineEffect(guid=shrine_asset.guid, name=shrine_asset.name, shrines=shrines_list)

    @cached_property
    def production_chains_by_target(
        self,
    ) -> Dict[ProductionChain | AssetPoolBase | BuildingFactoriesGroup, Dict[int, BuildingFactoriesGroup]]:
        """
        Dynamically clusters targets structurally.
        - If a nested AssetPool contains ONLY factory buildings, we resolve standard ProductionChain headers.
        - If an AssetPool contains further structural Sub-Pools, those Sub-Pools act as the top-level keys.
        - Standalone factory buildings map to their explicit external ProductionChains or fallback to themselves.
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

        # Collect target pools from local and exaltation effects
        target_pools: List[AssetPoolBase] = []
        for effect in self.local_effects:
            if effect.asset and hasattr(effect.asset, "targets"):
                for target in effect.asset.targets:
                    target_pools.append(target)
        for exalt in self.exaltation_effects:
            if exalt.asset and hasattr(exalt.asset, "targets"):
                for target in exalt.asset.targets:
                    target_pools.append(target)

        for target_pool in target_pools:
            nested_pools = [sub for sub in target_pool.asset_pool_list if isinstance(sub, AssetPoolBase)]

            if nested_pools:
                # Vulcan Case: the top-level pool contains nested pools.
                # We process each nested pool as an active_pool context.
                for active_pool in nested_pools:
                    pool_buildings = [b for b in active_pool.asset_pool_list if isinstance(b, BuildingFactoriesGroup)]
                    pool_guids = {b.guid for b in pool_buildings if hasattr(b, "guid")}

                    for building in pool_buildings:
                        chains = _find_production_chains(building)
                        has_complete_chain = False

                        for chain in chains:
                            chain_buildings = _get_chain_buildings(chain)
                            chain_guids = {b.guid for b in chain_buildings if hasattr(b, "guid")}
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
                # Neptune Case / Ceres Case / Minerva Case: the top-level pool contains buildings directly.
                active_pool = target_pool
                pool_buildings = [b for b in active_pool.asset_pool_list if isinstance(b, BuildingFactoriesGroup)]
                pool_guids = {b.guid for b in pool_buildings if hasattr(b, "guid")}

                for building in pool_buildings:
                    chains = _find_production_chains(building)
                    has_complete_chain = False

                    for chain in chains:
                        chain_buildings = _get_chain_buildings(chain)
                        chain_guids = {b.guid for b in chain_buildings if hasattr(b, "guid")}
                        all_present = len(chain_guids) > 0 and chain_guids.issubset(pool_guids)

                        if all_present:
                            if chain not in mapping:
                                mapping[chain] = {}
                            mapping[chain][building.guid] = building
                            has_complete_chain = True

                    if not has_complete_chain:
                        if building not in mapping:
                            mapping[building] = {}
                        mapping[building][building.guid] = building

        return mapping
