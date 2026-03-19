from collections.abc import Generator

import pytest
from prefect.testing.utilities import prefect_test_harness

pytest_plugins = ["tests.webhooks_shared"]


@pytest.fixture(scope="session")
def prefect_testing_environment() -> Generator[None]:
    with prefect_test_harness():
        yield
