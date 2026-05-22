from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Sequence, TypedDict, cast

from assetextractor.conversion.statistics.icon_processor import IconProcessor
from assetextractor.parsing.core.texts import StandardTextConverter
from assetextractor.parsing.typed.common.asset_pool_base import AssetPoolBase
from assetextractor.parsing.typed.item import Item, ItemWithBoost

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset, AssetCache
    from assetextractor.parsing.typed.common.upgrades.common import UpgradeAttributeJSON
    from assetextractor.parsing.typed.common.upgrades.factory_upgrade import AddedFertilityJSON
    from assetextractor.parsing.typed.common.upgrades.maintenance_upgrade import ReplacementWorkforceJSON

# Safely import IPython's display for Jupyter Notebook integration
try:
    from IPython.display import HTML, display  # type: ignore
except ImportError:
    display, HTML = None, None  # type: ignore


# --- Strictly Typed JSON Schemas ---


class ModifierResult(TypedDict):
    attributes: List[UpgradeAttributeJSON]
    added_fertility: AddedFertilityJSON | None
    workforce_replacement: ReplacementWorkforceJSON | None


class BuffModifierJSON(TypedDict):
    guid: int
    name: str
    label: str
    template: str  # e.g., "FactoryBuff", "ResidenceBuff", "ShipBuff"
    attributes: List[UpgradeAttributeJSON]
    workforce_replacement: ReplacementWorkforceJSON | None
    added_fertility: AddedFertilityJSON | None


class AffectedItemJSON(TypedDict):
    guid: int
    title: str


class TargetAssetJSON(TypedDict):
    guid: int
    name: str
    title: str
    affected_items: List[AffectedItemJSON]


class SpecialistEffectJSON(TypedDict):
    scope: str  # e.g., "AREA", "GLOBAL"
    category: str  # e.g., "ECONOMIC", "MILITARY"
    targets: List[TargetAssetJSON]
    buffs: List[BuffModifierJSON]


class SpecialistItemJSON(TypedDict):
    guid: int
    name: str
    title: str
    description: str
    icon_url: str
    rarity: str  # e.g., "COMMON", "EPIC", "LEGENDARY"
    niche: str  # e.g., "ROMAN", "CELTIC"
    allocation: str  # e.g., "GUILD_HOUSE", "TOWN_HALL", "HARBOR_MASTER"
    trade_price: int
    origin: str
    has_boost: bool
    effect: SpecialistEffectJSON | None


@dataclass
class SpecialistCollection:
    """Container for categorized and sorted game assets."""

    items: Dict[int, Item] = field(default_factory=lambda: cast("Dict[int, Item]", {}))
    items_with_boost: Dict[int, ItemWithBoost] = field(default_factory=lambda: cast("Dict[int, ItemWithBoost]", {}))


class SpecialistExtractor:
    """Main orchestrator for extracting items from Anno 117 assets."""

    # Dynamic format variable controlling visual separation lines globally
    DEFAULT_PRINT_WIDTH = 100

    def __init__(self, assets: AssetCache, language: str = "english"):
        """Initialize the specialists extractor.

        Args:
            assets: Asset cache with loaded assets
            language: Language for text localization (default: "english")
        """
        self.assets = assets
        self.language = language
        self.texts = assets.texts
        self.specialists = SpecialistCollection()
        self.print_width = self.DEFAULT_PRINT_WIDTH

    def _prepare_converter(self):
        """Ensures the shared cache is using this extractor's language."""
        self.assets.texts.converter = StandardTextConverter(self.language)

    def extract_all(self) -> SpecialistCollection:
        """
        Extracts all 'Item' and 'ItemWithBoost' assets, separates them,
        and saves them sorted by GUID into self.specialists.

        Returns:
            SpecialistCollection: The populated dataclass instance.
        """
        self._prepare_converter()

        tpl_item = self.assets.templates.get("Item")
        tpl_item_boost = self.assets.templates.get("ItemWithBoost")

        # If neither template exists, reset and return empty structure
        if not tpl_item and not tpl_item_boost:
            self.specialists = SpecialistCollection()
            return self.specialists

        # Gather assets from available templates safely
        all_assets: List[Asset] = []
        if tpl_item:
            all_assets.extend(tpl_item.assets)
        if tpl_item_boost:
            all_assets.extend(tpl_item_boost.assets)

        # Separate and map raw assets by type
        raw_items: Dict[int, Item] = {}
        raw_boosts: Dict[int, ItemWithBoost] = {}

        for a in all_assets:
            match a.template.name:
                case "ItemWithBoost":
                    raw_boosts[a.guid] = cast("ItemWithBoost", a)
                case "Item":
                    # Filter out test items.
                    if a.guid in [95752, 95753, 95764]:
                        continue
                    raw_items[a.guid] = cast("Item", a)
                case _:
                    pass

        # Sort by GUID and lock the order into the respective dictionaries
        sorted_items = {guid: raw_items[guid] for guid in sorted(raw_items.keys())}
        sorted_boosts = {guid: raw_boosts[guid] for guid in sorted(raw_boosts.keys())}

        # Instantiate and save to self.specialists
        self.specialists = SpecialistCollection(items=sorted_items, items_with_boost=sorted_boosts)

        return self.specialists

    # --- Serialization Methods ---

    def _serialize_single_buff_modifiers(self, buff_asset: Asset) -> BuffModifierJSON:
        """Inspects a buff asset and aggregates all active component modifiers dynamically."""
        attributes: List[UpgradeAttributeJSON] = []
        workforce_repl: ReplacementWorkforceJSON | None = None
        added_fertility_data: AddedFertilityJSON | None = None

        # List all the serialize modifiers methods.
        modifier_methods = [
            "serialize_building_modifiers",
            "serialize_factory_modifiers",
            "serialize_health_modifiers",
            "serialize_maintenance_modifiers",
            "serialize_movement_modifiers",
            "serialize_residence_modifiers",
            "serialize_trade_ship_modifiers",
            "serialize_unit_modifiers",
            "serialize_vehicle_modifiers",
            "serialize_area_buff_modifiers",
        ]

        for method_name in modifier_methods:
            if hasattr(buff_asset, method_name):
                # 1. Get the method
                method = getattr(buff_asset, method_name)

                # 2. Call it and cast to our TypedDict so the type checker
                #    knows the return structure
                res = cast("ModifierResult", method())

                # 3. Extend attributes safely
                if "attributes" in res:
                    attributes.extend(res["attributes"])

                # 4. Handle specific component side-effects
                if "added_fertility" in res:
                    added_fertility_data = res["added_fertility"]
                if "workforce_replacement" in res:
                    workforce_repl = res["workforce_replacement"]

        buff_label = buff_asset.text() if buff_asset.text else buff_asset.name
        return {
            "guid": buff_asset.guid,
            "name": buff_asset.name,
            "label": buff_label,
            "template": buff_asset.template.name,
            "attributes": attributes,
            "workforce_replacement": workforce_repl,
            "added_fertility": added_fertility_data,
        }

    def _serialize_targets(self, targets_sequence: Sequence[Asset]) -> List[TargetAssetJSON]:
        return [self._build_target_node(target) for target in targets_sequence]

    def _build_target_node(self, target_asset: Asset) -> TargetAssetJSON:
        affected_items: List[AffectedItemJSON] = []

        if isinstance(target_asset, AssetPoolBase):
            for sub_asset in target_asset.asset_pool_list:
                affected_items.append(
                    {"guid": sub_asset.guid, "title": sub_asset.text() if sub_asset.text else sub_asset.name}
                )

        return {
            "guid": target_asset.guid,
            "name": target_asset.name,
            "title": target_asset.text() if target_asset.text else target_asset.name,
            "affected_items": affected_items,
        }

    # --- Printing Methods ---

    def print_specialists(self, guid: int | None = None):
        """
        Prints details for stored specialists.

        Args:
            guid: If provided, only prints that specific specialist.
                  If None, prints all stored specialists.
        """
        if not self.specialists.items and not self.specialists.items_with_boost:
            print("No specialists loaded in memory. Call extract_all() first.")
            return

        # Combine both dictionaries and print them sorted by key
        all_specialists = {**self.specialists.items, **self.specialists.items_with_boost}
        if guid is not None:
            if specialist := all_specialists.get(guid):
                self._print_single_specialist(specialist)
            else:
                print(f"Specialist with GUID {guid} not found in current results.")
        else:
            for guid in sorted(all_specialists.keys()):
                self._print_single_specialist(all_specialists[guid])

    def _print_single_specialist(self, item: Item):
        """Internal helper to format and print the properties of a single specialist."""
        is_boost = isinstance(item, ItemWithBoost)
        type_label = "SPECIALIST (WITH BOOST)" if is_boost else "SPECIALIST"

        print(f"\n{'=' * self.print_width}")
        print(f"{type_label}: {item.item_standard_info.title} (GUID: {item.guid}) ".center(self.print_width))
        print(f"{'=' * self.print_width}")

        std_name = item.item_standard_info.std_name
        description = item.item_standard_info.description

        rendered_side_by_side = False
        if display is not None and HTML is not None:
            icon_data = IconProcessor.get_icon_package(item, include_image=True)
            img = icon_data.get("image")
            if img is not None:
                import base64

                b64_data = None
                mime_type = "image/png"

                # Extract raw bytes from the object's rich-display representation hooks
                for attr, mime in [
                    ("_repr_png_", "image/png"),
                    ("_repr_webp_", "image/webp"),
                    ("_repr_jpeg_", "image/jpeg"),
                ]:
                    if hasattr(img, attr):
                        try:
                            raw_bytes = getattr(img, attr)()
                            if raw_bytes:
                                b64_data = base64.b64encode(raw_bytes).decode("utf-8")
                                mime_type = mime
                                break
                        except Exception:
                            pass

                if b64_data:
                    # Dynamic theme-aware side-by-side flexbox layout
                    html_content = f"""
                    <div style="display: flex; align-items: flex-start; gap: 16px; margin: 12px 0; font-family: var(--jp-ui-font-family, sans-serif); color: var(--jp-ui-font-color1, #111);">
                        <div style="flex-shrink: 0; width: 64px; height: 64px; border: 1px solid var(--jp-border-color2, #ccc); border-radius: 4px; overflow: hidden; background: #2a2a2a; display: flex; align-items: center; justify-content: center;">
                            <img src="data:{mime_type};base64,{b64_data}" style="width: 64px; height: 64px; object-fit: contain;" />
                        </div>
                        <div style="display: flex; flex-direction: column; justify-content: center; min-height: 64px; line-height: 1.5;">
                            <div><strong style="color: var(--jp-ui-font-color2, #444);">Standard Name:</strong> {std_name}</div>
                            <div style="margin-top: 2px;"><strong style="color: var(--jp-ui-font-color2, #444);">Description:</strong> <span style="font-style: italic; color: var(--jp-ui-font-color3, #666);">{description}</span></div>
                        </div>
                    </div>
                    """
                    display(HTML(html_content))
                    rendered_side_by_side = True

        # Fallback to normal stacked text/image print if running outside a notebook
        if not rendered_side_by_side:
            if display is not None:
                icon_data = IconProcessor.get_icon_package(item, include_image=True)
                if img := icon_data.get("image"):
                    display(img, metadata={"image/png": {"width": 64, "height": 64}})
            print(f"Standard Name: {std_name}")
            print(f"Description:   {description}")

        print(f"{'-' * self.print_width}")

        info = item.item_info
        print(f"Allocation:    {info.allocation.value if hasattr(info.allocation, 'value') else info.allocation}")
        print(f"Rarity:        {info.rarity.value if hasattr(info.rarity, 'value') else info.rarity}")
        print(f"Niche:         {info.niche.value if hasattr(info.niche, 'value') else info.niche}")
        print(f"Trade Price:   {info.trade_price}")
        print(f"Origin:        {info.origin.value if hasattr(info.origin, 'value') else info.origin}")

        # Specialists don't use the localized chain matching structure of Patrons,
        # so we pass an empty dict safely to comply with AssetWithEffect's print signature.

        # We pass a starting branch to frame the buffs
        item.print_buffs(item.buffs, prefix="     ")

        # If we have a production chain mapping context (e.g., for Patrons/Effects), pass it here;
        # otherwise, pass an empty dictionary `{}` for specialists
        item.print_targets(item.targets, {}, prefix="     ")

        print(f"{'=' * self.print_width}")

    # --- Export Methods ---

    def to_json_dict(self, web_base_path: str | None = None, flatten: bool = True) -> Dict[str, SpecialistItemJSON]:
        output_dict: Dict[str, SpecialistItemJSON] = {}

        all_specs: List[tuple[Item | ItemWithBoost, bool]] = []
        for item in self.specialists.items.values():
            all_specs.append((item, False))
        for item_boost in self.specialists.items_with_boost.values():
            all_specs.append((item_boost, True))

        all_specs.sort(key=lambda x: x[0].guid)

        for item, has_boost in all_specs:
            std = item.item_standard_info
            info = item.item_info
            eff_info = item.effect_info
            item_icon = IconProcessor.get_icon_package(item)

            serialized_targets = self._serialize_targets(item.targets)

            serialized_buffs: List[BuffModifierJSON] = [
                self._serialize_single_buff_modifiers(buff) for buff in item.buffs
            ]

            effect_data: SpecialistEffectJSON = {
                "scope": eff_info.effect_scope,
                "category": eff_info.source_category,
                "targets": serialized_targets,
                "buffs": serialized_buffs,
            }

            output_dict[str(item.guid)] = {
                "guid": item.guid,
                "name": std.std_name,
                "title": std.title,
                "description": std.description,
                "icon_url": IconProcessor.get_final_url(
                    raw_path=item_icon["path"],
                    canon_name=item_icon["canon_name"],
                    web_base_path=web_base_path,
                    flatten=flatten,
                    default_name=item.canonical_name,
                ),
                "rarity": info.rarity,
                "niche": info.niche,
                "allocation": info.allocation,
                "trade_price": info.trade_price,
                "origin": info.origin,
                "has_boost": has_boost,
                "effect": effect_data,
            }

        return output_dict

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

    def export_all_assets(
        self,
        output_base: Path | str,
        quality: int = 75,
        resize: tuple[int, int] | None = (128, 128),
        flatten: bool = False,
    ) -> None:
        """
        Exports all item-related assets.

        Args:
            output_base: The base physical directory where icons will be exported.
            quality: Compression ratio parameter for WebP (1-100). Default is 75.
            resize: Sizing dimension tuple. Default is (128, 128).
            flatten: True to save directly under output_base, False to preserve hierarchy.
        """
        output_path = Path(output_base)
        standard_assets: List[Asset] = []

        for specialist in self.specialists.items.values():
            standard_assets.append(specialist)
        for specialist in self.specialists.items_with_boost.values():
            standard_assets.append(specialist)

        # Batch export all standard icons at 128x128
        print(f"Exporting {len(standard_assets)} specialist icons...")
        IconProcessor.export_icons(
            assets=standard_assets,
            output_base=output_path,
            flatten=flatten,
            quality=quality,
            resize=resize,
            use_canonical_name=True,
        )
