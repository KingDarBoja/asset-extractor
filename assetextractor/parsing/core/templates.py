from __future__ import annotations

import logging
import typing as t

import lxml.etree as et

from assetextractor.parsing.core.attributes import Attribute, ListItem, Property, TemplateAttribute
from assetextractor.parsing.core.common import ElementCache, Group, NamedElement, WeightedReference
from assetextractor.parsing.core.properties import MetaProperty, MetaPropertyCache, PropertyGroup, ValueDefinition

logger = logging.getLogger("parsing")

if t.TYPE_CHECKING:
    from pathlib import Path

    from assetextractor.parsing.core.assets import Asset

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

    @property
    def templates(self) -> list[Template]:
        # Get templates from this group
        result: list[Template] = [template for template in self.elements.values() if isinstance(template, Template)]
        # Get templates from all subgroups (flattened)
        for group in self.subgroups.values():
            if isinstance(group, TemplateGroup):
                result.extend(group.templates)
        return result


class TemplateCache(ElementCache[Template, TemplateGroup]):
    def __init__(self, path: Path, properties: MetaPropertyCache):
        super().__init__(path)

        self.properties = properties
        # self.nodeToGroup: Dict[et._Element, TemplateGroup] = dict()
        self._processed_templates = set[Template]()
        self._processed_defaults = set[TemplateAttribute]()

        parser = et.XMLParser(huge_tree=True)
        self.tree = et.parse(str(path), parser)

        for element in self.tree.xpath("/Templates/Group"):
            group = TemplateGroup(element, None, self)
            self.groups[group.name] = group

        TemplateAttribute.TEMPLATE_CACHE = self
        ValueDefinition.TEMPLATE_CACHE = self

        for group in self.properties.groups.values():
            self._process_property_group(group)

        # Fallback: process any MetaProperties missed by _process_property_group due to
        # duplicate group names (all-None <Name>) collapsing sibling groups into one slot.
        # All MetaProperties are registered globally in properties.elements via cache.add().
        for meta_property in self.properties.elements.values():
            self._process_meta_property(meta_property)

        for template in self:
            self._process_template(template)

    def _process_default(self, property: TemplateAttribute):
        if property in self._processed_defaults:
            return

        # allowed_templates = property.meta.allowed_templates
        # if property.template_name is None and len(allowed_templates) > 0:
        #    property.template = allowed_templates[0]
        #    property.template_name = property.template.name

        if property.template_name is not None:
            template = self.get(property.template_name)
            if template is None:
                raise ValueError(
                    f"Template {property.template_name} not found in cache for AutoCreateAsset {property.full_path} [{property.source}]"
                )

            self._process_template(template)

        # if there is no template specified, still mark as initialized
        property.resolve_inheritance(None)
        self._processed_defaults.add(property)

    def _process_value_definition(self, value_definition: ValueDefinition):
        if value_definition.data_type == "AutoCreateAsset" and isinstance(value_definition.default, TemplateAttribute):
            self._process_default(value_definition.default)

        for item in value_definition.items:
            self._process_value_definition(item)

    def _process_meta_property(self, property: MetaProperty):
        for value_definiton in property.value_definitions.values():
            self._process_value_definition(value_definiton)

        for subproperty in property.properties.values():
            self._process_meta_property(subproperty)

    def _process_property_group(self, group: PropertyGroup):
        for subgroup in group.subgroups.values():
            if isinstance(subgroup, PropertyGroup):
                self._process_property_group(subgroup)

        for property in group.defaults.values():
            self.resolve_template_attributes(property)

        for property in group.elements.values():
            if isinstance(property, MetaProperty):
                self._process_meta_property(property)

    def _process_template(self, template: Template):
        if template in self._processed_templates:
            return

        for property in template:
            group = property.meta.parent
            if not isinstance(group, PropertyGroup):
                raise ValueError(f"Property {property.full_path} [{property.source}] has no group.")
            self.resolve_template_attributes(property, template.name)

        self._processed_templates.add(template)

    def resolve_template_attributes(
        self, property: ListItem | Property | Attribute[ElementCache[t.Any, t.Any], t.Any], path: str | None = None
    ):
        if isinstance(property, TemplateAttribute):
            # Derive the template from allowed templates, if there is none specified
            # property.meta is a ValueDefinition which has a default attribute
            meta = t.cast("ValueDefinition", property.meta)
            if hasattr(meta, "default"):
                meta_default = meta.default
                if isinstance(meta_default, TemplateAttribute):
                    self._process_default(meta_default)

                if (
                    property.template_name is None
                    and isinstance(meta_default, TemplateAttribute)
                    and hasattr(meta_default, "template_name")
                    and meta_default.template_name is None
                ):
                    property.derive_template_name()

                if property.template_name is not None:
                    template = self.get(property.template_name)
                    if template is None:
                        raise ValueError(
                            f"Template {property.template_name} not found in cache for AutoCreateAsset {property.full_path} [{property.source}]"
                        )

                    self._process_template(template)

                # propagate from the updated default attribute
                # do not propagate if it is already specified (e.g. it has a Template node or initialized from DefaultValues)
                if isinstance(meta_default, TemplateAttribute):
                    property.resolve_inheritance(meta_default)  # type: ignore
                else:
                    property.resolve_inheritance(None)  # type: ignore
            else:
                property.resolve_inheritance(None)  # type: ignore

        if property.is_compound:
            for sub_property in property:
                assert isinstance(sub_property, (ListItem, Property, Attribute))
                self.resolve_template_attributes(
                    sub_property, path=f"{path}.{'Item' if isinstance(property, ListItem) else property.name}"
                )
