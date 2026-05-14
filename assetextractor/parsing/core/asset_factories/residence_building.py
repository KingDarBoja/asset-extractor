from __future__ import annotations

from typing import TYPE_CHECKING, Any

from assetextractor.parsing.core.asset_factories.common.cost import AssetWithCosts

# Import AssetCache ONLY for type checking
if TYPE_CHECKING:
    import lxml.etree as et

    from assetextractor.parsing.core.assets import AssetCache
    from assetextractor.parsing.core.common import NamedElement
    from assetextractor.parsing.core.texts import Text


class ResidenceBuilding(AssetWithCosts):
    """Specialized Asset for 'ResidenceBuilding' with pre-computed data."""

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
