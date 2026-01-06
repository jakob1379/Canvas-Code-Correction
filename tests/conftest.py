from __future__ import annotations

from collections.abc import Generator

import pytest
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="session", autouse=True)
def prefect_testing_environment() -> Generator[None, None, None]:
    with prefect_test_harness():
        yield
