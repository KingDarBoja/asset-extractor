from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache
from assetextractor.conversion.assetbrowser.convert import Converter

config = Config.from_json("config.json")
assets = AssetCache.load(config)
Converter(assets).run()