from __future__ import annotations

import re
import typing as t

import lxml.etree as et

if t.TYPE_CHECKING:
    from pathlib import Path


class AttributeMissingError(Exception):
    """Raised when an expected attribute is missing in the properties.xml file."""

    def __init__(self, element: NamedElement[t.Any], attribute: str):
        self.element = element
        self.attribute = attribute
        self.child_index = element.parent.node.index(element.node) if element.parent is not None else None
        super().__init__(
            f"Attribute {attribute} missing in {element.parent.full_path if element.parent is not None else 'No parent'}.child[{self.child_index}]: {[subelement for subelement in element.node]!s}"
        )


class NamedElement[CacheT: "ElementCache[t.Any, t.Any]"]:
    """Base class for all named elements contained in an XML tree, for which we re-create a tree representation here."""

    def __init__(self, node: et._Element, parent: NamedElement[CacheT] | None, cache: CacheT, name: str | None = None):
        self.cache: CacheT = cache
        self.parent = parent
        self.node = node
        self.description: str | None = self.get_value("Description")
        self._property_path = None
        self._full_path = None
        # self.instances: NamedElement = []

        if name is not None:
            self.name = name
        elif name is None:
            name_node = node.find("Name")
            if name_node is None:
                raise AttributeMissingError(self, "Name")

            self.name = str(name_node.text)
        else:
            raise AttributeMissingError(self, "Name")

    @property
    def identifier(self) -> str:
        """Returns the GUID for assets and the name for all other classes."""
        return self.name

    @property
    def safe_identifier(self) -> str:
        safe_identifier = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", self.identifier)
        return safe_identifier

    def get(self, name: str) -> NamedElement[t.Any] | None:
        """Returns the element with the given name or None if it does not exist."""
        if hasattr(self, "__getitem__"):
            try:
                return self[name]  # type: ignore
            except (KeyError, IndexError, TypeError):
                return None
        return None

    @property
    def group(self) -> Group[CacheT] | None:
        """Returns the group of this property."""
        if self.parent is None:
            return None

        if isinstance(self.parent, Group):
            return self.parent

        return self.parent.group

    @property
    def full_path(self) -> str:
        """Returns the path of groups (seperated by '/') and properties (seperated '.').
        The path can be input in another asset to get its corresponding attribute. Note that the path is not identical to the sequence of xml nodes in the original xml file. For technical reasons, the `Values` node in templates and `Item` node of lists are skipped.
        """
        if self._full_path is None:
            if self.parent:
                if isinstance(self.parent, Group):
                    self._full_path = f"{self.parent.full_path}/{self.identifier}"
                else:
                    self._full_path = f"{self.parent.full_path}.{self.identifier}"
            else:
                self._full_path = self.identifier
        return self._full_path

    @property
    def property_path(self) -> str:
        """Returns the path of properties (seperated '.') starting from the group."""
        if self._property_path is None:
            if self.parent is None or isinstance(self.parent, Group):
                self._property_path = self.identifier
            else:
                parent_path = self.parent.property_path
                if parent_path == "":
                    self._property_path = self.identifier
                else:
                    self._property_path = f"{self.parent.property_path}.{self.identifier}"
        return self._property_path

    def get_value[T: str | int | bool | float](self, xml_name: str, dtype: type[T] = str) -> T | None:
        """Returns the value of the element with the given name converted to dtype.

        or None if it does not exist or cannot be parsed.
        """
        element = self.node.find(xml_name)
        if element is not None and element.text is not None:
            try:
                value = dtype(element.text)
            except ValueError:
                value = None
        else:
            value = None
        return value

    def find(self, path: str) -> NamedElement[t.Any] | None:
        """Parses dot seperated list of names to find the element.

        Returns None if the path is not found.
        """
        parts = path.split(".")
        elem = self
        i = 0
        while i < len(parts) and (elem := elem.get(parts[i])) is not None:
            i += 1

        return elem if i == len(parts) else None

    def find_value[T: str](self, path: str, dtype: type[T] = str) -> T | None:
        element = self.find(path)

        if element is not None and element.node.text is not None:
            try:
                value = dtype(element.node.text)
            except ValueError:
                value = None
        else:
            value = None
        return value

    def __contains__(self, key: str) -> bool:
        return False

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        return self.name


class Group[CacheT: "ElementCache[t.Any]"](NamedElement[CacheT]):
    """Represents a group in the properties.xml file."""

    def __init__(self, node: et._Element, parent: NamedElement[CacheT] | None, cache: CacheT, name: str | None = None):
        super().__init__(node, parent, cache, name)
        self.elements: dict[str | int, NamedElement[t.Any]] = {}
        self.subgroups: dict[str | int, Group[t.Any]] = {}

    def get(self, name: str | int) -> NamedElement[t.Any] | None:
        if name in self.elements:
            return self.elements[name]
        if name in self.subgroups:
            return self.subgroups[name]

    def print_tree(self, indent: str = ""):
        print(f"{indent}{self.name}:")

        if len(self.elements) > 0:
            print(f"{indent}\tElements:")
            for element in self.elements.values():
                print(f"{indent}\t\t{element!s}")

        for subgroup in self.subgroups.values():
            subgroup.print_tree(indent + "\t")

    @property
    def is_compound(self) -> bool:
        return True

    def __iter__(self):
        for element in self.elements.values():
            yield element

        for subgroup in self.subgroups.values():
            yield subgroup

    def __getitem__(self, key: str | int) -> NamedElement[t.Any] | None:
        """Allows bracket notation access to elements."""
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.elements or key in self.subgroups

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        return f"Group {self.name} with {len(self.elements)} elements and {len(self.subgroups)} subgroups."


class ElementCache[ElementT: NamedElement[t.Any], GroupT: Group[t.Any] | None = None]:
    """Base class for all caches."""

    def __init__(self, path: Path, key_type: type[str | int] = str):
        self.path = path
        self.key_type = key_type
        self.elements: dict[str | int, ElementT] = {}
        self.groups: dict[str, GroupT] = {}
        self.nodes_to_elements: dict[et._Element, ElementT] = {}

    def add(self, element: ElementT):
        """Adds the element to the cache."""
        if self.key_type is str:
            key = element.name
        else:
            raise RuntimeError("Only string keys are supported.")

        if key in self.elements:
            raise ValueError(f"Element {key} found in {element.full_path} and {self.elements[key].full_path}.")
        self.elements[key] = element

        self.nodes_to_elements[element.node] = element

    def get(self, key: str | int) -> ElementT | None:
        """Returns the element with the given path or None if it does not exist."""
        return self.elements.get(key)

    def find(self, path: str) -> ElementT | None:
        """Prases dot seperated list of names to find the element.

        Returns None if the path is not found.
        """
        parts = path.split(".")
        elem = self.get(parts[0])
        i = 1
        while i < len(parts) and (elem := elem.get(parts[i]) if elem else None):
            i += 1

        return elem if i == len(parts) else None

    def print_tree(self):
        print(str(self))
        for group in self.groups.values():
            if group is not None:
                group.print_tree("\t")

    @property
    def is_compound(self) -> bool:
        return True

    def __iter__(self):
        for element in self.elements.values():
            yield element

    def __getitem__(self, key: str | int) -> ElementT | None:
        """Allows bracket notation access to elements."""
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.elements or key in self.groups

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        return f"Cache with {len(self.elements)} elements and {len(self.groups)} groups."


class Dataset(NamedElement["DatasetCache"]):
    """Represents a dataset in the datasets.xml file."""

    def __init__(self, node: et._Element, parent: DatasetCache):
        super().__init__(node, None, parent)
        id_node = node.find("Id")

        if id_node is None or id_node.text is None:
            self.id = 0
        else:
            self.id = int(id_node.text)
        self.elements: dict[str, int] = {}

        items_node = node.find("Items")
        if items_node is None:
            raise ValueError(f"Dataset {self.name} has no Items.")

        for child in items_node.iterchildren():
            name_node = child.find("Name")

            if name_node is None or name_node.text is None:
                raise ValueError(f"Dataset child item in {self.full_path} has no Name.")

            name = name_node.text
            id_node = child.find("Id")

            id = 0 if id_node is None or id_node.text is None else int(id_node.text)
            self.elements[name] = id

    @property
    def literals(self) -> list[str]:
        return list(self.elements.keys())

    def __getitem__(self, key: str | int) -> int | str | None:
        """Allows bracket notation access to elements."""
        if isinstance(key, str):
            if key not in self.elements:
                raise ValueError(f"Literal {key} does not exist in dataset {self.name}")
            return self.elements[key]
        else:
            for name, id in self.elements.items():
                if id == key:
                    return name
            raise ValueError(f"Id {key} does not exist in dataset {self.name}")

    def __contains__(self, key: str | int) -> bool:
        """Allows the use of the 'in' keyword."""
        return key in self.elements or key in self.elements.values()

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        return f"Dataset {self.name} with {len(self.elements)} values."  # FIXME: self.values didn't exist here, replaced with self.elements


class DatasetCache(ElementCache["Dataset"]):
    def __init__(self, xml_path: Path):
        super().__init__(xml_path)

        self.tree = et.parse(str(self.path))

        for element in self.tree.xpath("//DataSet"):
            dataset = Dataset(element, self)
            self.elements[dataset.name] = dataset
