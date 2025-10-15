"""CLI tests."""

import types
from typing import Any

from pytest import MonkeyPatch
from typer.testing import CliRunner

from canvas_code_correction import cli


def test_configure_grader_creates_prefect_block(monkeypatch: MonkeyPatch) -> None:
    saved: dict[str, Any] = {}

    class DummyJSON:
        def __init__(self, value: dict[str, Any]):
            self.value = value

        def save(self, name: str, overwrite: bool = False) -> None:
            saved["name"] = name
            saved["value"] = self.value
            saved["overwrite"] = overwrite

    monkeypatch.setattr(cli, "JSON", DummyJSON)

    runner = CliRunner()
    result = runner.invoke(
        cli.app,
        [
            "configure-grader",
            "course-42",
            "--docker-image",
            "ghcr.io/example/course:1.2",
            "--block-name",
            "custom-block",
            "--memory-limit",
            "2g",
            "--cpu-limit",
            "1.5",
            "--network-enabled",
            "--gpu-enabled",
            "--env",
            "FOO=bar",
            "--overwrite",
        ],
    )

    assert result.exit_code == 0
    assert saved["name"] == "custom-block"
    assert saved["value"] == {
        "docker_image": "ghcr.io/example/course:1.2",
        "network_disabled": False,
        "memory_limit": "2g",
        "cpu_limit": 1.5,
        "gpu_enabled": True,
        "env": {"FOO": "bar"},
    }
    assert saved["overwrite"] is True


def test_configure_grader_invalid_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "JSON", types.SimpleNamespace)  # not used due to failure

    runner = CliRunner()
    result = runner.invoke(
        cli.app,
        ["configure-grader", "course", "--docker-image", "img:latest", "--env", "INVALID"],
    )

    assert result.exit_code != 0
