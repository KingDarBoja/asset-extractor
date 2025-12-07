"""Pytest configuration and shared fixtures for integration tests."""

import pytest

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


@pytest.fixture(scope="session")
def config():
    """Load the configuration once for the entire test session."""
    return Config.from_json("config.json")


@pytest.fixture(scope="session")
def assets(config):
    """Load the asset cache once for the entire test session.

    This is an expensive operation, so we cache it at session scope.
    All tests will share the same AssetCache instance.
    """
    return AssetCache.load(config)


@pytest.fixture(scope="session")
def ui_text_cache(assets):
    """Provide access to the UI text cache."""
    return assets.properties.ui_text_cache


@pytest.fixture(scope="session")
def texts(assets):
    """Provide access to the text cache."""
    return assets.texts


def get_english_text(text_obj):
    """Helper function to extract English text from a Text object or string.

    Parameters
    ----------
    text_obj : Text | str | None
        The text object to extract from

    Returns
    -------
    str | None
        English text if available, None otherwise
    """
    if text_obj is None:
        return None
    if hasattr(text_obj, "values"):
        return text_obj.values.get("english", "N/A")
    if isinstance(text_obj, str):
        return text_obj
    return str(text_obj)


# Make helper function available to all tests
pytest.get_english_text = get_english_text
