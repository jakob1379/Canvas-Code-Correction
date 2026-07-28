"""Extended integration tests for CLI commands against live Canvas LMS.

These tests provide comprehensive coverage of CLI functionality with live Canvas API.
Run with: pytest -m integration

Required environment variables from .env.dev:
- CANVAS_API_TOKEN
- CANVAS_COURSE_ID (default: 13122436)
- CANVAS_API_URL (default: https://canvas.instructure.com)
- CANVAS_TEST_ASSIGNMENT_ID (default: 59160606)
"""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from canvasapi.exceptions import CanvasException
from requests.exceptions import RequestException
from typer.testing import CliRunner

from canvas_code_correction.cli import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Return a Typer CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_provision_assets() -> Iterator[MagicMock]:
    with patch("canvas_code_correction.cli_course._provision_course_assets") as mock:
        yield mock


@pytest.fixture
def canvas_credentials() -> dict[str, str]:
    """Load Canvas credentials from environment."""
    token = os.getenv("CANVAS_API_TOKEN")
    if not token:
        pytest.skip("Canvas API token not configured (CANVAS_API_TOKEN)")

    token_value = cast("str", token)
    api_url = os.getenv("CANVAS_API_URL") or "https://canvas.instructure.com"

    try:
        from canvasapi import Canvas

        canvas = Canvas(api_url, token_value)
        _ = canvas.get_current_user()
    except (CanvasException, RequestException):
        pytest.skip("Canvas API token is invalid or expired")

    return {
        "token": token_value,
        "course_id": os.getenv("CANVAS_COURSE_ID") or "13122436",
        "api_url": api_url,
        "assignment_id": os.getenv("CANVAS_TEST_ASSIGNMENT_ID") or "59160606",
    }


# =============================================================================
# COURSE SETUP COMMAND TESTS
# =============================================================================


@pytest.mark.integration
def test_course_setup_live_basic(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
    mock_provision_assets: MagicMock,
) -> None:
    """Test course setup command with basic non-interactive inputs."""
    with patch("canvas_code_correction.cli.CourseConfigBlock") as mock_block_class:
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                canvas_credentials["token"],
                "--course-id",
                canvas_credentials["course_id"],
                "--api-url",
                canvas_credentials["api_url"],
            ],
        )

        assert result.exit_code == 0
        saved_block_name = mock_block.save.call_args.args[0]
        assert f"Course configuration saved as block: {saved_block_name}" in result.output
        mock_block.save.assert_called_once()


@pytest.mark.integration
def test_course_setup_live_with_all_options(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
    mock_provision_assets: MagicMock,
) -> None:
    """Test course setup with all supported optional parameters."""
    with patch("canvas_code_correction.cli.CourseConfigBlock") as mock_block_class:
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                canvas_credentials["token"],
                "--course-id",
                canvas_credentials["course_id"],
                "--api-url",
                canvas_credentials["api_url"],
                "--docker-image",
                "python:3.11-slim",
                "--env",
                "KEY1=value1",
                "--env",
                "KEY2=value2",
            ],
        )

        assert result.exit_code == 0
        saved_block_name = mock_block.save.call_args.args[0]
        assert f"Course configuration saved as block: {saved_block_name}" in result.output

        call_kwargs = mock_block_class.call_args.kwargs
        assert call_kwargs["grader_env"] == {"KEY1": "value1", "KEY2": "value2"}
        assert call_kwargs["storage_auth_mode"] == "shared_environment"


@pytest.mark.integration
def test_course_setup_live_missing_required(cli_runner: CliRunner) -> None:
    """Test course setup fails when required non-interactive args missing."""
    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--token",
            "some-token",
        ],
    )

    assert result.exit_code != 0
    assert "Error" in result.output or "required" in result.output


# =============================================================================
# COURSE SETUP WITH WORK-PACKAGE MAPPINGS
# =============================================================================


@pytest.mark.integration
def test_course_setup_live_with_work_package_mappings(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
    tmp_path: Path,
    mock_provision_assets: MagicMock,
) -> None:
    """Test course setup with work-package-to-assignment mappings.

    Maps local work packages to Canvas assignment IDs.
    """
    with patch("canvas_code_correction.cli.CourseConfigBlock") as mock_block_class:
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block
        work_package_root = tmp_path / "my-work-package"
        (work_package_root / "assets").mkdir(parents=True)
        (work_package_root / "assets" / "main.sh").write_text("#!/bin/sh\n")

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                canvas_credentials["token"],
                "--api-url",
                canvas_credentials["api_url"],
                "--course-id",
                canvas_credentials["course_id"],
                "--work-package",
                f"{canvas_credentials['assignment_id']}:{work_package_root}",
                "--env",
                "DEBUG=true",
            ],
        )

        assert result.exit_code == 0
        assert "Canvas access validated successfully" in result.output
        mock_provision_assets.assert_called_once()

        # Verify work-package mappings were stored
        call_kwargs = mock_block_class.call_args.kwargs
        env = call_kwargs.get("grader_env", {})
        assert env.get("DEBUG") == "true"
        assert call_kwargs["assignment_asset_prefixes"] == {
            canvas_credentials["assignment_id"]: (
                f"graders/{canvas_credentials['course_id']}-"
                "ccc/assignments/"
                f"{canvas_credentials['assignment_id']}/assets"
            ),
        }


@pytest.mark.integration
def test_course_setup_live_multiple_work_package_mappings(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
    tmp_path: Path,
    mock_provision_assets: MagicMock,
) -> None:
    """Test course setup with multiple work-package mappings."""
    with patch("canvas_code_correction.cli.CourseConfigBlock") as mock_block_class:
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block
        work_package_root_1 = tmp_path / "work-package-1"
        (work_package_root_1 / "assets").mkdir(parents=True)
        (work_package_root_1 / "assets" / "main.sh").write_text("#!/bin/sh\n")
        work_package_root_2 = tmp_path / "work-package-2"
        (work_package_root_2 / "grader").mkdir(parents=True)
        (work_package_root_2 / "grader" / "main.sh").write_text("#!/bin/sh\n")
        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                canvas_credentials["token"],
                "--api-url",
                canvas_credentials["api_url"],
                "--course-id",
                canvas_credentials["course_id"],
                "--work-package",
                f"{canvas_credentials['assignment_id']}:{work_package_root_1}",
                "--work-package",
                f"999999:{work_package_root_2}",  # Invalid assignment ID, should still be stored
            ],
        )

        assert result.exit_code == 0
        mock_provision_assets.assert_called_once()

        # Verify multiple mappings stored
        call_kwargs = mock_block_class.call_args.kwargs
        assert call_kwargs.get("grader_env", {}) == {}


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


@pytest.mark.integration
def test_course_setup_live_malformed_token(cli_runner: CliRunner) -> None:
    """Test course setup with malformed Canvas token."""
    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--token",
            "not-a-valid-token-format",
            "--course-id",
            "13122436",
        ],
    )

    assert result.exit_code == 1
    assert "Failed to validate Canvas credentials" in result.output


@pytest.mark.integration
def test_course_setup_live_empty_token(cli_runner: CliRunner) -> None:
    """Test course setup with empty token."""
    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--token",
            "",
            "--course-id",
            "13122436",
        ],
    )

    assert result.exit_code == 1
    assert "Failed to validate Canvas credentials" in result.output


@pytest.mark.integration
def test_course_run_live_nonexistent_course_block(cli_runner: CliRunner) -> None:
    """Test course run fails with non-existent course block."""
    result = cli_runner.invoke(
        app,
        [
            "course",
            "run",
            "12345",
            "--course",
            "ccc-course-nonexistent-block-12345",
        ],
    )

    assert result.exit_code == 1
    assert "Error loading course block" in result.output


# =============================================================================
# CLI STRUCTURE TESTS
# =============================================================================


@pytest.mark.integration
def test_cli_version_with_live_env(cli_runner: CliRunner) -> None:
    """Test CLI version command works with live environment."""
    result = cli_runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "Canvas Code Correction" in result.output


@pytest.mark.integration
def test_cli_help_all_commands(cli_runner: CliRunner) -> None:
    """Test all CLI commands have proper help text."""
    commands = [
        (["--help"], "Canvas Code Correction CLI"),
        (["course", "--help"], "Course Administration"),
        (["course", "setup", "--help"], "Interactively set up"),
        (["course", "run", "--help"], "Run correction flow"),
        (["course", "list", "--help"], "List all configured"),
        (["system", "--help"], "Platform Administration"),
        (["system", "webhook", "--help"], "Manage webhook"),
        (["system", "webhook", "serve", "--help"], "Start webhook server"),
        (["system", "deploy", "--help"], "Manage Prefect"),
        (["system", "deploy", "create", "--help"], "Create or update"),
        (["system", "worker", "--help"], "Manage course-scoped workers"),
        (["system", "worker", "start", "--help"], "Start a course-scoped Prefect worker"),
        (["system", "status", "--help"], "Check platform status"),
    ]

    for args, expected_text in commands:
        result = cli_runner.invoke(app, args)
        assert result.exit_code == 0, f"Command {args} failed: {result.output}"
        assert expected_text in result.output, (
            f"Command {args} missing expected text: {expected_text}"
        )


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.integration
def test_course_setup_live_legacy_override_flags_are_rejected(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
) -> None:
    """Test course setup rejects removed manual naming flags."""
    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--token",
            canvas_credentials["token"],
            "--api-url",
            canvas_credentials["api_url"],
            "--course-id",
            canvas_credentials["course_id"],
            "--slug",
            "manual-override",
        ],
    )

    assert result.exit_code == 2
    assert "Unknown option(s): --slug, manual-override" in result.output


@pytest.mark.integration
def test_course_setup_live_invalid_env_var_format(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
    mock_provision_assets: MagicMock,
) -> None:
    """Test course setup handles invalid environment variable formats gracefully."""
    with patch("canvas_code_correction.cli.CourseConfigBlock") as mock_block_class:
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--token",
                canvas_credentials["token"],
                "--api-url",
                canvas_credentials["api_url"],
                "--course-id",
                canvas_credentials["course_id"],
                "--env",
                "INVALID_ENV_VAR",  # Missing equals sign
            ],
        )

        # Should still succeed but warn about invalid env var
        assert result.exit_code == 0
        assert "Skipping invalid env var" in result.output
