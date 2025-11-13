from __future__ import annotations

import typing as t
from contextlib import suppress

import lxml.etree as et

from assetextractor.parsing.core.attributes import (
    DictAttribute,
    ListAttribute,
    Property,
    ReferenceAttribute,
    TemplateAttribute,
)
from assetextractor.parsing.core.common import ElementCache, Group, NamedElement
from assetextractor.parsing.core.properties import Attribute, DatasetCache, MetaPropertyCache
from assetextractor.parsing.core.templates import (
    NamedRefColT,
    Template,
    TemplateCache,
    TemplateGroup,
    WeightedReference,
)
from assetextractor.parsing.core.texts import TextCache

if t.TYPE_CHECKING:
    from pathlib import Path

    from assetextractor.extraction.utils import Config


class Asset(NamedElement["AssetCache"]):
    IGNORED_TAGS = ("Template", "BaseAssetGUID")

    def __init__(self, node: et._Element, cache: AssetCache):
        super().__init__(node, None, cache, name="")

        self.cache = cache

        guid_text = node.findtext("Values/Standard/GUID")
        if guid_text is None:
            raise ValueError(f"GUID missing in {node.text}.")
        self.guid = int(guid_text)

        self.name = node.findtext("Values/Standard/Name")

        self.text = None
        if text_id := node.findtext("Values/Text/OasisId"):
            with suppress(Exception):
                self.text = cache.texts.get(int(text_id))
        if self.text is None:
            self.text = cache.texts.get(self.guid)

        self.base_asset_guid = self.get_value("BaseAssetGUID", int)
        self.base_asset = None
        self.instances: dict[int, WeightedReference] = dict()

        template = self.get_value("Template")
        if template is None and self.base_asset_guid is None:
            raise ValueError(f"Template missing in Asset {self.name}.")

        self.referenced_by: dict[int, WeightedReference] = dict()

        self.unlocked_by_dlcs: dict[int, WeightedReference] = dict()
        self.named_reference_collections: NamedRefColT = {
            "Instances": self.instances,
            "Referenced by": self.referenced_by,
            "Unlocked by DLCs": self.unlocked_by_dlcs,
        }  # Referenced by, construction cost, etc.

        self.properties: dict[str, Property] = dict()

        self.value_node = node.find("Values")
        if self.value_node is None:
            self.value_node = self.node

        if template is None:
            return  # properties filled in resolve_inheritance

        self.template = self.cache.templates[template]

        if self.template is None:
            raise ValueError(f"Template {template} not found for asset {self.guid}.")

        self.template.add_instance(self)

        for template_property in self.template.properties.values():
            self._process_property(template_property)

    @property
    def identifier(self):
        return str(self.guid)

    @property
    def property_path(self) -> str:
        return ""

    def _process_property(self, template_property: Property):
        assert self.value_node is not None
        name = template_property.name
        child = self.value_node.find(name)

        if child is None or len(child) == 0:
            property = template_property
        else:
            property = Property(child, self, template_property.meta, self.cache.properties)
            property.resolve_inheritance(template_property)

        self.properties[name] = property
        setattr(self, name, property)

    def resolve_inheritance(self, asset: Asset):
        self.base_asset = asset
        self.template = asset.template
        asset.instances[self.guid] = WeightedReference(self, asset, "BaseAssetGUID")

        for base_property in asset.properties.values():
            self._process_property(base_property)

    def set_referenced_by(self, source: Asset, reference: ReferenceAttribute):
        self.referenced_by[source.guid] = WeightedReference(source, self, reference.property_path)

    def print_tree(self):
        print(str(self))
        for property in self.properties.values():
            property.print_tree("\t")

        print("*) inherited **) default")

    def print_meta_tree(self):
        if self.template is not None:
            self.template.print_meta_tree()

    @property
    def short_description(self) -> str:
        if self.text is not None:
            text = self.text()  # use text converter
            if len(text) <= 120:
                return text
            else:
                return text[:120] + "..."

        if self.name is not None:
            return self.name

        return "{" + self.identifier + "}"

    @property
    def long_description(self):
        assert self.template
        return f"{self.name} [{self.guid} - {self.template.name}]"

    @property
    def is_compound(self) -> bool:
        return True

    def __getitem__(self, key: str) -> Property | None:
        """Allows bracket notation access to elements."""
        return self.properties.get(key)

    def __iter__(self):
        for property in self.properties.values():
            yield property

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.properties

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return self.short_description


class AssetGroup(Group["AssetCache"]):
    """Represents a group in the assets.xml."""

    def __init__(self, node: et._Element, parent: AssetGroup | None, template_group: TemplateGroup, cache: AssetCache):
        super().__init__(node, parent, cache, name=template_group.name)

        self.cache = cache

        for child in self.node.iterchildren():
            if child.tag == "Groups":
                for subchild, template_subgroup in zip(child.iterchildren(), template_group.subgroups.values()):
                    assert template_subgroup is TemplateGroup  # FIXME: Is this correct?
                    group = AssetGroup(subchild, self, template_subgroup, self.cache)
                    self.subgroups[group.name] = group
            elif child.tag == "Assets":
                for subchild in child.iterchildren():
                    asset = Asset(subchild, self.cache)
                    self.cache.add(asset)
                    self.elements[asset.guid] = asset
            else:
                raise ValueError(f"Unknown tag: {child.tag} in group {self.full_path}")


class AssetCache(ElementCache[t.Any]):
    def __init__(self, path: Path, templates: TemplateCache):
        super().__init__(path)

        self.templates = templates
        self.properties = templates.properties
        self.texts = self.properties.texts
        self.datasets = self.properties.datasets

        parser = et.XMLParser(huge_tree=True, remove_comments=True)
        if path.is_file():
            self.tree = et.parse(str(path), parser)
        else:
            root = et.Element("Root")
            for file in path.rglob("*.xml"):
                if file.name == "test.xml":
                    continue
                tree = et.parse(str(file), parser)
                if tree.getroot().tag == "Group":
                    root.append(tree.getroot())
                self.tree = et.ElementTree(root)

        # for element, template_group in zip(self.tree.xpath("/AssetList/Groups/Group"), self.templates.groups.values()):
        #     group = AssetGroup(element, self, template_group, self)
        #     self.groups[group.name] = group

        for element in self.tree.xpath("//Assets/Asset"):
            asset = Asset(element, self)
            self.elements[asset.guid] = asset

        for asset in self.elements.values():
            self.resolve_inheritance(asset)

        for template in self.templates:
            self.resolve_references(template)

        for asset in self.elements.values():
            self.resolve_references(asset)

        self.resolve_dlc_unlocks()

    def add(self, element: Asset):
        if self.key_type is str:
            super().add(element)
        else:
            self.elements[element.guid] = element

    def resolve_inheritance(self, asset: Asset):
        if asset.base_asset_guid is None or asset.base_asset is not None:
            return

        base_asset = self.elements[asset.base_asset_guid]
        self.resolve_inheritance(base_asset)  # recursively resolve inheritance of base asset first
        asset.resolve_inheritance(base_asset)
        for property in asset:
            self.templates.resolve_template_attributes(property)

    def resolve_references(self, asset: Asset | Template):
        def process_property(property: Property):
            for meta_property in property.meta.properties.values():
                process_property(getattr(property, meta_property.name))

            for value_definition in property.meta.value_definitions.values():
                attr = getattr(property, value_definition.name)
                if attr is None:
                    print(f"Missing attribute {value_definition.name} in {property.full_path}")
                    pass
                else:
                    process_attribute(attr)

        def process_attribute(element: Attribute[t.Any, t.Any]):
            if isinstance(element, ReferenceAttribute):
                if element.guid == 0:  # Skip references with default value
                    return

                if isinstance(asset, Asset):
                    element.set_reference(asset, self.get(element.guid))

            if isinstance(element, ListAttribute):
                for item in element:
                    for attr in item:
                        process_attribute(attr)

            if isinstance(element, DictAttribute):
                for attr in element:
                    process_attribute(attr)

            if isinstance(element, TemplateAttribute):
                for attr in element:
                    process_property(attr)

        for property in asset.properties.values():
            process_property(property)

    def resolve_dlc_unlocks(self):
        template_list: list[Template] = []

        for template in self.templates:
            if "Locked" in template and len(template.instances) > 0:
                template_list.append(template)

        for template in template_list:
            for asset in template.assets:
                dlc_attr = asset.find("Locked.DLCDependency")
                assert isinstance(dlc_attr, ReferenceAttribute)
                dlc = dlc_attr.value
                if dlc is not None:
                    weighted_reference = WeightedReference(source=asset, target=dlc)
                    asset.unlocked_by_dlcs[dlc.guid] = weighted_reference

    @staticmethod
    def load(config: Config) -> AssetCache:
        """Loads the asset cache from the given config."""
        """Determine paths for 117 or 1800"""
        unpacked_path = config.cache_path
        if (unpacked_path / "data/base").exists():
            export_dir = unpacked_path / "data/base/config/export"
            game_dir = unpacked_path / "data/base/config/game"
            game_asset_dir = game_dir / "asset"

            # ignore old game assets
            #if not game_asset_dir.exists():
            game_asset_dir = None
            gui_dir = unpacked_path / "data/base/config/gui"
        else:
            export_dir = unpacked_path / "data/config/export/main/asset"
            game_dir = None
            game_asset_dir = None
            gui_dir = unpacked_path / "data/config/gui"

        if not export_dir.exists():
            raise FileNotFoundError(f"Directory {export_dir} not found.")

        """Load datasets"""
        dataset_path = export_dir / "datasets.xml"
        if not dataset_path.exists() and game_dir is not None:
            dataset_path = game_dir / "datasets.xml"

        if not dataset_path.exists():
            raise FileNotFoundError(f"File {dataset_path} not found.")

        datasets = DatasetCache(dataset_path)

        """Load texts"""
        language = datasets["Language"]

        if language is None:
            raise ValueError("Language not found in datasets.xml.")

        texts = TextCache(gui_dir, language)

        """Load properties"""
        path_properties = export_dir / "properties-toolone.xml"

        if not path_properties.exists():
            path_properties = export_dir / "properties-meta.xml"

        if not path_properties.exists() and game_asset_dir is not None:
            path_properties = game_asset_dir / "properties.xml"

        if not path_properties.exists():
            raise FileNotFoundError(f"File {path_properties} not found.")

        properties = MetaPropertyCache(path_properties, unpacked_path, datasets, texts)

        """Load templates"""
        path_templates = (
            game_asset_dir / "templates.xml" if game_asset_dir is not None else export_dir / "templates.xml"
        )

        if not path_templates.exists():
            raise FileNotFoundError(f"File {path_templates} not found.")

        templates = TemplateCache(path_templates, properties)

        path_assets = game_asset_dir if game_asset_dir is not None else export_dir / "assets.xml"

        return AssetCache(path_assets, templates)
