from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, List

from attr import dataclass  # Postpones evaluation of annotations

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.core.attributes import ListAttribute, PrimitiveAttribute

# Import AssetCache ONLY for type checking
if TYPE_CHECKING:
    import lxml.etree as et

    from assetextractor.parsing.core.assets import AssetCache
    from assetextractor.parsing.core.common import NamedElement
    from assetextractor.parsing.core.texts import Text


@dataclass(frozen=True)
class Cost:
    ingredient: str
    """The ingredient (material) as localized text. Usually 'Denarii' + others
    like 'Timber', 'Marble', etc."""
    amount: int
    """Required quantity of this ingredient."""


class ProductionField(Asset):
    """Specialized Asset for Patron (Deities) with pre-computed data."""

    def __init__(self, node: et._Element, cache: AssetCache):
        super().__init__(node, cache)

    def _get_text_from_node(self, elm: NamedElement[Any], path: str, fallback: str) -> str:
        """Helper to resolve a Text node path into a localized string."""
        node = elm.find(path)

        if node is not None:
            lang = self.cache.texts.converter.language
            text_attr: Text | None = node()
            if text_attr is not None:
                # Return the localized string, fallback to English, then to the provided default
                return text_attr.get(lang) or text_attr.get("english") or fallback  # type: ignore

        return fallback

    @cached_property
    def costs(self) -> List[tuple[Asset, int]]:
        """
        Return a list of tuples with the first item being an asset of class
        'Product' and the second an integer value.
        """
        raw_cost_list = self.find("Cost.Costs")
        out_cost_list: List[tuple[Asset, int]] = []

        if isinstance(raw_cost_list, ListAttribute):
            for asset_entry in raw_cost_list:
                # Get the referenced asset
                linked_asset = asset_entry.find("Ingredient")
                amount_node = asset_entry.find("Amount")
                amount_val = (
                    amount_node.value
                    if isinstance(amount_node, PrimitiveAttribute) and isinstance(amount_node.value, int)
                    else 0
                )

                if linked_asset is not None and isinstance(linked_asset, Asset):
                    tpl_name = linked_asset.template.name

                    # TODO: Add all the Asset sub-classes per template name to
                    # have specialized instantiation of linked assets.
                    match tpl_name:
                        case _:
                            # Default generic asset.
                            out_cost_list.append((linked_asset, amount_val))

        return out_cost_list

    @cached_property
    def formatted_costs(self) -> List[Cost]:
        """Return the formatted costs with their localized ingredient names and amounts."""
        out_costs: List[Cost] = []

        for cost_asset, amount in self.costs:
            localized_name = cost_asset.text() if cost_asset.text is not None else cost_asset.name
            out_costs.append(Cost(ingredient=localized_name, amount=amount))

        return out_costs
