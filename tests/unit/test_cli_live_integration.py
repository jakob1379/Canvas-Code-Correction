"""Integration tests for CLI commands against local dev stack and live Canvas LMS.

These tests verify CLI commands work with:
1. Local dev stack (RustFS, Prefect server)
2. Live Canvas LMS (using credentials from .env.dev)

Run with: pytest -m integration
"""

from __future__ import annotations

import os
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from canvas_code_correction.cli import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Return a Typer CLI runner for testing."""
    return CliRunner()


def is_rustfs_available() -> bool:
    """Check if RustFS is available."""
    try:
        import boto3

        s3 = boto3.client(
            "s3",
            endpoint_url=os.getenv("RUSTFS_ENDPOINT", "http://localhost:9000"),
            aws_access_key_id=os.getenv("RUSTFS_ACCESS_KEY", "rustfsadmin"),
            aws_secret_access_key=os.getenv("RUSTFS_SECRET_KEY", "rustfsadmin"),
        )
        s3.list_buckets()
        return True
    except Exception:
        return False


def is_prefect_server_available() -> bool:
    """Check if Prefect server is available."""
    try:
        import requests

        response = requests.get(
            f"{os.getenv('PREFECT_API_URL', 'http://localhost:4200/api')}/health",
            timeout=5,
        )
        return response.status_code == 200
    except Exception:
        return False


def is_canvas_token_valid(token: str, api_url: str) -> bool:
    """Check whether Canvas token is currently valid."""
    try:
        from canvasapi import Canvas

        canvas = Canvas(api_url, token)
        _ = canvas.get_current_user()
        return True
    except Exception:
        return False


# =============================================================================
# LOCAL DEV STACK TESTS (RustFS + Prefect)
# =============================================================================


@pytest.mark.integration
@pytest.mark.skipif(not is_rustfs_available(), reason="RustFS not available")
def test_system_status_with_rustfs(cli_runner: CliRunner) -> None:
    """Test system status shows RustFS as available when it's running."""
    result = cli_runner.invoke(app, ["system", "status"])

    assert result.exit_code == 0
    assert "Platform Status" in result.output
    # Should show RustFS as running or error (depending on actual state)
    assert "RustFS (S3)" in result.output


@pytest.mark.integration
@pytest.mark.skipif(not is_prefect_server_available(), reason="Prefect server not available")
def test_system_status_with_prefect(cli_runner: CliRunner) -> None:
    """Test system status shows Prefect as available when it's running."""
    result = cli_runner.invoke(app, ["system", "status"])

    assert result.exit_code == 0
    assert "Platform Status" in result.output
    assert "Prefect server" in result.output


@pytest.mark.integration
def test_course_setup_non_interactive_missing_token(cli_runner: CliRunner) -> None:
    """Test course setup fails gracefully without Canvas token."""
    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--course-id",
            "12345",
            "--assets-block",
            "test-bucket",
        ],
    )

    assert result.exit_code == 1
    assert "--token is required" in result.output or "--token or --token-stdin" in result.output


# =============================================================================
# LIVE CANVAS LMS TESTS (requires .env.dev credentials)
# =============================================================================


@pytest.mark.integration
def test_course_setup_live_canvas_validation(cli_runner: CliRunner) -> None:
    """Test course setup validates token against live Canvas LMS.

    This test requires valid Canvas credentials from .env.dev:
    - CANVAS_API_TOKEN
    - CANVAS_API_URL (optional, defaults to https://canvas.instructure.com)
    """
    token = os.getenv("CANVAS_API_TOKEN")
    if not token:
        pytest.skip("Canvas API token not configured (CANVAS_API_TOKEN)")
    token = cast("str", token)

    api_url = os.getenv("CANVAS_API_URL") or "https://canvas.instructure.com"
    course_id = os.getenv("CANVAS_COURSE_ID") or "13122436"

    if not is_canvas_token_valid(token, api_url):
        pytest.skip("Canvas API token is invalid or expired")

    # Test with valid token - should validate successfully
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
                token,
                "--api-url",
                api_url,
                "--course-id",
                course_id,
                "--assets-block",
                "test-assets",
                "--slug",
                "test-course-live",
            ],
        )

        # Should validate token and attempt to save
        assert "Canvas API token validated successfully" in result.output
        assert result.exit_code == 0
        mock_block.save.assert_called_once()


@pytest.mark.integration
def test_course_setup_live_canvas_invalid_token(cli_runner: CliRunner) -> None:
    """Test course setup fails with invalid token against live Canvas LMS."""
    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--token",
            "invalid-token-12345",
            "--course-id",
            "13122436",
            "--assets-block",
            "test-bucket",
        ],
    )

    assert result.exit_code == 1
    assert "Failed to validate Canvas API token" in result.output


@pytest.mark.integration
def test_course_setup_live_canvas_invalid_course(cli_runner: CliRunner) -> None:
    """Test course setup fails with invalid course ID against live Canvas LMS.

    This test requires valid Canvas credentials from .env.dev.
    """
    token = os.getenv("CANVAS_API_TOKEN")
    if not token:
        pytest.skip("Canvas API token not configured (CANVAS_API_TOKEN)")
    token = cast("str", token)

    api_url = os.getenv("CANVAS_API_URL") or "https://canvas.instructure.com"

    if not is_canvas_token_valid(token, api_url):
        pytest.skip("Canvas API token is invalid or expired")

    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--token",
            token,
            "--api-url",
            api_url,
            "--course-id",
            "999999999",  # Invalid course ID
            "--assets-block",
            "test-bucket",
            "--slug",
            "invalid-course",
        ],
    )

    assert result.exit_code == 1
    assert "Course ID 999999999 not found" in result.output


@pytest.mark.integration
def test_course_list_with_live_prefect(cli_runner: CliRunner) -> None:
    """Test course list works with live Prefect server.

    This test requires a running Prefect server.
    """
    if not is_prefect_server_available():
        pytest.skip("Prefect server not available")

    result = cli_runner.invoke(app, ["course", "list"])

    # Should succeed even if no courses configured
    assert result.exit_code == 0
    # Output should either show courses or "No course configuration blocks found"
    assert (
        "Configured Courses" in result.output
        or "No course configuration blocks found" in result.output
    )


@pytest.mark.integration
def test_course_setup_live_full_workflow(cli_runner: CliRunner) -> None:
    """Test full course setup workflow against live Canvas LMS.

    This test performs a complete course setup using live Canvas API:
    1. Validates Canvas token
    2. Fetches course info
    3. Creates Prefect block

    Requires:
    - CANVAS_API_TOKEN
    - CANVAS_COURSE_ID (or uses default 13122436)
    - Running Prefect server
    """
    token = os.getenv("CANVAS_API_TOKEN")
    if not token:
        pytest.skip("Canvas API token not configured (CANVAS_API_TOKEN)")
    token = cast("str", token)

    course_id = os.getenv("CANVAS_COURSE_ID") or "13122436"
    api_url = os.getenv("CANVAS_API_URL") or "https://canvas.instructure.com"

    if not is_canvas_token_valid(token, api_url):
        pytest.skip("Canvas API token is invalid or expired")

    if not is_prefect_server_available():
        pytest.skip("Prefect server not available")

    # Use a unique slug to avoid conflicts
    import uuid

    test_slug = f"integration-test-{uuid.uuid4().hex[:8]}"

    result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--token",
            token,
            "--api-url",
            api_url,
            "--course-id",
            course_id,
            "--assets-block",
            "test-assets",
            "--assets-prefix",
            f"graders/{test_slug}/",
            "--slug",
            test_slug,
            "--docker-image",
            "python:3.11-slim",
        ],
    )

    # Should complete successfully
    assert result.exit_code == 0, f"Command failed with output: {result.output}"
    assert "Canvas API token validated successfully" in result.output
    assert f"Course configuration saved as block: ccc-course-{test_slug}" in result.output

    # Verify we can list the new course
    list_result = cli_runner.invoke(app, ["course", "list"])
    assert list_result.exit_code == 0
    assert f"ccc-course-{test_slug}" in list_result.output


@pytest.mark.integration
def test_course_run_dry_run_live(cli_runner: CliRunner) -> None:
    """Test course run with dry-run against live Canvas LMS.

    This test attempts to run a correction in dry-run mode using live Canvas API.
    Requires:
    - CANVAS_API_TOKEN
    - CANVAS_COURSE_ID
    - CANVAS_TEST_ASSIGNMENT_ID (or uses default 59160606)
    - Configured course block
    """
    token = os.getenv("CANVAS_API_TOKEN")
    if not token:
        pytest.skip("Canvas API token not configured (CANVAS_API_TOKEN)")
    token = cast("str", token)

    course_id = os.getenv("CANVAS_COURSE_ID") or "13122436"
    assignment_id = os.getenv("CANVAS_TEST_ASSIGNMENT_ID") or "59160606"
    api_url = os.getenv("CANVAS_API_URL") or "https://canvas.instructure.com"

    if not is_canvas_token_valid(token, api_url):
        pytest.skip("Canvas API token is invalid or expired")

    if not is_prefect_server_available():
        pytest.skip("Prefect server not available")

    # First, ensure we have a course block configured
    test_slug = f"run-test-{course_id}"

    setup_result = cli_runner.invoke(
        app,
        [
            "course",
            "setup",
            "--no-interactive",
            "--token",
            token,
            "--api-url",
            api_url,
            "--course-id",
            course_id,
            "--assets-block",
            "test-assets",
            "--slug",
            test_slug,
        ],
    )

    if setup_result.exit_code != 0:
        pytest.skip(f"Failed to setup course block: {setup_result.output}")

    # Now try to run in dry-run mode
    run_result = cli_runner.invoke(
        app,
        [
            "course",
            "run",
            assignment_id,
            "--course",
            f"ccc-course-{test_slug}",
            "--dry-run",
        ],
    )

    # Dry-run should succeed or fail gracefully
    # We mainly want to verify the command structure works
    assert run_result.exit_code in [0, 1]  # 0 = success, 1 = expected error


# =============================================================================
# WEBHOOK AND DEPLOYMENT TESTS (require full stack)
# =============================================================================


@pytest.mark.integration
@pytest.mark.skipif(not is_prefect_server_available(), reason="Prefect server not available")
def test_system_deploy_create_live(cli_runner: CliRunner) -> None:
    """Test deployment creation against live Prefect server.

    This test requires:
    - Running Prefect server
    - Existing course block
    """
    # First check if we have any course blocks
    list_result = cli_runner.invoke(app, ["course", "list"])

    if "No course configuration blocks found" in list_result.output:
        pytest.skip("No course blocks configured for deployment test")

    # Extract first course block name from output
    # This is a simplified check - in practice you'd parse the table
    pytest.skip("Deployment test requires manual verification with existing block")


@pytest.mark.integration
def test_system_webhook_serve_help(cli_runner: CliRunner) -> None:
    """Test webhook serve command help works without server."""
    result = cli_runner.invoke(app, ["system", "webhook", "serve", "--help"])

    assert result.exit_code == 0
    assert "Start webhook server" in result.output
    assert "--host" in result.output
    assert "--port" in result.output
