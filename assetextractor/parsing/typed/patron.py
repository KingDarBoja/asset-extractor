from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, cast

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.core.attributes import FileNameAttribute, WandImageProto
from assetextractor.parsing.typed.asset_pool_base import AssetPoolBase

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
    def production_chains_by_target(self) -> Dict[Asset, Dict[int, Asset]]:
        """
        Processes targets and groups them by their parent Production Chain.
        For Mines (GUID: 50225) and Quarries (GUID: 50608), it bypasses ProductionChain
        lookup entirely and groups leaf assets directly under the pool container asset.

        Returns:
            Dict[Asset, Dict[int, Asset]]:
                - Top level key: The unique ProductionChain or specific AssetPool asset object
                - Inner level key: The target asset's integer GUID
                - Inner value: The target asset object itself
        """
        mapping: Dict[Asset, Dict[int, Asset]] = {}

        def _process_asset_production_chain(target_asset: Asset, current_pool_key: Asset | None = None):
            pool_key = current_pool_key

            # Intercept the specific Mine and Quarry pools to use them as top-level structural keys
            if getattr(target_asset, "guid", None) in (50225, 50608):
                pool_key = target_asset
                if pool_key not in mapping:
                    mapping[pool_key] = {}

            if pool_key is not None:
                # Group deep leaf production assets directly under the respective pool container key
                if not isinstance(target_asset, AssetPoolBase):
                    mapping[pool_key][target_asset.guid] = target_asset
            else:
                # Standard behavior: Trace references to find parent ProductionChain templates
                referenced_by = getattr(target_asset, "referenced_by", None)
                if referenced_by:
                    for ref in referenced_by.values():
                        source = getattr(ref, "source", None)
                        if source:
                            template = getattr(source, "template", None)
                            if template and getattr(template, "name", None) == "ProductionChain":
                                chain_asset = source

                                # Initialize the chain entry if seen for the first time
                                if chain_asset not in mapping:
                                    mapping[chain_asset] = {}

                                # Add the specific target asset under this chain group
                                mapping[chain_asset][target_asset.guid] = target_asset

            # Descend recursively through structural nested asset pools
            if isinstance(target_asset, AssetPoolBase):
                for sub_asset in target_asset.asset_pool_list:
                    _process_asset_production_chain(sub_asset, pool_key)

        # Crawl local and exaltation targets for this specific patron
        for effect in self.local_effects:
            if effect.asset and hasattr(effect.asset, "targets"):
                for target in effect.asset.targets:
                    _process_asset_production_chain(target)
        for exalt in self.exaltation_effects:
            if exalt.asset and hasattr(exalt.asset, "targets"):
                for target in exalt.asset.targets:
                    _process_asset_production_chain(target)

        return mapping


# The GUIDs of Mines and Quarries Assets with the asset pool list are:

# - AssetPoolNamed -> Vulcanus Goods - GUID: 144801

# Contains both Mines and Quarries:
# - AssetPoolNamed -> Asset Pool Production All Mines - GUID: 50225
# - AssetPoolNamed -> Asset Pool Production All Quarries - GUID: 50608

# So I want only the assets from those two (Quarries and Mines) instead of the ProductionChain being referenced
