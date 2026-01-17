"""Unit tests for webhook deployment management."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WebhookSettings,
    WorkspaceSettings,
)
from canvas_code_correction.webhooks.deployments import (
    ensure_deployment,
    get_deployment_name,
    trigger_deployment,
)


@pytest.fixture
def mock_settings() -> Settings:
    """Mock settings for testing."""
    return Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake-token"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test-bucket"),
        grader=GraderSettings(work_pool_name="test-pool"),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(
            enabled=True,
            require_jwt=False,
            secret=None,
            deployment_name=None,
            rate_limit="10/minute",
        ),
    )


def test_get_deployment_name_default() -> None:
    """Test default deployment name generation."""
    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(),
    )

    # Default naming
    name = get_deployment_name(settings, "test-course")
    assert name == "ccc-test-course-deployment"

    # With ccc-course- prefix
    name = get_deployment_name(settings, "ccc-course-math101")
    assert name == "ccc-math101-deployment"


def test_get_deployment_name_custom() -> None:
    """Test custom deployment name from settings."""
    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(deployment_name="custom-deployment-name"),
    )

    name = get_deployment_name(settings, "test-course")
    assert name == "custom-deployment-name"


@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
def test_ensure_deployment_success(mock_flow: MagicMock) -> None:
    """Test successful deployment creation."""
    mock_flow.deploy.return_value = "deployment-id-123"

    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(work_pool_name="test-pool"),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(),
    )

    deployment_name = asyncio.run(ensure_deployment("test-course", settings))

    assert deployment_name == "ccc-test-course-deployment"
    mock_flow.deploy.assert_called_once_with(
        name="ccc-test-course-deployment",
        work_pool_name="test-pool",
        parameters={
            "course_block": "test-course",
            "download_dir": None,
            "dry_run": False,
        },
        tags=["canvas-webhook", "course:test-course"],
        print_next_steps=False,
        ignore_warnings=True,
    )


@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
def test_ensure_deployment_default_work_pool(mock_flow: MagicMock) -> None:
    """Test deployment creation with default work pool."""
    mock_flow.deploy.return_value = "deployment-id-123"

    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(work_pool_name=None),  # No work pool specified
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(),
    )

    deployment_name = asyncio.run(ensure_deployment("test-course", settings))

    assert deployment_name == "ccc-test-course-deployment"
    # Should default to "local-pool"
    mock_flow.deploy.assert_called_once_with(
        name="ccc-test-course-deployment",
        work_pool_name="local-pool",
        parameters={
            "course_block": "test-course",
            "download_dir": None,
            "dry_run": False,
        },
        tags=["canvas-webhook", "course:test-course"],
        print_next_steps=False,
        ignore_warnings=True,
    )


@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
def test_ensure_deployment_failure(mock_flow: MagicMock) -> None:
    """Test deployment creation failure (still returns name)."""
    mock_flow.deploy.side_effect = Exception("Deployment failed")

    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(work_pool_name="test-pool"),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(),
    )

    # Should still return the deployment name even if creation fails
    deployment_name = asyncio.run(ensure_deployment("test-course", settings))

    assert deployment_name == "ccc-test-course-deployment"
    mock_flow.deploy.assert_called_once()


@patch("canvas_code_correction.webhooks.deployments.run_deployment")
@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
def test_trigger_deployment_success(
    mock_flow: MagicMock,
    mock_run_deployment: MagicMock,
    mock_settings: Settings,
) -> None:
    """Test successful deployment triggering."""
    mock_flow.deploy.return_value = "deployment-id-123"
    mock_run = MagicMock()
    mock_run.id = "flow-run-456"
    mock_run_deployment.return_value = mock_run

    result = asyncio.run(
        trigger_deployment(
            course_block="test-course",
            assignment_id=123,
            submission_id=456,
            settings=mock_settings,
        ),
    )

    assert result == "flow-run-456"
    mock_flow.deploy.assert_called_once()
    mock_run_deployment.assert_called_once_with(
        name="ccc-test-course-deployment",
        parameters={
            "assignment_id": 123,
            "submission_id": 456,
            "download_dir": None,
            "dry_run": False,
        },
        timeout=0,
    )


@patch("canvas_code_correction.webhooks.deployments.run_deployment")
@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
def test_trigger_deployment_failure(
    mock_flow: MagicMock,
    mock_run_deployment: MagicMock,
    mock_settings: Settings,
) -> None:
    """Test deployment triggering failure."""
    mock_flow.deploy.return_value = "deployment-id-123"
    mock_run_deployment.side_effect = Exception("Run failed")

    result = asyncio.run(
        trigger_deployment(
            course_block="test-course",
            assignment_id=123,
            submission_id=456,
            settings=mock_settings,
        ),
    )

    assert result is None
    mock_flow.deploy.assert_called_once()
    mock_run_deployment.assert_called_once()


@patch("canvas_code_correction.webhooks.deployments.run_deployment")
@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
def test_trigger_deployment_with_custom_name(
    mock_flow: MagicMock,
    mock_run_deployment: MagicMock,
) -> None:
    """Test deployment triggering with custom deployment name."""
    mock_flow.deploy.return_value = "deployment-id-123"
    mock_run = MagicMock()
    mock_run.id = "flow-run-456"
    mock_run_deployment.return_value = mock_run

    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(work_pool_name="test-pool"),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(deployment_name="custom-deployment"),
    )

    result = asyncio.run(
        trigger_deployment(
            course_block="test-course",
            assignment_id=123,
            submission_id=456,
            settings=settings,
        ),
    )

    assert result == "flow-run-456"
    mock_flow.deploy.assert_called_once_with(
        name="custom-deployment",
        work_pool_name="test-pool",
        parameters={
            "course_block": "test-course",
            "download_dir": None,
            "dry_run": False,
        },
        tags=["canvas-webhook", "course:test-course"],
        print_next_steps=False,
        ignore_warnings=True,
    )
    mock_run_deployment.assert_called_once_with(
        name="custom-deployment",
        parameters={
            "assignment_id": 123,
            "submission_id": 456,
            "download_dir": None,
            "dry_run": False,
        },
        timeout=0,
    )
