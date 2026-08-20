from __future__ import annotations

from assetextractor.parsing.typed.buildings import AssetBuildingBase


class AqueductDistributor(AssetBuildingBase, template_names="AqueductDistributor"):
    """
    Specialized Asset for 'AqueductDistributor' with pre-computed data.

    Examples:
        - GUID: 19753 -> Aqueduct Roman Distribution.
    """

    pass


class AqueductProducer(AssetBuildingBase, template_names="AqueductProducer"):
    """
    Specialized Asset for 'AqueductProducer' with pre-computed data.

    Examples:
        - GUID: 19691 -> Aqueduct Roman Basin.
    """

    pass


class AqueductConnector(AssetBuildingBase, template_names="AqueductConnector"):
    """
    Specialized Asset for 'AqueductConnector' with pre-computed data.

    Examples:
        - GUID: 19723 -> Aqueduct Roman Aqueduct MinGround Main.
    """

    pass
