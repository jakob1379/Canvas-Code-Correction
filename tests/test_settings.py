# bandit: disable=B101,B105,B106
"""Settings model tests."""

import os
from pathlib import Path

from pytest import MonkeyPatch

from canvas_code_correction.config import Settings


def test_settings_from_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CCC_SKIP_DOTENV", "1")
    monkeypatch.delenv("CANVAS_API_TOKEN", raising=False)
    monkeypatch.setenv("CANVAS_API_URL", "https://canvas.test")
    monkeypatch.setenv("CANVAS_API_TOKEN", "token-value")
    monkeypatch.setenv("CANVAS_COURSE_ID", "42")

    settings = Settings.from_env()

    assert settings.canvas.api_url == "https://canvas.test"  # nosec B101
    assert settings.canvas.token == "token-value"  # nosec B101,B105
    assert settings.canvas.course_id == 42  # nosec B101


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

    assert settings.canvas.api_url == "https://canvas.file"  # nosec B101
    assert settings.canvas.token == "file-token"  # nosec B101,B105
    assert settings.canvas.course_id == 21  # nosec B101

    if original is not None:
        os.environ["CCC_SKIP_DOTENV"] = original
