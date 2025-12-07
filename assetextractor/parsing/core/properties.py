from __future__ import annotations

import typing as t

import lxml.etree as et

from assetextractor.parsing.core.attributes import (
    Attribute,
    AttributeFactory,
    ListItem,
    PrimitiveAttribute,
    Property,
    TemplateAttribute,
)
from assetextractor.parsing.core.common import DatasetCache, ElementCache, Group, NamedElement

if t.TYPE_CHECKING:
    from pathlib import Path

    from assetextractor.parsing.core.texts import Text, TextCache
    from assetextractor.parsing.core.uitext import UITextCache


class ValueDefinition(NamedElement["MetaPropertyCache"]):
    """Represents a value definition in the properties.xml file. These give meta data about attributes, e.g. allowed values, data type, or description."""

    # Class variables are filled when constructing PropertyCache
    ALL_ATTRIBUTES: t.ClassVar[set[str]] = set()
    ALL_DATA_TYPES: t.ClassVar[set[str]] = set()

    def __init__(self, node: et._Element, parent: NamedElement[MetaPropertyCache], cache: MetaPropertyCache):
        super().__init__(node, parent, cache)

        data_type_node = node.find("DataType")
        if data_type_node is None or data_type_node.text is None:
            raise ValueError(f"DataType missing in {self.full_path}.")

        self.data_type = data_type_node.text
        self.variable_type = self.get_value("VariableType", str)
        self.parent = parent

        items = node.find("Items")
        self.items = [] if items is None else [ValueDefinition(item, self, cache) for item in items.iterchildren()]

        needed_property = self.get_value("NeededProperty", str)
        self.needed_property = needed_property.split(";") if needed_property else []

        self.allow_empty = self.get_value("AllowEmpty", bool)

        self.dataset = None

        if dataset := self.get_value("DataSet"):
            self.dataset = self.cache.datasets[dataset]

            # if self.data_type != "Array":
            #     print(f"{self.data_type} for {dataset} in {self.full_path}")

        self.min = self.get_value("Min", float)
        self.max = self.get_value("Max", float)
        self.is_percent = self.get_value("IsPercent", bool)

        self.default: Attribute[t.Any, t.Any] = AttributeFactory.create(
            AttributeFactory.create_default_node(
                self.name, self.data_type, next(iter(self.dataset.literals)) if self.dataset is not None else None
            ),
            parent,
            self,
            self.cache,
        )

    @property
    def is_primitive(self):
        """Represents a builtin data type."""
        return self.data_type in PrimitiveAttribute.TYPE_MAP or self.variable_type in PrimitiveAttribute.TYPE_MAP

    @property
    def is_compound(self):
        return self.data_type in ["Array", "AutoCreateAsset", "Property", "Struct", "Vector"]

    def get(self, name: str) -> NamedElement["MetaPropertyCache"] | None:
        """Returns the element with the given name or None if it does not exist."""
        for item in self.items:
            if item.name == name:
                return item

        return None

    def print_tree(self, indent: str = ""):
        if self.is_compound:
            print(f"{indent}{self.name}: " + (f"({self.description})" if self.description is not None else ""))
            for item in self.items:
                item.print_tree(indent + "\t")
        else:
            print(f"{indent}{self!s}")

    def __iter__(self) -> t.Iterator[ValueDefinition]:
        for element in self.items:
            yield element

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        text = f"{self.name}: {self.data_type}"
        if self.allow_empty:
            text += " [optional]"
        if self.min and self.max:
            text += f" [{self.min}, {self.max}]"
        elif self.dataset:
            text += f" from {self.dataset}"
        if self.description:
            text += f" ({self.description})"
        return text


class MetaProperty(NamedElement["MetaPropertyCache"]):
    """Represents the meta data for a property as defined in properties-toolone.xml file."""

    def __init__(self, node: et._Element, parent: NamedElement[MetaPropertyCache], cache: MetaPropertyCache):
        super().__init__(node, parent, cache)
        self.value_definitions: dict[str, ValueDefinition] = dict()
        self.properties: dict[str, MetaProperty] = dict()
        self.singleton: bool = self.get_value("Singleton", bool) or False
        self.export_serialize_code = self.get_value("ExportSerializeCode", bool)

        self.text: Text | None = None  # UI text for that property

        ignored = [
            "Name",
            "Description",
            "ExportTextSourceStub",
            "HasImplementation",
            "Templates",
            "ExportSerializeCode",
            "HasGameTick",
            "IsGameProperty",
            "ExportName",
            "Singleton",
            "IgnoreHashingInTemplates",
        ]
        for child in self.node.iterchildren():
            if child.tag in ignored:
                continue

            if child.tag == "Property":
                property = MetaProperty(child, self, cache)
                self.properties[property.name] = property
            elif child.tag == "ValueDefinition":
                value_definition = ValueDefinition(child, self, cache)
                self.value_definitions[value_definition.name] = value_definition
            else:
                raise ValueError(f"Unknown tag: {child.tag} in property {self.full_path}")

    def get(self, name: str) -> ValueDefinition | MetaProperty | None:
        if name in self.value_definitions:
            return self.value_definitions[name]
        if name in self.properties:
            return self.properties[name]
        return None

    @property
    def is_complex(self):
        return len(self.properties) + len(self.value_definitions) >= 2

    @property
    def is_compound(self) -> bool:
        return True

    def print_tree(self, indent: str = ""):
        print(f"{indent}{self.name}:")
        for value_definition in self.value_definitions.values():
            value_definition.print_tree(indent + "\t")
        for property in self.properties.values():
            property.print_tree(indent + "\t")

        if indent == "":
            print("*) inherited **) default")

    def __iter__(self) -> t.Iterator[ValueDefinition | MetaProperty]:
        for element in self.value_definitions.values():
            yield element

        for element in self.properties.values():
            yield element

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.value_definitions or key in self.properties

    def __getitem__(self, key: str) -> ValueDefinition | MetaProperty | None:
        """Allows bracket notation access to elements."""
        return self.get(key)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        return f"Property {self.name} with {len(self.properties)} properties and {len(self.value_definitions)} value definitions."


class PropertyGroup(Group["MetaPropertyCache"]):
    """Represents a group in the properties.xml file.
    Property Groups contain definitions for properties (stored as MetaPropery), values for containers (DefaultContainerValues) and default values for other attributes (DefaultValues).
    Unfortunately, not for all attributes a default is defined. In those cases a default value for the data type is used (e.g. 0 for numbers).
    """

    IGNORED_GROUPS: tuple[str] = tuple()  # ["ExportConditions", "ExportConditionObjectives"]
    IGNORED_TAGS = ("Name", "AdditionalTemplates", "ExportAsAction", "ExportAsCondition", "ExportAsConditionObjective")

    def __init__(self, node: et._Element, parent: NamedElement[MetaPropertyCache] | None, cache: MetaPropertyCache):
        super().__init__(node, parent, cache)

        self.cache = cache
        self.defaults: dict[str, Property] = dict()
        self.default_node: et._Element | None = None
        self.default_container_node: et._Element | None = None

        for child in self.node.iterchildren():
            if child.tag in self.IGNORED_TAGS:
                continue

            if child.tag == "Property":
                property = MetaProperty(child, self, cache)
                self.cache.add(property)
                self.elements[property.name] = property
            elif child.tag == "Groups":
                for child in child.iterchildren():
                    name_node = child.find("Name")

                    if name_node is None:
                        raise ValueError("Group has no name.")

                    if name_node.text not in self.IGNORED_GROUPS:
                        group = PropertyGroup(child, self, self.cache)
                        self.subgroups[group.name] = group
            elif child.tag == "DefaultValues":
                self.default_node = child
            elif child.tag == "DefaultContainerValues":
                self.default_container_node = child
            else:
                raise ValueError(f"Unknown tag: {child.tag} in group {self.full_path}")

        if self.default_container_node is not None:
            self._propagate_default_container_values(self, self.default_container_node)

        if self.default_node is not None:
            Property.process(self, self.default_node, self.defaults, self.cache)

    def _propagate_default_container_values(self, element: NamedElement[MetaPropertyCache], node: et._Element):
        """Store the values from DefaultContainerValues in the corresponding MetaPropery."""
        if isinstance(element, ValueDefinition) and element.data_type == "AutoCreateAsset":
            element.default = AttributeFactory.create(node, None, element, self.cache)
            return

        if isinstance(element, ValueDefinition) and not element.is_compound and node.text is not None:
            if node.text == "[NONE]":
                node.text = None

            element.default = AttributeFactory.create(node, None, element, self.cache)

            return

        if isinstance(element, ValueDefinition) and element.data_type == "Vector" and len(node.xpath("./Item")) >= 2:
            element.default = AttributeFactory.create(node, None, element, element.cache)

        for child in node.iterchildren():
            if child.tag == "LocaText":
                continue  # exported and handeled separately

            if "DEPRECATED" in str(child.tag):
                continue

            if child.tag == "ContainerValues" and isinstance(
                element, ValueDefinition
            ):  # FIXME: Do something if element is not ValueDef?
                for child_element in element.items:
                    subchild = child.find(child_element.name)

                    if subchild is not None:
                        self._propagate_default_container_values(child_element, subchild)

                continue

            child_element = element.get(str(child.tag))
            if child_element is None:
                child_element = self.cache.get(str(child.tag))

            if child_element is None:
                #    raise ValueError(f"Could not find {child.tag} in {element.get_full_path()}.")
                continue

            self._propagate_default_container_values(child_element, child)


class MetaPropertyCache(ElementCache[MetaProperty, PropertyGroup]):
    """Parses the meta description file 'properties-toolone.xml' containing discribing all attributes and value types."""

    def __init__(self, path: Path, unpacked_path: Path, datasets: DatasetCache, texts: TextCache):
        super().__init__(path)

        self.unpacked_path = unpacked_path
        self.datasets = datasets
        self.texts = texts
        self.ui_text_cache: UITextCache | None = None  # Will be set after AssetCache is loaded

        parser = et.XMLParser(huge_tree=True, remove_comments=True)
        self.tree: et._ElementTree = et.parse(str(path), parser)

        self._calculate_all_value_definitions()
        for element in self.tree.xpath("/Properties/Groups/Group"):
            name_node = element.find("Name")

            if name_node is None:
                raise ValueError("Group has no name.")

            if name_node.text not in PropertyGroup.IGNORED_GROUPS:
                group = PropertyGroup(element, None, self)
                self.groups[group.name] = group

        for group in self.groups.values():
            for property in group.defaults.values():
                self.resolve_template_attributes(property)

    def _calculate_all_value_definitions(self):
        def process_node(element: et._Element):
            if element.tag == "DataType" and element.text:
                ValueDefinition.ALL_DATA_TYPES.add(element.text)
            if element.tag == "ValueDefinition":
                for child in element.iterchildren():
                    ValueDefinition.ALL_ATTRIBUTES.add(str(child.tag))

            for child in element.iterchildren():
                process_node(child)

        process_node(self.tree.getroot())

    def resolve_template_attributes(self, property: ListItem | Property | Attribute[ElementCache[t.Any, t.Any], t.Any]):
        """Once all properties are created, this method iterates the properties of an AutoCreateAsset attribute and updates the default values. This can only be done after initializing the cache to ensure all properties have been created."""
        if isinstance(property, TemplateAttribute):
            if property.value_node is None:
                raise ValueError(f"AutoCreateAsset attribute has no values: {property.meta.full_path}.")

            property.process_properties()

        # nested AutoCreateAsset
        if property.is_compound:
            for sub_property in property:
                assert isinstance(sub_property, (ListItem, Property, Attribute))
                self.resolve_template_attributes(sub_property)
