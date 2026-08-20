from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, TypedDict

from assetextractor.conversion.statistics.icon_processor import IconProcessor
from assetextractor.parsing.core.texts import StandardTextConverter
from assetextractor.parsing.typed.common.enums import Region
from assetextractor.parsing.typed.production_chain import ProductionChain, ProductionChainBase

if TYPE_CHECKING:
    from pathlib import Path

    from assetextractor.parsing.core.assets import Asset, AssetCache


class BuildingNodeJSON(TypedDict):
    guid: int
    std_name: str
    text: str
    icon_url: str
    canon_name: str
    tier: List[BuildingNodeJSON]
    region: List[Region]


class ProductionChainJSON(TypedDict):
    uid: int
    canon_name: str
    name: str
    description: str
    output_building: BuildingNodeJSON


class ProductionChainExtractor:
    """Main orchestrator for extracting production chains from Anno 117 assets."""

    # Dynamic format variable controlling visual separation lines globally
    DEFAULT_PRINT_WIDTH = 100

    def __init__(self, assets: AssetCache, language: str = "english"):
        """Initialize the production chain extractor.

        Args:
            assets: Asset cache with loaded assets
            language: Language for text localization (default: "english")
        """
        self.assets = assets
        self.language = language
        self.texts = assets.texts
        self.print_width = self.DEFAULT_PRINT_WIDTH
        # Stores results after extract_all()
        self.production_chains: Dict[int, ProductionChain] = {}

    def _prepare_converter(self):
        """Ensures the shared cache is using this extractor's language."""
        self.assets.texts.converter = StandardTextConverter(self.language)

    def extract_all(self) -> Dict[int, ProductionChain]:
        """
        Extracts all Production Chain assets and saves them into self.production_chains.

        Returns:
            Dict[int, ProductionChain]: A map of production chain GUID to 'ProductionChain' instance.
        """
        self._prepare_converter()

        template = self.assets.templates.get("ProductionChain")
        if not template:
            self.production_chains = {}
            return {}

        # Extract raw assets
        raw_map = {a.guid: a for a in template.assets if isinstance(a, ProductionChain)}

        # Sort by GUID and re-insert into a new dict to lock the order
        self.production_chains = {guid: raw_map[guid] for guid in sorted(raw_map.keys())}

        return self.production_chains

    def _get_text(self, asset: Asset) -> str:
        """Safely extracts localized text from an asset."""
        return asset.text() if asset.text else "N/A"

    # --- Printing Methods ---

    def print_chain(self, chain_guid: int):
        """
        Prints a production chain in a clean, indented visual representation of its tiers.

        Args:
            chain_guid: The GUID of the production chain to print.
        """
        self._prepare_converter()
        chain_asset = self.production_chains.get(chain_guid)
        if not chain_asset:
            print(f"Production chain with GUID {chain_guid} not found.")
            return

        print("".center(self.print_width, "="))
        print(f"PRODUCTION CHAIN: {chain_asset.name} (GUID: {chain_asset.guid})")
        print(f"Description: {chain_asset.localized_description}")
        print("".center(self.print_width, "="))

        chain_base = chain_asset.production_chain
        self._print_node_recursive(chain_base, level=0)

    def print_all_chains(self):
        """Prints a visual overview of all extracted production chains."""
        if not self.production_chains:
            print("No production chains loaded. Run extract_all() first.")
            return

        for guid in self.production_chains:
            self.print_chain(guid)

    def _print_node_recursive(self, node: ProductionChainBase, level: int):
        """Helper to print a single production chain node and its children recursively."""
        indent = "   " * level
        marker = "└── " if level > 0 else "★ "

        b = node.building
        b_name = b.name if b else "Unknown Building"
        b_guid = b.guid if b else 0
        b_text = self._get_text(b) if b else "N/A"

        print(f"{indent}{marker}[Tier {level}] {b_text} ({b_name} | GUID: {b_guid})")

        for child in node.tier:
            self._print_node_recursive(child, level + 1)

    # --- JSON Generation Methods ---

    def to_json_dict(self, web_base_path: str | None = None, flatten: bool = True) -> Dict[str, ProductionChainJSON]:
        """
        Serializes the production chains into a JSON-compatible dictionary structure.

        Args:
            web_base_path: Folder URL path prefix (e.g. 'assets/icons').
            flatten: If True, uses the asset's canonical name for filenames.
                     If False, retains the nested mirrored folder structures.

        Returns:
            Dict mapping chain GUID string to its production chain data.
        """
        self._prepare_converter()
        export_data: Dict[str, ProductionChainJSON] = {}

        for guid, chain in self.production_chains.items():
            chain_base = chain.production_chain

            export_data[str(guid)] = {
                "uid": chain.guid,
                "canon_name": chain.canonical_name,
                "name": chain.text() if chain.text else chain.name,
                "description": chain.localized_description,
                "output_building": self._node_to_json_dict(chain_base, web_base_path, flatten, level=0),
            }

        return export_data

    def _node_to_json_dict(
        self, node: ProductionChainBase, web_base_path: str | None, flatten: bool, level: int
    ) -> BuildingNodeJSON:
        """Helper to recursively map production building structures to a standard JSON layout."""
        b = node.building

        raw_icon_path = None
        canon_icon_name = None
        if b and b.icon and b.icon.value:
            raw_icon_path = str(b.icon.value)
            canon_icon_name = b.icon.canonical_name

        icon_url = IconProcessor.get_final_url(
            raw_path=raw_icon_path,
            canon_name=canon_icon_name,
            web_base_path=web_base_path,
            flatten=flatten,
            default_name="building_icon",
        )

        # Handle the case of another template like "AqueductDistributor", that
        # does not have "Building" data.
        region_val = (
            b.building_info.associated_regions if hasattr(b, "building_info") else [Region.CELTIC, Region.ROMAN]
        )

        return {
            "guid": b.guid if b else 0,
            "std_name": b.name if b else "Unknown",
            "text": self._get_text(b) if b else "N/A",
            "icon_url": icon_url,
            "canon_name": b.canonical_name if b else "unknown",
            "region": region_val,
            "tier": [self._node_to_json_dict(child, web_base_path, flatten, level + 1) for child in node.tier],
        }

    # --- Alternative JSON structure: Web-App Friendly Adjacency List ---

    def to_web_adjacency_list(self, web_base_path: str | None = None, flatten: bool = True) -> Dict[str, Any]:
        """
        Generates an alternative web-app friendly representation of the production chains.
        This provides a flat dictionary of unique buildings (nodes) and an array of directed edge links.
        This flat format makes it extremely easy to render with React Flow, Vis.js, D3, or similar libraries.

        Returns:
            A dictionary containing:
            - 'nodes': Flat map of building GUID to attributes (name, text, icon).
            - 'edges': List of link objects mapping source building -> target building.
        """
        self._prepare_converter()
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        def traverse_flat(node: ProductionChainBase):
            b = node.building
            if not b:
                return

            b_guid_str = str(b.guid)
            if b_guid_str not in nodes:
                raw_icon_path = str(b.icon.value) if b.icon and b.icon.value else None
                canon_icon_name = b.icon.canonical_name if b.icon else None

                nodes[b_guid_str] = {
                    "guid": b.guid,
                    "name": b.name,
                    "text": self._get_text(b),
                    "canon_name": b.canonical_name,
                    "icon_url": IconProcessor.get_final_url(
                        raw_path=raw_icon_path,
                        canon_name=canon_icon_name,
                        web_base_path=web_base_path,
                        flatten=flatten,
                        default_name="building_icon",
                    ),
                }

            for child in node.tier:
                cb = child.building
                if cb:
                    edges.append(
                        {
                            "source": cb.guid,  # Supplier (e.g., Flax / Murex Snail)
                            "target": b.guid,  # Output (e.g., Cloth / Tyrian Purple)
                        }
                    )
                traverse_flat(child)

        for chain in self.production_chains.values():
            traverse_flat(chain.production_chain)

        return {"nodes": nodes, "edges": edges}

    def save_to_json(self, file_path: Path | str, web_base_path: str | None = None, flatten: bool = True):
        """
        Helper to write the exported production chain dictionary to a physical file.

        Args:
            file_path: Where to save the actual .json file.
            web_base_path: The URL prefix to use for images inside the JSON.
            flatten: If True, uses canon_name for the images. If False, uses the
                mirrored relative path.
        """
        data = self.to_json_dict(web_base_path=web_base_path, flatten=flatten)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Successfully exported {len(data)} production chains to {file_path}")

    # --- Icon Export Methods ---

    def export_all_chain_assets(
        self,
        output_base: Path | str,
        quality: int = 75,
        resize: tuple[int, int] | None = (128, 128),
        flatten: bool = False,
    ) -> Dict[str, int]:
        """
        Gathers all unique building assets across all active production chains
        and batch-exports their high-resolution WebP icons.

        Args:
            output_base: The base physical directory where icons will be exported.
            quality: Compression ratio parameter for WebP (1-100). Default is 75.
            resize: Sizing dimension tuple. Default is (128, 128).
            flatten: True to save directly under output_base, False to preserve hierarchy.

        Returns:
            A dictionary tracking counts for 'exported', 'skipped', and 'errors'.
        """
        self._prepare_converter()
        unique_buildings: Dict[int, Asset] = {}

        def collect_buildings(node: ProductionChainBase):
            if node.building:
                unique_buildings[node.building.guid] = node.building
            for child in node.tier:
                collect_buildings(child)

        # Collect unique building assets across all production chains
        for chain in self.production_chains.values():
            collect_buildings(chain.production_chain)

        building_list = list(unique_buildings.values())
        print(
            f"Exporting {len(building_list)} unique production building icons to {output_base} (Quality: {quality})..."
        )

        # Reuse IconProcessor's core batch exporter
        return IconProcessor.export_icons(
            assets=building_list,
            output_base=output_base,
            quality=quality,
            resize=resize,
            use_canonical_name=True,
            flatten=flatten,
        )

    # --- Graph Drawing Method (Jupyter Notebook Compatible) ---

    def draw_graph(self, chain_guid: int):
        """
        Renders a beautiful horizontal tree diagram of the production chain inside
        Jupyter Notebooks using NetworkX, Matplotlib, and inline icon overlays.

        Styling matches the custom color scheme:
        - Primary Color: #5f032e (Node background)
        - Secondary Color: #1d000e (Node borders & Connection edges)
        - Background Color: #d4b89b (Canvas background)

        To visualize, make sure you have standard graphing dependencies installed:
        >>> pip install networkx matplotlib pillow

        Args:
            chain_guid: The GUID of the production chain to draw.
        """
        try:
            import matplotlib.pyplot as plt
            import networkx as nx
            from matplotlib.offsetbox import AnnotationBbox, OffsetImage, TextArea

        except ImportError:
            print("[Error] drawing graph requires 'networkx' and 'matplotlib' packages.")
            print("Please run: pip install networkx matplotlib pillow")
            return

        self._prepare_converter()
        chain_asset = self.production_chains.get(chain_guid)
        if not chain_asset:
            print(f"Production chain with GUID {chain_guid} not found.")
            return

        # Define custom color palette variables for easy reuse
        primary_color = "#5f032e"
        secondary_color = "#1d000e"
        bg_color = "#d4b89b"

        # Dedicated variable for custom node label font sizes
        label_fontsize = 14

        chain_base = chain_asset.production_chain
        graph: nx.DiGraph[int] = nx.DiGraph()
        labels: Dict[int, str] = {}
        positions: Dict[int, tuple[float, float]] = {}
        guid_to_asset_map: Dict[int, Asset] = {}

        # Use a coordinate layout tracker to cleanly center intermediate/supplier nodes
        levels_map: Dict[int, List[int]] = {}

        def traverse_graph(node: ProductionChainBase, level: int = 0):
            b = node.building
            if not b:
                return

            labels[b.guid] = self._get_text(b)
            guid_to_asset_map[b.guid] = b
            if level not in levels_map:
                levels_map[level] = []
            if b.guid not in levels_map[level]:
                levels_map[level].append(b.guid)

            for child in node.tier:
                cb = child.building
                if cb:
                    # Arrow points from supplier (child) to output (parent)
                    graph.add_edge(cb.guid, b.guid)
                traverse_graph(child, level + 1)

        traverse_graph(chain_base, level=0)

        # Build position coordinate layouts:
        # We reverse levels so inputs (highest level) appear on the left, and final outputs (level 0) on the right
        max_level = max(levels_map.keys()) if levels_map else 0
        for lvl, guids in levels_map.items():
            x = max_level - lvl  # left-to-right progression
            count = len(guids)
            for i, guid in enumerate(guids):
                # Distribute nodes vertically centered around 0
                y = i - (count - 1) / 2.0 if count > 1 else 0.0
                positions[guid] = (x, y)

        # Begin Plot Configuration
        fig, ax = plt.subplots(figsize=(12, 7))  # type: ignore

        # Apply themed backgrounds using our variables (Canvas background remains bg_color)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        ax.set_title(  # type: ignore
            f"Production Chain: {self._get_text(chain_asset)}",
            fontsize=15,
            pad=25,
            fontweight="bold",
            color=secondary_color,
        )

        # Draw edges with nice curves and arrowheads (using secondary color for graph connections)
        nx.draw_networkx_edges(
            graph,
            pos=positions,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=18,
            edge_color=secondary_color,
            width=2.2,
            connectionstyle="arc3,rad=0.08",
            ax=ax,
        )

        # Track which nodes were rendered successfully with image icons
        drawn_icons: set[int] = set()

        # Try drawing the node icons
        for guid, (x, y) in positions.items():
            building_asset = guid_to_asset_map.get(guid)
            if building_asset:
                try:
                    import tempfile

                    from PIL import Image as PILImage

                    icon_pkg = IconProcessor.get_icon_package(building_asset, include_image=True)
                    wand_img = icon_pkg.get("image")
                    raw_path = icon_pkg.get("path")

                    if wand_img and raw_path:
                        # Use a temporary directory to save the image with our existing save_image method
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # print(f"Created temporary directory at: {temp_dir}")
                            saved_path = IconProcessor.save_image(
                                image=wand_img,
                                original_path=raw_path,
                                output_base=temp_dir,
                                quality=90,
                                resize=(128, 128),
                                flatten=True,
                                forced_filename=f"node_{guid}",
                            )
                            if saved_path and saved_path.exists():
                                # Load the saved WebP image and immediately copy to memory before temp_dir closes
                                with PILImage.open(saved_path) as img:
                                    pil_img = img.copy()

                                # Generate the Matplotlib OffsetImage (resizing via zoom parameter)
                                imagebox = OffsetImage(pil_img, zoom=0.45)  # type: ignore
                                ab = AnnotationBbox(
                                    imagebox,
                                    (x, y),
                                    frameon=True,
                                    bboxprops=dict(
                                        edgecolor=secondary_color,
                                        lw=2.5,
                                        facecolor=primary_color,
                                        boxstyle="circle,pad=0.2",
                                    ),
                                )
                                ax.add_artist(ab)
                                drawn_icons.add(guid)
                except Exception:
                    pass

        # Draw default node shapes for any assets that couldn't render an icon (using primary/secondary theme)
        fallback_nodes = [guid for guid in positions if guid not in drawn_icons]
        if fallback_nodes:
            nx.draw_networkx_nodes(
                graph,
                pos=positions,
                nodelist=fallback_nodes,
                node_size=3500,
                node_color=primary_color,
                node_shape="o",  # Circle nodes
                alpha=0.9,
                edgecolors=secondary_color,
                ax=ax,
            )

        # Draw labels: Offset slightly downwards if an icon is drawn to keep the graphic clean
        for guid, (x, y) in positions.items():
            label_text = labels[guid]
            if guid in drawn_icons:
                # We render the text inside a separate AnnotationBbox.
                # xybox=(0, -45) offsets the text exactly 45 pixels straight down from the node center,
                # completely independent of the dynamic y-axis coordinate scale.
                text_area = TextArea(
                    label_text,
                    textprops=dict(
                        fontsize=label_fontsize, fontweight="bold", color=secondary_color, ha="center", va="center"
                    ),
                )
                ab_label = AnnotationBbox(
                    text_area,
                    (x, y),
                    xybox=(0, -55),
                    xycoords="data",
                    boxcoords="offset points",
                    frameon=True,
                    pad=0.2,
                    bboxprops=dict(boxstyle="round,pad=0.3", facecolor=bg_color, edgecolor=secondary_color, alpha=0.9),
                    arrowprops=None,
                )
                ax.add_artist(ab_label)
            else:
                # Render centered inside standard fallback nodes (use bg_color for text on primary_color nodes)
                ax.text(  # type: ignore
                    x,
                    y,
                    label_text,
                    fontsize=label_fontsize,
                    fontweight="bold",
                    color=bg_color,
                    ha="center",
                    va="center",
                )

        # Hide chart axes for clean representation
        ax.axis("off")

        # Provide some padding around coordinates
        all_x = [pos[0] for pos in positions.values()]
        all_y = [pos[1] for pos in positions.values()]
        if all_x and all_y:
            ax.set_xlim(min(all_x) - 0.4, max(all_x) + 0.4)
            ax.set_ylim(min(all_y) - 0.4, max(all_y) + 0.4)

        plt.tight_layout()
        plt.show()  # type: ignore
