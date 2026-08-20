"""
Package initialization for the buildings sub-module.

This file ensures that all modules within the 'buildings' directory are
correctly discovered and registered during the package initialization phase.
"""

from typing import Union

from .area_buff import *
from .buffs import *
from .building_buff import *
from .defense_building_buff import *
from .ship_buff import *

# Shared type definition for all valid buff template assets.
BuffKey = Union["BuildingBuff", "ShipBuff", "DefenseBuildingBuff", "AreaBuff", "TroopBuff"]
"""TODO: Add the other asset classes into this list (if applies)."""

BUFF_CLASSES = (BuildingBuff, ShipBuff, DefenseBuildingBuff, AreaBuff, TroopBuff)