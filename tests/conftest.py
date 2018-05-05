import pytest


@pytest.fixture
def loop(event_loop):
    return event_loop
