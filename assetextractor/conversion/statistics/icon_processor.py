from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple, TypedDict

from assetextractor.parsing.core.attributes import FileNameAttribute

if TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset
    from assetextractor.parsing.core.attributes import WandImageProto


class IconData(TypedDict):
    name: str | None
    canon_name: str | None
    image: WandImageProto | None
    path: str | None
    """Original path."""
    image_url: str | None
    """Formatted path for web usage."""


class IconProcessor:
    """Handles icon metadata extraction, path sanitization, and batch exporting."""

    @staticmethod
    def clean_path(raw_path: str | None) -> str | None:
        """
        Sanitizes a raw file path into a web-ready URL string by removing
        internal cache prefixes and file extensions.

        Args:
            - raw_path: The full system path to the asset (e.g., from a FileNameAttribute).

        Returns:
            A cleaned string starting after the '.cache' segment without a suffix,
            or the original path if '.cache' is not found.
        """
        if not raw_path:
            return None

        _, sep, after = raw_path.partition(".cache")
        return str(Path(after).with_suffix("")) if sep else raw_path

    @staticmethod
    def get_mirrored_path(raw_path: str | None) -> str | None:
        """
        Converts an absolute filesystem path into a relative game-data path
        suitable for mirroring directory structures.

        It identifies the root UI directory (typically '4k' or '.cache') and
        preserves all subsequent folders like 'icon_content' or 'features'.

        Examples:
            Input icon `.../.cache/data/ui/4k/base/icon_content/religion/icon.dds` 
            becomes `base/icon_content/religion/icon`

        Args:
            raw_path: The absolute path to the original .dds or .cache file.

        Returns:
            A relative path string starting after the UI root, excluding the
            file extension.
        """
        if not raw_path:
            return None

        parts = Path(raw_path).parts

        # 1. Find the game data root (starting after '4k' or '.cache')
        try:
            start_index = parts.index("4k") + 1
        except ValueError:
            try:
                start_index = parts.index(".cache") + 1
            except ValueError:
                return Path(raw_path).name  # Fallback to filename

        # 2. Extract all parts to preserve full structure (icon_content, features, etc.)
        relevant_parts = parts[start_index:]

        # Join and strip extension
        return str(Path(*relevant_parts).with_suffix(""))

    @classmethod
    def get_icon_package(cls, asset: Asset, include_image: bool = False) -> IconData:
        """
        Extracts comprehensive icon metadata and optionally the raw image object
        from an asset.

        This method retrieves the 'Standard.IconFilename', calculates canonical
        names, and generates sanitized URLs.

        Args:
            asset: The source Asset object to inspect.
            include_image: If True, attempts to load the actual WandImageProto 
                from the asset's icon property.

        Returns:
            An IconData TypedDict containing the name, canon_name, image object,
            original path, and cleaned image_url.
        """
        path_str = None
        name = None

        icon_node = asset.find("Standard.IconFilename")
        if icon_node and isinstance(icon_node, FileNameAttribute) and icon_node.value:
            path_str = str(icon_node.value)
            name = icon_node.value.stem

        img_obj: WandImageProto | None = None
        if include_image and asset.icon and path_str and Path(path_str).exists():
            img_obj = asset.icon.get_image()

        return {
            "name": name,
            "canon_name": asset.icon.canonical_name if asset.icon is not None else name,
            "image": img_obj,
            "path": path_str,
            "image_url": cls.clean_path(path_str),
        }

    @classmethod
    def export_icons(
        cls,
        assets: List[Asset],
        output_base: Path | str,
        quality: int = 80,
        resize: Tuple[int, int] | None = (64, 64),
        use_canonical_name: bool = False,
        flatten: bool = True,
    ) -> Dict[str, int]:
        """
        Batch processes and exports asset icons to WebP format with optional
        compression and resizing.

        This method can either flatten all images into a single directory or
        mimic the original game folder hierarchy.

        Args:
            assets: A list of Asset objects (e.g., Patrons) to process.
            output_base: The base directory where icons will be saved.
            quality: WebP compression quality (1-100). Defaults to 80.
            resize: An optional (width, height) tuple for downscaling.
                Defaults to (64, 64).
            use_canonical_name: If True (and flattening), uses the asset's
                unique canonical name for the filename.
            flatten: If True, saves all icons directly in output_base. If
                False, recreates the internal game folder structure.

        Returns:
            A dictionary containing statistics on 'exported', 'skipped', and
            'errors' counts.
        """
        base_dir = Path(output_base).resolve()
        base_dir.mkdir(parents=True, exist_ok=True)

        seen_paths: set[str] = set()
        stats: Dict[str, int] = {"exported": 0, "skipped": 0, "errors": 0}

        for asset in assets:
            # 1. Get the icon package which already computes the canonical_name
            icon_data = cls.get_icon_package(asset, include_image=True)
            original_path = icon_data["path"]
            img = icon_data["image"]

            if not original_path or original_path in seen_paths or img is None:
                stats["skipped"] += 1
                continue

            seen_paths.add(original_path)

            # Determine target file path based on flatten toggle
            # Use canonical_name if available, otherwise fallback to asset name
            if flatten:
                file_name = icon_data["canon_name"] or asset.name if use_canonical_name else icon_data["name"]
                target_file = (base_dir / f"{file_name}").with_suffix(".webp")
            else:
                # Use the full mirrored path
                rel_path = cls.get_mirrored_path(original_path)
                target_file = (base_dir / f"{rel_path}").with_suffix(".webp")

            target_file.parent.mkdir(parents=True, exist_ok=True)

            # ----------------------------------------------------

            try:
                img.format = "webp"
                img.compression_quality = quality
                if resize:
                    img.resize(resize[0], resize[1])

                # Save to the flattened path
                img.save(filename=str(target_file))  # type: ignore
                stats["exported"] += 1

                # Print relative to 'results' (two levels up from the file)
                # This results in: [OK] PatronMars -> results/icons/patrons/icon_2d_deity_mars_0.webp
                print(f"  [OK] {asset.name} -> {target_file.relative_to(base_dir.parent.parent.parent)}")

            except Exception as e:
                print(f"  [ERROR] Failed to save {asset.name}: {e}")
                stats["errors"] += 1

        print("---")
        print(f"Finished! Exported: {stats['exported']} | Skipped: {stats['skipped']}")
        return stats
