import pytest

from pecan_apispec import reset


@pytest.fixture(autouse=True)
def clean_registry():
    """Each test starts with an empty registry and leaves it empty."""
    reset()
    yield
    reset()
