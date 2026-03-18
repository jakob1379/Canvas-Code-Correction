from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.bootstrap import (
    CourseBlockLoadError,
    find_course_block_names,
    load_course_block,
    load_settings_from_course_block,
)
from canvas_code_correction.prefect_blocks.canvas import CourseConfigBlock


def _make_block() -> MagicMock:
    block = MagicMock(spec=CourseConfigBlock)
    block.canvas_api_url = HttpUrl("https://canvas.example.com")
    block.canvas_token = SecretStr("secret-token")
    block.canvas_course_id = 123
    block.asset_bucket_block = "test-bucket"
    block.asset_path_prefix = "prefix"
    block.workspace_root = None
    block.grader_image = "grader:latest"
    block.work_pool_name = "test-pool"
    block.grader_env = {"ENV": "value"}
    block.grader_command = ["bash", "run.sh"]
    block.grader_timeout_seconds = 450
    block.grader_memory_mb = 1024
    block.grader_upload_check_duplicates = False
    block.grader_upload_comments = False
    block.grader_upload_grades = False
    block.grader_upload_verbose = True
    block.webhook_secret = None
    block.deployment_name = None
    block.webhook_enabled = True
    block.webhook_require_jwt = False
    block.webhook_rate_limit = "10/minute"
    return block


def test_load_settings_from_course_block_maps_block_fields() -> None:
    block = _make_block()
    expected_root = Path("/tmp/ccc/workspaces")

    with (
        patch(
            "canvas_code_correction.bootstrap._default_workspace_root",
            return_value=expected_root,
        ),
        patch.object(CourseConfigBlock, "load", return_value=block),
    ):
        settings = load_settings_from_course_block("test-course")

    assert settings.canvas.course_id == 123
    assert str(settings.canvas.api_url).rstrip("/") == "https://canvas.example.com"
    assert settings.canvas.token.get_secret_value() == "secret-token"
    assert settings.assets.bucket_block == "test-bucket"
    assert settings.assets.path_prefix == "prefix"
    assert settings.grader.docker_image == "grader:latest"
    assert settings.grader.work_pool_name == "test-pool"
    assert settings.grader.env == {"ENV": "value"}
    assert settings.grader.command == ["bash", "run.sh"]
    assert settings.grader.timeout_seconds == 450
    assert settings.grader.memory_mb == 1024
    assert settings.grader.upload_check_duplicates is False
    assert settings.grader.upload_comments is False
    assert settings.grader.upload_grades is False
    assert settings.grader.upload_verbose is True
    assert settings.webhook.rate_limit == "10/minute"
    assert settings.workspace.root == expected_root


def test_load_settings_from_course_block_expands_workspace_root() -> None:
    block = _make_block()
    block.workspace_root = "~/ccc-workspaces"
    block.webhook_secret = SecretStr("webhook-secret")

    with patch.object(CourseConfigBlock, "load", return_value=block):
        settings = load_settings_from_course_block("test-course")

    assert settings.workspace.root == Path("~/ccc-workspaces").expanduser()
    assert settings.webhook.secret is not None
    assert settings.webhook.secret.get_secret_value() == "webhook-secret"


def test_load_settings_from_course_block_round_trips_webhook_rate_limit() -> None:
    block = _make_block()
    block.webhook_rate_limit = "42/hour"

    with patch.object(CourseConfigBlock, "load", return_value=block):
        settings = load_settings_from_course_block("test-course")

    assert settings.webhook.rate_limit == "42/hour"


def test_load_course_block_surface_error() -> None:
    error = RuntimeError("boom")

    with patch.object(CourseConfigBlock, "load", side_effect=error):
        with pytest.raises(CourseBlockLoadError) as excinfo:
            load_course_block("test-course")

    assert "test-course" in str(excinfo.value)
    assert excinfo.value.reason == str(error)
    assert isinstance(excinfo.value.cause, Exception)
    assert excinfo.value.cause is error


def test_find_course_block_names_returns_strings() -> None:
    names = ["course-one", Path("course-two")]

    with patch.object(CourseConfigBlock, "find", return_value=names, create=True):
        assert find_course_block_names() == ["course-one", "course-two"]
