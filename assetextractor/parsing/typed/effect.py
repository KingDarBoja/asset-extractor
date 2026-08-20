from __future__ import annotations

from assetextractor.parsing.typed.common.effect_base import AssetWithEffect


class Effect(AssetWithEffect, template_names="Effect"):
    """Specialized Asset for Effect with pre-computed data."""

    pass
