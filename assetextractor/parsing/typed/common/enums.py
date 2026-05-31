"""These are merely used for intellisense or easier conversion to JSON schemas."""

from enum import Enum


class BuildingType(str, Enum):
    """Define the dataset 'BuildingType' that must contain 8 values."""

    FACTORY = "Factory"
    RESIDENCE = "Residence"
    OTHER = "Other"
    MINE = "Mine"
    LOGISTIC = "Logistic"
    PUBLIC = "Public"
    BUILDING_MODULE = "BuildingModule"
    WAREHOUSE = "Warehouse"


class Region(str, Enum):
    """Define the dataset 'Region' that must contain 4 values."""

    META = "Meta"
    ROMAN = "Roman"
    CELTIC = "Celtic"
    EGYPTIAN = "Egyptian"


class ScopeVisualization(str, Enum):
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


class BuffCategory(str, Enum):
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


class ItemAllocation(str, Enum):
    """
    Define the dataset 'ItemAllocation' that must contain 3 values. This comes
    from 'ItemBalancing' asset.
    """

    NONE = "None"
    SHIP = "Ship"
    VILLA = "Villa"


class RarityVisualization(str, Enum):
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


class NicheVisualization(str, Enum):
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


class ItemOrigin(str, Enum):
    """
    Define the dataset 'ItemOrigin' that must contain 5 values. This comes
    from '?' asset.
    """

    TESTING = "Testing"
    BASE_RELEASE = "BaseRelease"  # Vanilla
    PREORDER = "PreOrder"  # Mostly for ornaments and logos.
    TWITCH_DROP = "TwitchDrop"  # Mostly ornaments and logos.
    DLC_POA = "DLC01"  # Prophecies of Ashes
    DLC_HIPO = "DLC02"  # Assuming this is gonna be for Hippodrome.
    DLC_EGYPT = "DLC03"  # Assuming this is gonna be for Dawn of the Delta.


class SlotType(str, Enum):
    """
    Define the dataset 'SlotType' that must contain 7 values. This comes
    from '?' asset.
    """

    NONE = "None"
    COAST = "Coast"
    RIVER = "River"
    CLAIMING = "ClaimingBuilding"
    MOUNTAIN = "Mountain"
    WORKAREA = "WorkArea"
    MARSH = "Marsh"


class UplayProductType(str, Enum):
    """
    Define the dataset 'UplayProductType' that must contain 6 values. This comes
    from '?' asset.
    """

    SEASON_PASS = "SeasonPass"
    DLC = "DLC"
    COSMETIC_DLC = "CosmeticDLC"
    PREORDER_BONUS = "PreOrderBonus"
    TWITCH_DROP = "TwitchDrop"
    LANGUAGE_PACK = "LanguagePack"
