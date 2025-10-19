"""Settings model tests."""

import os
from pathlib import Path

from pytest import MonkeyPatch, approx

from canvas_code_correction.config import Settings


def test_settings_from_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CCC_SKIP_DOTENV", "1")
    monkeypatch.delenv("CANVAS_API_TOKEN", raising=False)
    monkeypatch.setenv("CANVAS_API_URL", "https://canvas.test")
    monkeypatch.setenv("CANVAS_API_TOKEN", "token-value")
    monkeypatch.setenv("CANVAS_COURSE_ID", "42")

    settings = Settings.from_env()

    assert settings.canvas.api_url == "https://canvas.test"
    assert settings.canvas.token == "token-value"
    assert settings.canvas.course_id == 42
    assert settings.runner.gpu_enabled is False


def test_settings_from_env_file(tmp_path: Path) -> None:
    original = os.environ.get("CCC_SKIP_DOTENV")
    if original is not None:
        os.environ.pop("CCC_SKIP_DOTENV")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "CANVAS_API_URL=https://canvas.file",
                "CANVAS_API_TOKEN=file-token",
                "CANVAS_COURSE_ID=21",
            ]
        )
    )

    settings = Settings.from_file(env_file)

    assert settings.canvas.api_url == "https://canvas.file"
    assert settings.canvas.token == "file-token"
    assert settings.canvas.course_id == 21

    if original is not None:
        os.environ["CCC_SKIP_DOTENV"] = original


def test_settings_runner_block(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CCC_SKIP_DOTENV", "1")
    monkeypatch.setenv("CANVAS_API_URL", "https://canvas.block")
    monkeypatch.setenv("CANVAS_API_TOKEN", "token")
    monkeypatch.setenv("CANVAS_COURSE_ID", "7")
    monkeypatch.setenv("CCC_RUNNER_BLOCK", "grader-config/course-a")

    def fake_load(block_name: str):  # type: ignore[override]
        assert block_name == "grader-config/course-a"
        return {
            "docker_image": "ghcr.io/example/course-a:latest",
            "network_disabled": False,
            "memory_limit": "2g",
            "cpu_limit": 2.5,
            "env": {"EXTRA": "value"},
            "gpu_enabled": True,
        }

    monkeypatch.setattr(Settings, "_load_runner_block", staticmethod(fake_load))

    settings = Settings.from_env()

    assert settings.runner.docker_image == "ghcr.io/example/course-a:latest"
    assert settings.runner.network_disabled is False
    assert settings.runner.memory_limit == "2g"
    assert settings.runner.cpu_limit == approx(2.5)
    assert settings.runner.env == {"EXTRA": "value"}
    assert settings.runner.config_block == "grader-config/course-a"
    assert settings.runner.gpu_enabled is True


def test_settings_runner_env_override(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CCC_SKIP_DOTENV", "1")
    monkeypatch.setenv("CANVAS_API_URL", "https://canvas.override")
    monkeypatch.setenv("CANVAS_API_TOKEN", "token")
    monkeypatch.setenv("CANVAS_COURSE_ID", "8")
    monkeypatch.setenv("CCC_RUNNER_BLOCK", "grader-config/course-b")
    monkeypatch.setenv("CCC_RUNNER_IMAGE", "ghcr.io/example/override:1.0")
    monkeypatch.setenv("CCC_RUNNER_CPU_LIMIT", "3.0")
    monkeypatch.setenv("CCC_RUNNER_MEMORY_LIMIT", "3g")
    monkeypatch.setenv("CCC_RUNNER_NETWORK_DISABLED", "0")
    monkeypatch.setenv("CCC_RUNNER_GPU_ENABLED", "1")

    def fake_load(block_name: str):  # type: ignore[override]
        assert block_name == "grader-config/course-b"
        return {
            "docker_image": "ghcr.io/example/course-b:latest",
            "network_disabled": True,
            "memory_limit": "1g",
            "cpu_limit": 1.0,
            "gpu_enabled": False,
        }

    monkeypatch.setattr(Settings, "_load_runner_block", staticmethod(fake_load))

    settings = Settings.from_env()

    assert settings.runner.docker_image == "ghcr.io/example/override:1.0"
    assert settings.runner.cpu_limit == approx(3.0)
    assert settings.runner.memory_limit == "3g"
    assert settings.runner.network_disabled is False
    assert settings.runner.gpu_enabled is True


def test_settings_working_dir_override(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CCC_SKIP_DOTENV", "1")
    monkeypatch.setenv("CANVAS_API_URL", "https://canvas.dir")
    monkeypatch.setenv("CANVAS_API_TOKEN", "token")
    monkeypatch.setenv("CANVAS_COURSE_ID", "9")
    monkeypatch.setenv("CCC_WORKING_DIR", str(tmp_path))

    settings = Settings.from_env()

    assert settings.working_dir == tmp_path
