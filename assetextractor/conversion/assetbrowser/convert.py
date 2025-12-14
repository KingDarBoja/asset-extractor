import shutil
from copy import deepcopy
from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from lxml.etree import indent, tostring

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.parsing.core.templates import Template


class Converter:
    def __init__(self, cache: AssetCache):
        self.assets = cache

        # Set up Jinja2 environment
        self.template_dir = Path(__file__).parent / "templates"
        self.output_dir = Path(__file__).parent / "../../../results/assetbrowser/"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)), trim_blocks=True, lstrip_blocks=True)

    def render_elements(self, elements: list[Asset | Template], jinja_template_name: str, output_subdirectory: str):
        template = self.env.get_template(jinja_template_name)

        output_dir = (self.output_dir / output_subdirectory).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        for element in elements:
            # Create a deep copy of the node to avoid modifying the original
            node_copy = deepcopy(element.node)
            # Force proper indentation regardless of source XML formatting
            indent(node_copy, space="  ")

            html = template.render(
                asset=element,
                template=element,
                xml=escape(tostring(node_copy, encoding="unicode")),
            )
            element_id = element.safe_identifier
            filename = f"{element_id}.html"
            filepath = output_dir / filename
            with filepath.open("w", encoding="utf-8") as f:
                f.write(html)

    def render_overview(self):
        template = self.env.get_template("template_cache.html")

        html = template.render(cache=self.assets.templates)

        filepath = self.output_dir / "index.html"
        with filepath.open("w", encoding="utf-8") as f:
            f.write(html)

    def run(self):
        # Copy styles.css to the output directory
        src_css = self.template_dir.parent / "styles.css"
        dst_css = self.output_dir / "styles.css"
        dst_css.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_css.resolve()), str(dst_css))

        self.render_elements(list(self.assets), "asset.html", "assets")
        self.render_elements(list(self.assets.templates), "template.html", "templates")
        self.render_overview()


if __name__ == "__main__":
    config = Config.from_json("config.json")
    cache = AssetCache.load(config)
    converter = Converter(cache)
    converter.run()
