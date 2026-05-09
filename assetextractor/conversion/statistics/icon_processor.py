from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset
    from assetextractor.parsing.core.attributes import FileNameAttribute, WandImageProto


class IconData(TypedDict):
    name: str | None
    image: WandImageProto | None
    path: str | None
    image_url: str | None


class IconProcessor:
    """Handles icon metadata extraction and path sanitization for web display."""

    @staticmethod
    def clean_path(raw_path: str | None) -> str | None:
        """Removes the .cache prefix and file extension for web-ready URLs."""
        if not raw_path:
            return None

        _, sep, after = raw_path.partition(".cache")
        return str(Path(after).with_suffix("")) if sep else raw_path

    @classmethod
    def get_icon_package(cls, asset: Asset, include_image: bool = False) -> IconData:
        """Extracts and processes all icon-related metadata from an asset."""
        path_str = None
        name = None

        # Use find to get the raw filename attribute
        icon_node: FileNameAttribute = asset.find("Standard.IconFilename")  # type: ignore
        if icon_node and icon_node.value:
            path_str = str(icon_node.value)
            name = icon_node.value.stem

        img_obj = None
        # Only attempt to get the image if requested AND the file actually exists
        if include_image and asset.icon and path_str and Path(path_str).exists():
            # Check existence HERE to prevent the library from logging an error
            img_obj = asset.icon.get_image()
        # If it doesn't exist, img_obj remains None and no error is logged
        else:
            pass

        return {"name": name, "image": img_obj, "path": path_str, "image_url": cls.clean_path(path_str)}
