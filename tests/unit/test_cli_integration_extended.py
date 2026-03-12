"""Extended integration tests for CLI commands against live Canvas LMS.

These tests provide comprehensive coverage of CLI functionality with live Canvas API.
Run with: pytest -m integration

Required environment variables from .env.dev:
- CANVAS_API_TOKEN
- CANVAS_COURSE_ID (default: 13122436)
- CANVAS_API_URL (default: https://canvas.instructure.com)
- CANVAS_TEST_ASSIGNMENT_ID (default: 59160606)
"""

from __future__ import annotations

import os
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
def test_course_setup_live_basic(cli_runner: CliRunner, canvas_credentials: dict[str, str]) -> None:
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
                "--slug",
                "test-setup-basic",
                "--token",
                canvas_credentials["token"],
                "--course-id",
                canvas_credentials["course_id"],
                "--assets-block",
                "test-assets",
                "--api-url",
                canvas_credentials["api_url"],
            ],
        )

        assert result.exit_code == 0
        assert "Course configuration saved as block: ccc-course-test-setup-basic" in result.output
        mock_block.save.assert_called_once()


@pytest.mark.integration
def test_course_setup_live_with_all_options(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
) -> None:
    """Test course setup with all optional parameters."""
    with patch("canvas_code_correction.cli.CourseConfigBlock") as mock_block_class:
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        result = cli_runner.invoke(
            app,
            [
                "course",
                "setup",
                "--no-interactive",
                "--slug",
                "test-setup-full",
                "--token",
                canvas_credentials["token"],
                "--course-id",
                canvas_credentials["course_id"],
                "--assets-block",
                "test-assets",
                "--api-url",
                canvas_credentials["api_url"],
                "--assets-prefix",
                "graders/test/",
                "--docker-image",
                "python:3.11-slim",
                "--work-pool",
                "test-pool",
                "--env",
                "KEY1=value1",
                "--env",
                "KEY2=value2",
            ],
        )

        assert result.exit_code == 0
        assert "Course configuration saved as block: ccc-course-test-setup-full" in result.output

        call_kwargs = mock_block_class.call_args.kwargs
        assert call_kwargs["grader_env"] == {"KEY1": "value1", "KEY2": "value2"}


@pytest.mark.integration
def test_course_setup_live_missing_required(cli_runner: CliRunner) -> None:
    """Test course setup fails when required non-interactive args missing."""
    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--slug",
            "test-missing",
            "--token",
            "some-token",
        ],
    )

    assert result.exit_code != 0
    assert "Error" in result.output or "required" in result.output


# =============================================================================
# COURSE SETUP WITH TEST MAPPINGS
# =============================================================================


@pytest.mark.integration
def test_course_setup_live_with_test_mappings(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
) -> None:
    """Test course setup with test-to-assignment mappings.

    Maps local test files to Canvas assignment IDs.
    """
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
                "--assets-block",
                "test-assets",
                "--slug",
                "test-with-mappings",
                "--test-map",
                f"{canvas_credentials['assignment_id']}:/tests/test_assignment.py",
                "--env",
                "DEBUG=true",
            ],
        )

        assert result.exit_code == 0
        assert "Canvas API token validated successfully" in result.output

        # Verify test mappings were stored
        call_kwargs = mock_block_class.call_args.kwargs
        env = call_kwargs.get("grader_env", {})
        assert f"CCC_TEST_MAP_{canvas_credentials['assignment_id']}" in env
        assert (
            env[f"CCC_TEST_MAP_{canvas_credentials['assignment_id']}"]
            == "/tests/test_assignment.py"
        )
        assert env.get("DEBUG") == "true"


@pytest.mark.integration
def test_course_setup_live_multiple_test_mappings(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
) -> None:
    """Test course setup with multiple test mappings."""
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
                "--assets-block",
                "test-assets",
                "--slug",
                "test-multi-mappings",
                "--test-map",
                f"{canvas_credentials['assignment_id']}:/tests/test1.py",
                "--test-map",
                "999999:/tests/test2.py",  # Invalid assignment ID, should still be stored
            ],
        )

        assert result.exit_code == 0

        # Verify multiple mappings stored
        call_kwargs = mock_block_class.call_args.kwargs
        env = call_kwargs.get("grader_env", {})
        assert f"CCC_TEST_MAP_{canvas_credentials['assignment_id']}" in env
        assert "CCC_TEST_MAP_999999" in env


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
            "--assets-block",
            "test-assets",
        ],
    )

    assert result.exit_code == 1
    assert "Failed to validate Canvas API token" in result.output


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
            "--assets-block",
            "test-assets",
        ],
    )

    assert result.exit_code == 1
    assert "Failed to validate Canvas API token" in result.output


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
def test_course_setup_live_special_chars_in_slug(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
) -> None:
    """Test course setup handles special characters in slug."""
    with patch("canvas_code_correction.cli.CourseConfigBlock") as mock_block_class:
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        # Use slug with hyphens and numbers
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
                "--assets-block",
                "test-assets",
                "--slug",
                "cs-101-fall-2024",
            ],
        )

        assert result.exit_code == 0
        assert "ccc-course-cs-101-fall-2024" in result.output


@pytest.mark.integration
def test_course_setup_live_long_slug(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
) -> None:
    """Test course setup handles long slugs."""
    with patch("canvas_code_correction.cli.CourseConfigBlock") as mock_block_class:
        mock_block = MagicMock()
        mock_block_class.return_value = mock_block

        long_slug = "a" * 50  # 50 character slug

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
                "--assets-block",
                "test-assets",
                "--slug",
                long_slug,
            ],
        )

        assert result.exit_code == 0
        assert f"ccc-course-{long_slug}" in result.output


@pytest.mark.integration
def test_course_setup_live_invalid_env_var_format(
    cli_runner: CliRunner,
    canvas_credentials: dict[str, str],
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
                "--assets-block",
                "test-assets",
                "--slug",
                "test-invalid-env",
                "--env",
                "INVALID_ENV_VAR",  # Missing equals sign
            ],
        )

        # Should still succeed but warn about invalid env var
        assert result.exit_code == 0
        assert "Skipping invalid env var" in result.output
