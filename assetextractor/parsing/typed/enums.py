from enum import Enum


class BuildingType(Enum):
    """
    Define the dataset 'BuildingType' that must contain 8 values.

    This is merely used for intellisense or easier conversion to JSON schemas.
    """

    FACTORY = "Factory"
    RESIDENCE = "Residence"
    OTHER = "Other"
    MINE = "Mine"
    LOGISTIC = "Logistic"
    PUBLIC = "Public"
    BUILDING_MODULE = "BuildingModule"
    WAREHOUSE = "Warehouse"


class Region(Enum):
    """
    Define the dataset 'Region' that must contain 4 values.

    This is merely used for intellisense or easier conversion to JSON schemas.
    """

    META = "Meta"
    ROMAN = "Roman"
    CELTIC = "Celtic"
    EGYPTIAN = "Egyptian"
