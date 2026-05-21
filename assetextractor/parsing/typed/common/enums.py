"""These are merely used for intellisense or easier conversion to JSON schemas."""

from enum import Enum


class BuildingType(Enum):
    """Define the dataset 'BuildingType' that must contain 8 values."""

    FACTORY = "Factory"
    RESIDENCE = "Residence"
    OTHER = "Other"
    MINE = "Mine"
    LOGISTIC = "Logistic"
    PUBLIC = "Public"
    BUILDING_MODULE = "BuildingModule"
    WAREHOUSE = "Warehouse"


class Region(Enum):
    """Define the dataset 'Region' that must contain 4 values."""

    META = "Meta"
    ROMAN = "Roman"
    CELTIC = "Celtic"
    EGYPTIAN = "Egyptian"


class ScopeVisualization(Enum):
    """Define the dataset 'ScopeVisualization' that must contain 12 values."""

    LOCAL = "Local"
    MODULE_OWNER = "ModuleOwner"
    STREET_DISTANCE = "StreetDistance"
    RADIUS = "Radius"
    OBJECTS_IN_AREA = "ObjectsInArea"
    AREA = "Area"
    OBJECTS_IN_SESSION = "ObjectsInSession"
    SESSION = "Session"
    OBJECTS_IN_META = "ObjectsInMeta"
    META = "Meta"
    AREAS_IN_META = "AreasInMeta"
    AREAS_IN_SESSION = "AreasInSession"


class BuffCategory(Enum):
    """
    Define the dataset 'BuffCategory' that must contain 15 values. This comes
    from 'BuffConfig' asset.
    """

    ADJACENCY = "Adjacency"
    AQUEDUCT = "Aqueduct"
    ASSEMBLY = "Assembly"
    DIPLOMACY = "Diplomacy"
    INCIDENT = "Incident"
    MAJOR_INCIDENT = "MajorIncident"
    INSTITUTION = "Institution"
    ITEM = "Item"
    RELIGION = "Religion"
    TECH = "Tech"

    # TODO: Complete this. I am lazy atm and just needed the "Item".


class ItemAllocation(Enum):
    """
    Define the dataset 'ItemAllocation' that must contain 3 values. This comes
    from 'ItemBalancing' asset.
    """

    NONE = "None"
    SHIP = "Ship"
    VILLA = "Villa"


class RarityVisualization(Enum):
    """
    Define the dataset 'RarityVisualization' that must contain 8 values. This comes
    from 'ItemBalancing' asset.
    """

    NARRATIVE = "Narrative"
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"
    QUEST = "Quest"
    UNIQUE = "Unique"


class NicheVisualization(Enum):
    """
    Define the dataset 'NicheVisualization' that must contain 10 values. This comes
    from 'ItemBalancing' asset.
    """

    NONE = "None"
    FINANCE = "Finance"
    RELIGION = "Religion"
    RESEARCH = "Research"
    CULTURE = "Culture"
    ECONOMY = "Economy"
    AGRICULTURE = "Agriculture"
    DIPLOMACY = "Diplomacy"
    MILITARY = "Military"
    NAUTICS = "Nautics"


class ItemOrigin(Enum):
    """
    Define the dataset 'ItemOrigin' that must contain 5 values. This comes
    from '?' asset.
    """

    BASE_RELEASE = "BaseRelease"  # Vanilla
    DLC_POA = "DLC01"  # Prophecies of Ashes


class SlotType(Enum):
    """
    Define the dataset 'SlotType' that must contain 7 values. This comes
    from '?' asset.
    """

    MOUNTAIN = "Mountain"
    NONE = "None"
    RIVER = "River"
