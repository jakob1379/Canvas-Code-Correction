import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from prefect.testing.utilities import prefect_test_harness

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytest_plugins = ["tests.webhooks_shared"]


@pytest.fixture(scope="session")
def prefect_testing_environment() -> Generator[None]:
    with prefect_test_harness():
        yield
