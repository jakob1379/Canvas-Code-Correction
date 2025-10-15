"""Configuration helper tests."""

from canvas_code_correction.config import Settings


def test_settings_from_env_defaults(monkeypatch):
    monkeypatch.setenv("CCC_SKIP_DOTENV", "1")
    monkeypatch.delenv("CANVAS_API_URL", raising=False)
    monkeypatch.delenv("CANVAS_API_TOKEN", raising=False)
    monkeypatch.delenv("CANVAS_COURSE_ID", raising=False)

    settings = Settings.from_env()

    assert settings.canvas.api_url == "https://canvas.instructure.com"
    assert settings.canvas.token == "changeme"
    assert settings.canvas.course_id == 0
