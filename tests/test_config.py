# bandit: disable=B101,B105,B106
"""Configuration helper tests."""

from canvas_code_correction.config import Settings


def test_settings_from_env_defaults(monkeypatch):
    monkeypatch.setenv("CCC_SKIP_DOTENV", "1")
    monkeypatch.delenv("CANVAS_API_URL", raising=False)
    monkeypatch.delenv("CANVAS_URL", raising=False)
    monkeypatch.delenv("CANVAS_API_TOKEN", raising=False)
    monkeypatch.delenv("CANVAS_TOKEN", raising=False)
    monkeypatch.delenv("CANVAS_TOKE", raising=False)
    monkeypatch.delenv("CANVAS_COURSE_ID", raising=False)

    settings = Settings.from_env()

    assert settings.canvas.api_url == "https://canvas.example"  # nosec B101
    assert settings.canvas.token == "changeme"  # nosec B101,B105
    assert settings.canvas.course_id == 0  # nosec B101
