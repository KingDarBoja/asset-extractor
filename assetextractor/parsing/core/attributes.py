from __future__ import annotations

import base64
import datetime
import logging
import typing as t
from io import BytesIO
from pathlib import Path

import lxml.etree as et
from wand.image import Image as WandImage  # type: ignore

from assetextractor.parsing.core.common import ElementCache, NamedElement
from assetextractor.parsing.core.texts import Text

logger = logging.getLogger("parsing")

type AttributeParentT = Attribute[MetaPropertyCache, t.Any] | Property | ListItem | None

if t.TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset
    from assetextractor.parsing.core.properties import MetaProperty, MetaPropertyCache, PropertyGroup, ValueDefinition
    from assetextractor.parsing.core.templates import Template


def parse_bool(text: str | None) -> bool:
    if text is None:
        return False
    return str(text).strip().lower() not in ("0", "false", "")


# Property must be here due to cyclic constructor calls between Property and TemplateAttribute
class Property(NamedElement[t.Any]):
    """Building block for templates, can be nested. Can be used like a dictionary with the only exception that a for-each iterates over values instead of keys. One can easily get the key by `value.name`."""

    def __init__(self, node: et._Element, parent: NamedElement[t.Any], meta: MetaProperty, cache: MetaPropertyCache):
        super().__init__(node, parent, cache, str(node.tag))

        self.meta = meta
        self.cache = cache
        self.inherited = False
        self.attributes: dict[str, Attribute[t.Any, t.Any]] = dict()
        self.properties: dict[str, Property] = dict()
        self._full_path = None
        self._property_path = None

        all_properties = set(child for child in self.node.iterchildren() if isinstance(child.tag, str))
        for meta_property in self.meta.properties.values():
            # if meta_property.export_serialize_code:
            #    continue

            name = meta_property.name
            child = node.find(name)
            if child is None:
                setattr(self, name, None)
                continue
            all_properties.remove(child)

            self.properties[name] = Property(child, self, meta_property, self.cache)
            setattr(self, name, self.properties[name])

        for value_definition in self.meta.value_definitions.values():
            name = value_definition.name
            child = node.find(name)

            if child is not None:
                all_properties.remove(child)

            attribute = AttributeFactory.create(child, self, value_definition, cache)

            self.attributes[name] = attribute
            setattr(self, name, attribute)

        for child in all_properties:
            logger.info(f"Ignoring property {child.tag} without meta definition in property {self.full_path}")

    @property
    def is_compound(self) -> bool:
        return True

    @staticmethod
    def process(parent: PropertyGroup, node: et._Element, container: dict[str, Property], cache: MetaPropertyCache):
        """Creates Property objects given an xml node and stores them in container."""
        for child in node.iterchildren():
            meta_property = parent.elements.get(str(child.tag))

            if meta_property is None:
                logger.info(f"Ignoring property {parent.full_path}.{child.tag}")
                continue

            # this check would lead to cyclic imports
            # if not isinstance(meta_property, MetaProperty):
            #    raise ValueError(f"Got group but expected property for {child.tag} in {parent.full_path}")

            prop = Property(child, parent, meta_property, cache)  # type: ignore
            container[str(prop.name)] = prop

    def resolve_inheritance(self, default: Property):
        """Recursively override not initialized attributes with the values form default."""
        for meta_property in self.meta.properties.values():
            # if meta_property.export_serialize_code:
            #    continue

            if (prop := self.properties.get(meta_property.name)) is None:
                logger.debug(f"Copy {meta_property.name} from {default.full_path}")
                prop = getattr(default, meta_property.name)
                setattr(self, meta_property.name, prop)
                if prop is not None:
                    self.properties[meta_property.name] = prop
            else:
                logger.debug(f"{prop.name} from {default.full_path}")
                prop.resolve_inheritance(getattr(default, meta_property.name))

        for value_definition in self.meta.value_definitions.values():
            name = value_definition.name
            default_attr = default.attributes.get(name)
            if default_attr is None:
                raise ValueError(
                    f"Missing attribute {name} of type {value_definition.data_type} in {default.full_path} (found when updating inheritance in {self.full_path})"
                )

            if (attr := self.attributes.get(name)) is None:
                logger.debug(f"Copy {name} from {default_attr.full_path}")
                setattr(self, name, default_attr)
                self.attributes[name] = default_attr
            else:
                if attr.is_default:
                    logger.debug(f"Copy {attr.name} from default {default_attr.full_path}")
                    self.attributes[name] = default_attr
                    setattr(self, name, default_attr)
                else:
                    logger.debug(f"{attr.name} from {default.full_path}")
                    attr.resolve_inheritance(default_attr)

    # def get_all_attributes(self) -> List[Attribute]:
    #     name = "_all_attributes"
    #     if not hasattr(self, name):
    #         all_attributes = []
    #         for meta_property in self.meta.properties.values():
    #             all_attributes += getattr(self, meta_property.name).get_all_attributes()

    #         for value_definition in self.meta.value_definitions.values():
    #             value = getattr(self, value_definition.name)

    #         setattr(self, name, all_attributes)
    #     return getattr(self, name)

    def get_tree_note(self, inherited: bool) -> str:
        if inherited:
            return "*"

        return ""

    def print_tree(self, indent: str = "", inherited: bool = False):
        print(f"{indent}{self.name}{self.get_tree_note(inherited)}:")
        for attribute in self.attributes.values():
            attribute.print_tree(indent + "\t", attribute.parent != self)
        for property in self.properties.values():
            property.print_tree(indent + "\t", property.parent != self)

        if indent == "":
            print("*) inherited")

    def print_meta_tree(self, indent: str = ""):
        self.meta.print_tree(indent)

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.attributes or key in self.properties

    def __iter__(self) -> t.Iterator[Attribute[ElementCache[t.Any, t.Any], t.Any] | Property]:
        for attribute in self.attributes.values():
            yield attribute

        for attribute in self.properties.values():
            yield attribute

    def __getitem__(self, key: str) -> Attribute[t.Any, t.Any] | Property | None:
        """Allows bracket notation access to elements."""
        if key in self.attributes:
            return self.attributes[key]
        if key in self.properties:
            return self.properties[key]
        return None


class Attribute[CacheT: ElementCache[t.Any, t.Any], ValueT](NamedElement[CacheT]):
    """Virtual base class for all attributes."""

    def __init__(self, node: et._Element, parent: t.Any, meta: ValueDefinition, cache: CacheT):
        super().__init__(node, parent, cache, name=str(node.tag))

        self.meta = meta
        self.cache = cache
        self.value: ValueT | None = None

        self._value_text = node.text

    def resolve_inheritance(self, default: t.Self | None):
        if self.meta.default == self and default is not None:
            raise ValueError(f"Trying to override default attribute {self.meta.full_path} with {default.full_path}")

        if default is not None and self.value is None:
            self.value = default.value  # For non-primitive attributes: copy values from default to self

    @property
    def is_compound(self) -> bool:
        """Checks if the attribute is compound."""
        return self.meta.is_compound

    @property
    def is_default(self) -> bool:
        """Checks if the attribute is default."""
        return self.meta.default == self

    def get_tree_note(self, inherited: bool = False) -> str:
        """Returns a note for the tree representation."""
        if self.is_default:
            return "**"
        if inherited:
            return "*"

        return ""

    def print_tree(self, indent: str = "", inherited: bool = False):
        print(f"{indent}{self!s} {self.get_tree_note(inherited)}")
        if indent == "":
            print("*) inherited **) default")

    def print_meta_tree(self, indent: str = ""):
        self.meta.print_tree(indent)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        return f"{self.name}: {self.value!s}{'%' if self.meta.is_percent or getattr(self, 'percental', False) else ''}"

    def __call__(self) -> t.Any:
        return self.value

    def __getitem__(self, key: int | str) -> str | ListItem | Attribute[t.Any, t.Any] | Property | None:
        """Allows bracket notation access to elements."""
        if self._value_text is None:
            return None

        if isinstance(key, str):
            raise ValueError(
                f"Trying key access with {key} on attribute {self.meta.full_path if self.is_default else self.full_path}"
            )
        else:
            return self._value_text[key]


class PrimitiveAttribute(Attribute["MetaPropertyCache", bool | str | float | int]):
    TYPE_MAP: t.ClassVar[t.Mapping[str | None, type[t.Any]]] = {
        "Boolean": bool,
        "Choice": str,
        "Float": float,
        "FloatOrPercental": float,
        "Int64": int,
        "Integer": int,
        "ScriptId": str,
        "String": str,
        "UnsignedInt64": int,
    }

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)

        if self._value_text is None:
            self.value = None
            return

        data_type = meta.data_type
        self.percental = False

        if data_type == "FloatOrPercental":
            percental_node = node.find("Percental")
            if percental_node is not None and percental_node.text is not None:
                self.percental = parse_bool(percental_node.text)

            value_node = node.find("Value")
            try:
                if value_node is None:
                    self.value = None
                elif value_node.text is not None:
                    self.value = float(value_node.text)
                else:
                    self.value = float(self._value_text)
            except ValueError:
                raise ValueError(
                    f"Could not convert {self._value_text} to float in {self.meta.full_path if self.is_default else self.full_path}: {et.tostring(self.node, pretty_print=True).decode('utf-8')}"
                )

            return

        if data_type == "Boolean":
            self.value = parse_bool(self._value_text)
            return

        if data_type in self.TYPE_MAP:
            try:
                self.value = self.TYPE_MAP[data_type](self._value_text)
            except ValueError:
                raise ValueError(
                    f"Could not convert {self._value_text} to {data_type} in {self.meta.full_path if self.is_default else self.full_path}."
                )
        else:
            raise ValueError(
                f"Unknown data type: {data_type} in {self.meta.full_path if self.is_default else self.full_path}."
            )


class ColorAttribute(Attribute["MetaPropertyCache", dict[str, int] | int]):
    """Represents a color attribute that can handle both single value and dictionary-like XML structures."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)

        if len(node) == 0:  # Single value case
            try:
                self.value = int(self._value_text) if self._value_text else None
            except ValueError:
                raise ValueError(
                    f"Could not convert {self._value_text} to int in {self.meta.full_path if self.is_default else self.full_path}."
                )
        else:  # Dictionary-like structure case
            self.value = {}
            for child in node.iterchildren():
                try:
                    if child.text is None or str(child.tag) == "ColorMode":
                        continue

                    self.value[str(child.tag)] = int(child.text)
                except ValueError:
                    print(f"XML for {node.tag}:\n{et.tostring(node, pretty_print=True).decode('utf-8')}")
                    raise ValueError(
                        f"Could not convert {child.text} to int in {self.meta.full_path if self.is_default else self.full_path}."
                    )

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        if isinstance(self.value, dict):
            return key in self.value
        return False

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        if isinstance(self.value, dict):
            return f"{self.name}: {self.value}"
        return f"{self.name}: {self.value}"


class TextAttribute(Attribute["MetaPropertyCache", Text]):
    """A localized text stored in texts_*.xml. Internal strings are stored as PrimitiveAttribute of data type string."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)
        self.value = self.cache.texts.get(int(self._value_text)) if self._value_text else None

    def __iter__(self) -> t.Iterator[str]:
        if self.value is None:
            return

        for text in self.value.values.values():
            yield text

    def __getitem__(self, key: int | str) -> str | None:
        """Allows bracket notation access to elements."""
        if self.value is None:
            return None

        if isinstance(key, str):
            if self.cache.texts.languages.get(key) is None:
                raise ValueError(
                    f"Unknown language {key} when accessing text attribute {self.meta.full_path if self.is_default else self.full_path}"
                )
            return self.value.values.get(key)
        else:
            raise ValueError(
                f"Trying index access with {key} on the time attribute {self.meta.full_path if self.is_default else self.full_path}"
            )

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.cache.texts.languages

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        if self._value_text == "0":
            return f'{self.name}:""'
        if self.value is None:
            return f"{self.name}: Missing text with id {self._value_text}"
        return f"{self.name}: {self.value!s}"


class TimeAttribute(Attribute["MetaPropertyCache", datetime.timedelta]):
    """Represents a duration."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)
        self.value = datetime.timedelta(milliseconds=int(self._value_text)) if self._value_text else None


class UpgradeAttribute(Attribute["MetaPropertyCache", int]):
    """Consists of an amount (stored in value) and bool percental."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)
        value = node.find("Value")

        if value is None:
            self.value = 0
            self._value_text = None
        else:
            self._value_text = value.text
            try:
                self.value = int(value.text) if value.text else None
            except ValueError:
                raise ValueError(
                    f"Could not convert {value} to int in {self.meta.full_path if self.is_default else self.full_path}"
                )

        percental = node.find("Percental")
        if percental is not None:
            self.percental = parse_bool(percental.text)
        else:
            self.percental = None

    def resolve_inheritance(self, default: t.Self | None):
        if self.meta.default == self and default is not None:
            raise ValueError(f"Trying to override default attribute {self.meta.full_path} with {default.full_path}")

        if default is None:
            return

        if self._value_text is None:  # value is initialized with 0
            self.value = default.value
        if self.percental is None:
            self.percental = default.percental


class FlagsAttribute(Attribute["MetaPropertyCache", list[str]]):
    """A (potentially empty) list of literals. See self.meta.dataset.literals for all literals."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)
        self.value = self._value_text.split(";") if self._value_text else []

    def __contains__(self, key: str | int) -> bool:
        """Allows the use of the 'in' keyword."""
        assert self.value is not None
        return key in self.value

    def __iter__(self) -> t.Iterator[str]:
        if self.value is None:
            return

        for flag in self.value:
            yield flag

    def __getitem__(self, key: int | str) -> str | ListItem | None:
        """Allows bracket notation access to elements."""
        if self.value is None:
            return None

        if isinstance(key, str):
            raise ValueError(
                f"Trying key access with {key} on list attribute {self.meta.full_path if self.is_default else self.full_path}"
            )
        else:
            if key >= len(self.value):
                raise IndexError(
                    f"Index {key} out of range for {self.meta.full_path if self.is_default else self.full_path}"
                )
            return self.value[key]


class FileNameAttribute(Attribute["MetaPropertyCache", Path]):
    """Stores a link to another file. The link is resolved to your local cache directory."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)

        if self._value_text is None:
            return

        self.value = self.cache.unpacked_path / Path(self._value_text)
        if self.is_image:
            self.value = self.value
            if not self.value.exists():
                self.value = self.value.with_suffix(".dds")
            if not self.value.exists() and not self.value.stem.endswith("_0"):
                self.value = self.value.with_stem(self.value.stem + "_0")
            if not self.value.exists():
                # Try alternative subfolders for UI images
                ui_index = None
                parts = list(self.value.parts)
                for i, part in enumerate(parts):
                    if part == "ui":
                        ui_index = i
                        break

                if ui_index is not None and ui_index + 1 < len(parts):
                    for subfolder in ["4k", "4kimages", "2kimages"]:
                        alt_parts = parts[:]
                        alt_parts[ui_index + 1] = subfolder
                        alt_path = Path(*alt_parts)
                        if alt_path.exists():
                            self.value = alt_path
                            break

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        assert self.value is not None
        return key in str(self.value)

    def __getitem__(self, key: int | str) -> str | None:
        raise ValueError(
            f"Trying index access with {key} on the filename attribute {self.meta.full_path if self.is_default else self.full_path}"
        )

    @property
    def identifier(self) -> str:
        if self._value_text is None:
            return ""

        return str(Path(self._value_text).as_posix())

    @property
    def is_image(self) -> bool:
        """Checks if the file is an image."""
        if self.value is None:
            return False

        return str(self.value).endswith((".png", ".jpg", ".jpeg", ".tga", ".bmp", ".gif", ".dds"))

    def get_image(self) -> WandImage | None:
        """Returns the image if the file is an image."""
        if self.value is None or not self.is_image:
            return None

        try:
            filename = self.value
            logger.debug(f"Loading image {filename}")

            if not filename.exists():
                logger.error(f"Image {filename} does not exist.")
                return None

            return WandImage(filename=str(filename))
        except Exception as e:
            logger.error(f"Could not load image {self.value}: {e}")
            return None

    def get_data_url(self) -> str | None:
        """Returns the data URL of the image if the file is an image."""
        data = self.get_image()
        if data is None:
            return None

        try:
            with WandImage(data) as webp_img:
                webp_img.format = "webp"
                buffer = BytesIO()
                webp_img.save(file=buffer)  # type: ignore
                base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
                return f"data:image/webp;base64,{base64_str}"
        except Exception as e:
            logger.error(f"Could not encode image {self.value}: {e}")
            return None


class ReferenceAttribute(Attribute["MetaPropertyCache", "Asset"]):
    """Stores a reference to another asset. If the reference is invalid (i.e. the destination does not exist) the value is None."""

    IGNORED_VALUES = ("Human0", "Resident_tier01_atWork")

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)
        self.guid = (
            0 if (self._value_text in self.IGNORED_VALUES or self._value_text is None) else int(self._value_text)
        )
        self.value = None  # is set in constructor of AssetCache

    def set_reference(self, source: Asset, target: Asset | None):
        # ReferenceAttribute might be included in several assets
        self.value = target

        if self.value is None:
            logger.info(
                f"Invalid reference {self.guid} in {self.meta.full_path if self.is_default else self.full_path}"
            )
        else:
            self.value.set_referenced_by(source, self)

    @property
    def is_compound(self) -> bool:
        return True

    def resolve_inheritance(self, default: t.Self | None):
        if default is not None and self.guid == 0:
            self.value = default.value
            self.guid = default.guid

    def __iter__(self) -> t.Iterator[Property]:
        if self.value is None:
            return

        for property in self.value:
            yield property

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        if self.value is None:
            return False

        return key in self.value

    def __getitem__(self, key: int | str) -> Property | None:
        if self.value is None:
            raise ValueError(
                f"Cannot access invalid reference {self.meta.full_path if self.is_default else self.full_path}: {self!s}"
            )

        if isinstance(key, str):
            return self.value[key]
        else:
            raise ValueError(
                f"Trying index access with {key} on the reference attribute {self.meta.full_path if self.is_default else self.full_path}"
            )


class QuestAttribute(ReferenceAttribute):
    """References a quest asset and stores a boolean win_quest."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)
        guid = node.get("Quest")
        self.guid = 0 if guid is None else int(guid)

        if win_quest := node.get("WinQuest"):
            self.win_quest = parse_bool(win_quest)
        else:
            self.win_quest = None


class ListItem:
    def __init__(self, index: int, node: et._Element, parent: ListAttribute | DictAttribute, cache: MetaPropertyCache):
        self.index = index
        self.node = node
        self.parent = parent
        self.cache = cache
        self.super_index = self.get_super_index(self.node)
        self.inherited = self.super_index is not None
        self.value: dict[str, Attribute[ElementCache[t.Any, t.Any], t.Any] | None] = {}
        self._full_path = None
        self._property_path = None

        for value_definition in parent.meta.items:
            name = value_definition.name
            child = node.find(name)

            if child is None:
                attr = value_definition.default
            else:
                attr = AttributeFactory.create(child, self, value_definition, cache)
                if attr.is_compound and not self.inherited:
                    attr.resolve_inheritance(value_definition.default)

            self.value[name] = attr
            setattr(self, name, attr)

    @staticmethod
    def get_super_index(node: et._Element) -> int | None:
        subnode = node.find("VectorElement")
        if subnode is not None:
            subnode = subnode.find("InheritedIndex")

            if subnode is not None and subnode.text is not None:
                return int(subnode.text)

        return None

    def resolve_inheritance(self, default: ListItem):
        for value_definition in self.parent.meta.items:
            name = value_definition.name
            attribute = self.value[name]
            default_attr = default.value[name]

            if default_attr is None:
                continue

            if attribute is None or value_definition.default == attribute:
                setattr(self, name, default_attr)
                self.value[name] = default_attr
            else:
                attribute.resolve_inheritance(default_attr)

    @property
    def full_path(self) -> str:
        if self._full_path is None:
            self._full_path = f"{self.parent.full_path}[{self.index}]"
        return self._full_path

    @property
    def property_path(self) -> str:
        if self._property_path is None:
            self._property_path = f"{self.parent.full_path}[{self.index}]"
        return self._property_path

    def get_tree_note(self, inherited: bool = False) -> str:
        """Returns a note for the tree representation."""
        if self.inherited:
            return "*"

        return ""

    def print_tree(self, indent: str = "", inherited: bool = False):
        print(f"{indent}{self!s} {self.get_tree_note(inherited)}:")
        for attribute in self.value.values():
            if attribute is not None:
                attribute.print_tree(indent + "\t")
        if indent == "":
            print("*) inherited **) default")

    def print_meta_tree(self):
        self.parent.print_meta_tree()

    @property
    def is_compound(self) -> bool:
        return True

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.value

    def __iter__(self) -> t.Iterator[Attribute[ElementCache[t.Any, t.Any], t.Any]]:
        for attribute in self.value.values():
            if attribute is not None:
                yield attribute

    def __getitem__(self, key: int | str) -> str | Attribute[t.Any, t.Any] | None:
        if isinstance(key, str):
            return self.value.get(key)
        else:
            raise ValueError(f"Trying index access with {key} on the reference attribute {self.full_path}")

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"Item ({self.index})"


class ListAttribute(Attribute["MetaPropertyCache", list[ListItem]]):
    """Represents a list. Supports for-each iteration, index access, and checking containment - like regular Python lists. Modifying methods like concatention are not supported."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)

        self.value = []
        self.inherits = False

        for item_node in node.iterchildren():
            if item_node.tag != "Item":
                raise ValueError(
                    f"Invalid list item tag: {item_node.tag} in {self.meta.full_path if self.is_default else self.full_path}"
                )

            item = ListItem(len(self.value), item_node, self, cache)
            if item.super_index is not None:
                self.inherits = True

            self.value.append(item)

        self._value_list = self.value

    def resolve_inheritance(self, default: t.Self | None):
        if not self.inherits or default is None:
            return

        assert self.value is not None

        for item in self.value:
            if item.super_index is not None:
                assert default is not None and default.value is not None

                super_item = None
                if len(default.value) == 0:
                    if isinstance(self.meta.default, ListAttribute):
                        default = self.meta.default  # type: ignore
                    if len(default.value) == 0 and item.super_index == 0:  # type: ignore
                        # Vectors in template that inherit items from DefaultContainerValues
                        super_item = ListItem(
                            0, AttributeFactory.create_default_node("Item", "Vector"), self, self.cache
                        )

                assert default is not None and default.value is not None

                if super_item is None:
                    try:
                        super_item = default.value[item.super_index]
                    except Exception:
                        raise ValueError(
                            f"Invalid inheritance index {item.super_index} for {self.meta.full_path if self.is_default else self.full_path}: {default.meta.full_path if default.is_default else default.full_path}",
                            default,
                        )

                logger.debug(f"[{item.index}] from {super_item.full_path}")
                item.resolve_inheritance(super_item)

    @property
    def is_compound(self) -> bool:
        return True

    def print_tree(self, indent: str = "", inherited: bool = False):
        assert self.value is not None
        print(f"{indent}{self!s} ({len(self.value)} items) {self.get_tree_note(inherited)}:")

        for item in self.value:
            item.print_tree(indent + "\t", item.parent != self)

        if indent == "":
            print("*) inherited **) default")

    def __iter__(self) -> t.Iterator[ListItem]:
        assert self.value is not None
        for attribute in self.value:
            yield attribute

    def __getitem__(self, key: int | str) -> str | ListItem | None:
        """Allows bracket notation access to elements."""
        if self.value is None:
            return None

        if isinstance(key, str):
            raise ValueError(
                f"Trying key access with {key} on list attribute {self.meta.full_path if self.is_default else self.full_path}"
            )
        else:
            if key >= len(self.value):
                raise IndexError(
                    f"Index {key} out of range for {self.meta.full_path if self.is_default else self.full_path}"
                )
            return self.value[key]

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.name}"


class GenericDictAttribute[ValueT: Property | Attribute[t.Any, t.Any]](
    Attribute["MetaPropertyCache", dict[str, ValueT]]
):
    """Parent class for DictAttribute and TemplateAttribute. Provides methods for for-each iteration, key access, and checking containment."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        """Ignore_dataset is used to create child dictionries for each literal of the dataset."""
        super().__init__(node, parent, meta, cache)

        self.value = {}
        self._value_list: list[ValueT] = []
        self.attributes: dict[str, ValueT] = {}
        self.inherits = False

        self.unprocessed_properties = set(child for child in node.iterchildren() if isinstance(child.tag, str))

    def _add_attribute(self, name: str, attribute: ValueT):
        self.unprocessed_properties.discard(attribute.node)  # node is not in all_properties if it is a default node

        if name in self.attributes:
            for idx, child in enumerate(self._value_list):
                if child.name == name:
                    self._value_list[idx] = attribute
                    break

        else:
            self._value_list.append(attribute)

        self.attributes[name] = attribute
        assert self.value is not None
        self.value[name] = attribute

        setattr(self, name, attribute)

    def print_tree(self, indent: str = "", inherited: bool = False):
        print(f"{indent}{self!s} {self.get_tree_note(inherited)}:")

        for item in self._value_list:
            item.print_tree(indent + "\t", item.parent != self)

        if indent == "":
            print("*) inherited **) default")

    @property
    def is_compound(self) -> bool:
        return True

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.attributes

    def __iter__(self) -> t.Iterator[ValueT]:
        for attribute in self._value_list:
            yield attribute

    def __getitem__(self, key: int | str) -> str | ValueT | None:
        """Allows bracket notation access to elements."""
        if self.value is None:
            return None

        if isinstance(key, str):
            return self.value.get(key)
        else:
            if key >= len(self.value):
                raise IndexError(
                    f"Index {key} out of range for {self.meta.full_path if self.is_default else self.full_path}"
                )
            return self._value_list[key]

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.name}"


class DictAttribute(GenericDictAttribute[Attribute[t.Any, t.Any]]):
    """Union for the attributes Array, Struct, and Property."""

    def __init__(
        self,
        node: et._Element,
        parent: AttributeParentT,
        meta: ValueDefinition,
        cache: MetaPropertyCache,
        ignore_dataset: bool = False,
    ):
        """Ignore_dataset is used to create child dictionries for each literal of the dataset."""
        super().__init__(node, parent, meta, cache)

        if meta.dataset is not None and not ignore_dataset:
            # Create a dictionary for each literal in the dataset
            for key in meta.dataset.literals:
                child = node.find(key)
                if child is None:
                    child = AttributeFactory.create_default_node(key, meta.data_type)

                self._add_attribute(key, DictAttribute(child, self, self.meta, self.cache, ignore_dataset=True))

        else:
            for value_definition in meta.items:
                name = value_definition.name
                child = node.find(name)
                self._add_attribute(name, AttributeFactory.create(child, self, value_definition, cache))

        for child in self.unprocessed_properties:
            logger.info(
                f"Ignoring property {child.tag} without meta definition in dictionary {self.meta.full_path if self.is_default else self.full_path}"
            )

    def resolve_inheritance(self, default: t.Self | None, ignore_dataset: bool = False):
        if default is None:
            return

        if self.inherits:
            for item in self._value_list:
                super_index = ListItem.get_super_index(item.node)
                if super_index is not None:
                    try:
                        assert default.value is not None
                        super_item = default._value_list[super_index]
                    except Exception:
                        raise ValueError(
                            f"Invalid inheritance index {super_index} for {self.meta.full_path if self.is_default else self.full_path}"
                        )

                    if super_item.name != item.name:
                        raise ValueError(
                            f"Inherited index resolved to incorrect item: {self.meta.full_path if self.is_default else self.full_path} with index {super_index} resolved to {super_item.full_path}"
                        )

                    logger.debug(f"{item.name} from {super_item.full_path}")
                    item.resolve_inheritance(super_item)
        # TODO: Check inheritance
        elif self.meta.dataset is not None and not ignore_dataset:
            for child in self.attributes.values():
                default_attr = default.attributes.get(child.name)
                if not isinstance(default_attr, DictAttribute) or not isinstance(child, DictAttribute):
                    raise ValueError(
                        f"Missing attribute {child.name} of dataset {self.meta.dataset.name} in {default.full_path} (found when updating inheritance in {self.full_path})"
                    )
                child.resolve_inheritance(default_attr, ignore_dataset=True)
        else:
            for value_definition in self.meta.items:
                name = value_definition.name
                default_attr = default.attributes.get(name)
                if default_attr is None:
                    raise ValueError(
                        f"Missing attribute {name} of type {value_definition.data_type} in {default.full_path} (found when updating inheritance in {self.full_path})"
                    )

                if (attr := self.attributes.get(name)) is None:
                    logger.debug(f"Copy {name} from {default_attr.full_path}")
                    self._add_attribute(name, default_attr)
                else:
                    if attr.is_default:
                        logger.debug(f"Copy {attr.name} from default {default_attr.full_path}")
                        self._add_attribute(name, default_attr)
                    else:
                        logger.debug(f"{attr.name} from {default.full_path}")
                        attr.resolve_inheritance(default_attr)


class TemplateAttribute(GenericDictAttribute["Property"]):
    """Represents an AutoCreateAsset attribute. For those, their building blocks are not defined in meta properties but in templates where they indicate from which template their properties are taken. The instances of the same meta attribute might reference different templates."""

    def __init__(self, node: et._Element, parent: AttributeParentT, meta: ValueDefinition, cache: MetaPropertyCache):
        super().__init__(node, parent, meta, cache)
        self.template_node = node.find("Template")
        self.value_node = node.find("Values")
        self.template_name: str | None = None
        self.template: Template | None = None

        self.unprocessed_properties: set[et._Element] = set()
        if self.value_node is not None:
            self.unprocessed_properties = set(
                child for child in self.value_node.iterchildren() if isinstance(child.tag, str)
            )
            self.process_properties()

        if self.get_value("IsBaseAutoCreateAsset", bool):
            self.inherits = True
            return

        if self.template_node is not None:
            # Template and Values can be inherited
            self.template_name = str(self.template_node.text)

    def process_properties(self):
        if self.value_node is None:
            return

        for child in self.value_node.iterchildren():
            name = str(child.tag)
            if name in self.attributes:
                continue

            meta_property = self.cache.get(name)
            if meta_property is None:
                continue  # Might not have yet been added. MetaPropertyCache.resolve_template_attributes will take care.

            child_property = Property(child, self, meta_property, self.cache)
            self._add_attribute(name, child_property)

    def resolve_inheritance(self, default: t.Self | None):
        if default is None:
            return

        if self.template_name is None:
            self.template_node = default.template_node
            self.template_name = default.template_name

        # self.attributes contains Property as values
        for default_property in default.attributes.values():
            if (prop := self.attributes.get(default_property.name)) is None:
                logger.debug(f"Copy {default_property.name} from {default_property.full_path}")
                prop = default_property
                self._add_attribute(default_property.name, prop)
            else:
                logger.debug(f"{prop.name} from {default_property.full_path}")
                prop.resolve_inheritance(default_property)

    def set_template(self, template: Template):
        """Sets the template for the AutoCreateAsset."""
        self.template = template

        for template_property in template:
            name = template_property.name
            assert self.value_node is not None
            attribute_property = self.attributes.get(name)

            if attribute_property is None:
                attribute_property = template_property
                self._add_attribute(name, attribute_property)
            else:
                attribute_property.resolve_inheritance(template_property)

            self.unprocessed_properties.discard(attribute_property.node)

        if len(self.unprocessed_properties) > 0:
            logger.info(
                f"Setting template {template.name} before all values were processed in {self.meta.full_path if self.is_default else self.full_path} {[child.tag for child in self.unprocessed_properties]}"
            )


class AttributeFactory:
    IGNORED_TYPES = ("AssetGroup", "Matrix", "QuestGroup", "Variable", "TextGroup", "ScriptIdGroup")

    @staticmethod
    def create_default_node(name: str, data_type: str, default_value: str | None = None) -> et._Element:
        """Creates an XML tree with a single node containing the given name and a default value."""
        root = et.Element(name)

        if data_type == "Choice" and default_value is not None:
            root.text = str(default_value)
        if data_type == "String":
            root.text = ""
        elif data_type in PrimitiveAttribute.TYPE_MAP or data_type in "Time":
            root.text = "0"
        elif data_type == "Upgrade":
            child = et.Element("Value")
            child.text = "0"
            root.append(child)
        elif data_type == "AutoCreateAsset":
            child = et.Element("Template")
            root.append(child)
            child = et.Element("Values")
            root.append(child)

        return root

    @staticmethod
    def create(
        node: et._Element | None, parent: AttributeParentT, value_definition: ValueDefinition, cache: MetaPropertyCache
    ) -> Attribute[t.Any, t.Any]:
        if node is None:
            return value_definition.default

        dt = value_definition.data_type
        if dt in AttributeFactory.IGNORED_TYPES:
            return Attribute(node, parent, value_definition, cache)
        if value_definition.is_primitive:  # contains internla strings, for localized strings see TextAttribute
            return PrimitiveAttribute(node, parent, value_definition, cache)

        if dt == "Asset" and value_definition.name == "Text":
            # Handle KeyBindings where text is marked as Asset
            return TextAttribute(node, parent, value_definition, cache)

        match dt:
            case "Color":
                return ColorAttribute(node, parent, value_definition, cache)
            case "Time":
                return TimeAttribute(node, parent, value_definition, cache)
            case "Upgrade":
                return UpgradeAttribute(node, parent, value_definition, cache)
            case "Flags":
                return FlagsAttribute(node, parent, value_definition, cache)
            case "Text":
                return TextAttribute(node, parent, value_definition, cache)
            case "Asset":
                return ReferenceAttribute(node, parent, value_definition, cache)
            case "Quest":
                return QuestAttribute(node, parent, value_definition, cache)
            case "FileName":
                return FileNameAttribute(node, parent, value_definition, cache)
            case "Property" | "Struct" | "Array":
                return DictAttribute(node, parent, value_definition, cache)
            case "Vector":
                return ListAttribute(node, parent, value_definition, cache)
            case "AutoCreateAsset":
                return TemplateAttribute(node, parent, value_definition, cache)
            case _:
                raise ValueError(f"Unprocessed data type: {dt} in {value_definition.full_path}.")
