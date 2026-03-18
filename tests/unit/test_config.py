"""Unit tests for configuration module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.bootstrap import load_settings_from_course_block
from canvas_code_correction.config import (
    CanvasSettings,
    Settings,
    WebhookSettings,
    WorkspaceSettings,
)
from canvas_code_correction.prefect_blocks.canvas import CourseConfigBlock


@pytest.fixture
def mock_course_block() -> MagicMock:
    """Return a mock CourseConfigBlock."""
    mock = MagicMock(spec=CourseConfigBlock)
    mock.canvas_api_url = HttpUrl("https://canvas.example.com")
    mock.canvas_token = SecretStr("secret-token")
    mock.canvas_course_id = 123
    mock.asset_bucket_block = "test-bucket"
    mock.asset_path_prefix = "prefix"
    mock.workspace_root = None
    mock.grader_image = "test/image:latest"
    mock.work_pool_name = "test-pool"
    mock.grader_env = {}
    mock.webhook_secret = None
    mock.deployment_name = None
    mock.webhook_enabled = True
    mock.webhook_require_jwt = False
    return mock


@pytest.mark.local
def test_load_settings_from_course_block(mock_course_block: MagicMock) -> None:
    """Test load_settings_from_course_block with a mock block."""
    with patch.object(CourseConfigBlock, "load", return_value=mock_course_block):
        settings = load_settings_from_course_block("dummy-block")
        assert settings.canvas.api_url == mock_course_block.canvas_api_url
        assert settings.canvas.token.get_secret_value() == "secret-token"
        assert settings.canvas.course_id == 123
        assert settings.assets.bucket_block == "test-bucket"
        assert settings.assets.path_prefix == "prefix"
        assert settings.grader.docker_image == "test/image:latest"
        assert settings.grader.work_pool_name == "test-pool"
        assert settings.grader.env == {}
        assert isinstance(settings.workspace.root, Path)
        assert settings.workspace.root == Path("/tmp/ccc/workspaces")  # default
        assert settings.webhook.secret is None
        assert settings.webhook.deployment_name is None
        assert settings.webhook.enabled is True
        assert settings.webhook.require_jwt is False
        assert settings.webhook.rate_limit == "10/minute"


@pytest.mark.local
def test_load_settings_from_course_block_with_workspace_root(mock_course_block: MagicMock) -> None:
    """Test loader with a custom workspace root."""
    mock_course_block.workspace_root = "/custom/workspace"
    with patch.object(CourseConfigBlock, "load", return_value=mock_course_block):
        settings = load_settings_from_course_block("dummy-block")
        assert settings.workspace.root == Path("/custom/workspace").expanduser()


@pytest.mark.local
def test_load_settings_from_course_block_with_webhook_secret(mock_course_block: MagicMock) -> None:
    """Test loader with webhook secret."""
    mock_course_block.webhook_secret = SecretStr("supersecret")
    with patch.object(CourseConfigBlock, "load", return_value=mock_course_block):
        settings = load_settings_from_course_block("dummy-block")
        assert settings.webhook.secret is not None
        assert settings.webhook.secret.get_secret_value() == "supersecret"


@pytest.mark.local
def test_load_settings_from_course_block_returns_settings(mock_course_block: MagicMock) -> None:
    """Test loader returns Settings objects."""
    with patch.object(CourseConfigBlock, "load", return_value=mock_course_block):
        settings = load_settings_from_course_block("dummy-block")
        assert isinstance(settings, Settings)
        assert settings.canvas.course_id == 123


@pytest.mark.local
def test_canvas_settings_validation() -> None:
    """Test CanvasSettings validation."""
    settings = CanvasSettings(
        api_url="https://canvas.example.com",
        token=SecretStr("token"),
        course_id=456,
    )
    assert str(settings.api_url).rstrip("/") == "https://canvas.example.com"
    assert settings.token.get_secret_value() == "token"
    assert settings.course_id == 456


@pytest.mark.local
def test_workspace_settings_default() -> None:
    """Test WorkspaceSettings default root."""
    settings = WorkspaceSettings()
    assert settings.root == Path("/tmp/ccc/workspaces")


@pytest.mark.local
def test_webhook_settings_default() -> None:
    """Test WebhookSettings defaults."""
    settings = WebhookSettings()
    assert settings.secret is None
    assert settings.deployment_name is None
    assert settings.enabled is True
    assert settings.require_jwt is False
    assert settings.rate_limit == "10/minute"
