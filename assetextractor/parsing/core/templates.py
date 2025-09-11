from __future__ import annotations

import logging
import typing as t

import lxml.etree as et

from assetextractor.parsing.core.attributes import Attribute, ListItem, Property, TemplateAttribute
from assetextractor.parsing.core.common import ElementCache, Group, NamedElement
from assetextractor.parsing.core.properties import MetaPropertyCache, PropertyGroup

logger = logging.getLogger("parsing")

if t.TYPE_CHECKING:
    from pathlib import Path

    from assetextractor.parsing.core.assets import Asset


class WeightedReference:
    """
    Stores a a reference from source to target.
    If path is set, the reference is stored in the target and path is the property path in source to the ReferenceAttribute.
    The optional weight can represent an amount or probability.
    """

    def __init__(self, source: Asset, target: Asset | Template, path: str | None = None, weight: float | None = None):
        self.source = source
        self.target = target
        self.path = path
        self.is_forward = path is None
        self.weight = weight

    def __rep__(self):
        return self.__str__()

    def __str__(self):
        if self.is_forward:
            return f"{self.target!s}"
        return f"{self.source!s} from {self.path}"


NamedRefColT = dict[str, dict[int, WeightedReference]]


class Template(NamedElement["TemplateCache"]):
    """Represents a template in the templates.xml file."""

    IGNORED_NAMES: t.ClassVar[list[str]] = []

    def __init__(self, node: et._Element, parent: TemplateGroup, cache: TemplateCache):
        super().__init__(node, parent, cache)

        self.properties: dict[str, Property] = {}
        self.cache = cache
        self.instances: dict[int, WeightedReference] = dict()
        self.named_reference_collections: NamedRefColT = {
            "Instances": self.instances
        }  # Referenced by, construction cost, etc.

        ignored = ["Name", "Description", "IsExpertTemplate", "HiddenValues"]
        for child in self.node.iterchildren():
            if child.tag in ignored:
                continue

            if child.tag == "Properties":
                for subchild in child.iterchildren():
                    meta_property = self.cache.properties.get(str(subchild.tag))
                    if meta_property is None:
                        raise ValueError(f"Property {subchild.tag} not found for {self.full_path}.")

                    property = Property(subchild, self, meta_property, self.cache.properties)
                    if isinstance(meta_property.parent, PropertyGroup):
                        defaults = meta_property.parent.defaults.get(meta_property.name)
                        if defaults is not None:
                            # print(f"Add defaults for {meta_property.name} on {self.name}")
                            property.resolve_inheritance(defaults)
                    self.properties[str(subchild.tag)] = property
                    setattr(self, meta_property.name, property)
            else:
                raise ValueError(f"Unknown tag: {child.tag} in property {self.full_path}")

    def add_instance(self, instance: Asset):
        self.instances[instance.guid] = WeightedReference(instance, self, "Template")

    @property
    def property_path(self) -> str:
        return ""

    def print_tree(self):
        """Prints the template tree."""
        print(f"Template {self.name} ({self.full_path})")
        for property in self.properties.values():
            property.print_tree("\t")

        print("*) inherited **) default")

    def print_meta_tree(self):
        """Prints the meta definiton of the template."""
        print(f"Template {self.name} ({self.full_path})")
        for property in self.properties.values():
            property.meta.print_tree("\t")

    @property
    def is_compound(self) -> bool:
        return True

    @property
    def assets(self) -> list[Asset]:
        return [ref.source for ref in self.instances.values()]

    def __iter__(self):
        for attribute in self.properties.values():
            yield attribute

    def __getitem__(self, key: str) -> Property | None:
        """Allows bracket notation access to elements."""
        return self.properties.get(key)

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.properties

    def __str__(self) -> str:
        """Returns a string representation of the template."""
        return f"Template {self.name} ({len(self.instances)} assets)"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def long_description(self):
        return f"Template {self.name} with {len(self.properties)} properties [{len(self.instances)} Assets]."


class TemplateGroup(Group["TemplateCache"]):
    """Represents a group in the templates.xml file."""

    def __init__(self, node: et._Element, parent: NamedElement[TemplateCache] | None, cache: TemplateCache):
        super().__init__(node, parent, cache)

        self.cache = cache

        for child in self.node.iterchildren():
            if child.tag == "Name":
                continue

            if child.tag == "Group":
                group = TemplateGroup(child, self, self.cache)
                self.subgroups[group.name] = group
            elif child.tag == "Template":
                if child.find("Name") is not None and str(child.find("Name").text) in Template.IGNORED_NAMES:  # type: ignore
                    continue
                template = Template(child, self, self.cache)
                self.cache.add(template)
                self.elements[template.name] = template
            else:
                raise ValueError(f"Unknown tag: {child.tag} in group {self.full_path}")

        # self.cache.nodeToGroup[node] = self


class TemplateCache(ElementCache[Template, TemplateGroup]):
    def __init__(self, path: Path, properties: MetaPropertyCache):
        super().__init__(path)

        self.properties = properties
        # self.nodeToGroup: Dict[et._Element, TemplateGroup] = dict()

        parser = et.XMLParser(huge_tree=True)
        self.tree = et.parse(str(path), parser)

        for element in self.tree.xpath("/Templates/Group"):
            group = TemplateGroup(element, None, self)
            self.groups[group.name] = group

        for template in self:
            for property in template:
                group = property.meta.parent
                if not isinstance(group, PropertyGroup):
                    raise ValueError(f"Property {property.full_path} has no group.")
                self.resolve_template_attributes(property, template.name)

    def resolve_template_attributes(
        self, property: ListItem | Property | Attribute[ElementCache[t.Any, t.Any], t.Any], path: str | None = None
    ):
        if isinstance(property, TemplateAttribute):
            # property.process_properties()
            try:
                if property.template_name is None:
                    raise ValueError(
                        f"Missing template name for {property.meta.full_path if property.is_default else property.full_path}."
                    )

                ref_template = self.get(property.template_name)
                if ref_template is None:
                    raise ValueError(
                        f"Template {property.template_name} not found for {property.meta.full_path if property.is_default else property.full_path} with path {path}."
                    )

                property.set_template(ref_template)
            except ValueError as e:
                logger.debug(e)

        if property.is_compound or isinstance(property, TemplateAttribute):
            for sub_property in property:
                assert isinstance(sub_property, (ListItem, Property, Attribute))
                self.resolve_template_attributes(
                    sub_property, path=f"{path}.{'Item' if isinstance(property, ListItem) else property.name}"
                )
