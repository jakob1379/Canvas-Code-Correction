"""Unit tests for webhook deployment management."""

import asyncio
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

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
    DeploymentEnsureResult,
    TriggerDeploymentResult,
    _serialize_settings_for_flow,
    ensure_deployment,
    get_deployment_name,
    resolve_deployment_target,
    trigger_deployment,
)


@pytest.fixture
def mock_prefect_client() -> Iterator[None]:
    """Mock Prefect client context manager used by deployment operations."""
    async_client = AsyncMock()
    async_client.__aenter__.return_value = AsyncMock(
        read_deployment_by_name=AsyncMock(return_value=None),
    )
    with patch("canvas_code_correction.webhooks.deployments.get_client", return_value=async_client):
        yield


pytestmark = pytest.mark.usefixtures("mock_prefect_client")


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


def test_serialize_settings_for_flow_matches_settings_payload() -> None:
    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test", path_prefix="prefix"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(
            secret=SecretStr("webhook-secret"),
            deployment_name="webhook-deploy",
            rate_limit="42/hour",
        ),
    )

    serialized = _serialize_settings_for_flow(settings)
    assert serialized == settings.to_flow_payload()


def test_resolve_deployment_target_default_pool(mock_settings: Settings) -> None:
    target = resolve_deployment_target(mock_settings, "test-course")
    assert target.name == "ccc-test-course-deployment"
    assert target.work_pool_name == "test-pool"


@patch("canvas_code_correction.webhooks.deployments._get_webhook_correction_flow")
def test_ensure_deployment_success(mock_get_flow: MagicMock) -> None:
    mock_flow = mock_get_flow.return_value
    """Test successful deployment creation."""
    mock_flow.name = "webhook-correction-flow"
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

    result = asyncio.run(ensure_deployment(settings, "test-course"))

    assert result == DeploymentEnsureResult(
        deployment_name="ccc-test-course-deployment",
        work_pool_name="test-pool",
        ensured=True,
        deployment_id="deployment-id-123",
    )
    settings_payload = _serialize_settings_for_flow(settings)
    mock_flow.deploy.assert_called_once_with(
        name="ccc-test-course-deployment",
        work_pool_name="test-pool",
        parameters={
            "course": {
                "course_block": "test-course",
                "settings": settings_payload,
            },
            "download_dir": None,
            "dry_run": False,
        },
        tags=["canvas-webhook", "course:test-course"],
        print_next_steps=False,
        ignore_warnings=True,
    )


@patch("canvas_code_correction.webhooks.deployments._get_webhook_correction_flow")
def test_ensure_deployment_default_work_pool(mock_get_flow: MagicMock) -> None:
    mock_flow = mock_get_flow.return_value
    """Test deployment creation with default work pool."""
    mock_flow.name = "webhook-correction-flow"
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

    result = asyncio.run(ensure_deployment(settings, "test-course"))

    assert result == DeploymentEnsureResult(
        deployment_name="ccc-test-course-deployment",
        work_pool_name="local-pool",
        ensured=True,
        deployment_id="deployment-id-123",
    )
    # Should default to "local-pool"
    settings_payload = _serialize_settings_for_flow(settings)
    mock_flow.deploy.assert_called_once_with(
        name="ccc-test-course-deployment",
        work_pool_name="local-pool",
        parameters={
            "course": {
                "course_block": "test-course",
                "settings": settings_payload,
            },
            "download_dir": None,
            "dry_run": False,
        },
        tags=["canvas-webhook", "course:test-course"],
        print_next_steps=False,
        ignore_warnings=True,
    )


@patch("canvas_code_correction.webhooks.deployments._get_webhook_correction_flow")
def test_ensure_deployment_failure(mock_get_flow: MagicMock) -> None:
    mock_flow = mock_get_flow.return_value
    """Test deployment creation failure (still returns name)."""
    mock_flow.name = "webhook-correction-flow"
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

    result = asyncio.run(ensure_deployment(settings, "test-course"))

    assert result == DeploymentEnsureResult(
        deployment_name="ccc-test-course-deployment",
        work_pool_name="test-pool",
        ensured=False,
        error="Deployment failed",
        error_type="Exception",
    )
    mock_flow.deploy.assert_called_once()


@patch("canvas_code_correction.webhooks.deployments._get_webhook_correction_flow")
def test_ensure_deployment_redeploys_when_existing(mock_get_flow: MagicMock) -> None:
    mock_flow = mock_get_flow.return_value
    mock_flow.name = "webhook-correction-flow"
    mock_flow.deploy.return_value = "deployment-id-456"

    async_client = AsyncMock()
    async_client.__aenter__.return_value = AsyncMock(
        read_deployment_by_name=AsyncMock(return_value=MagicMock(id="existing-deployment")),
    )

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

    with patch("canvas_code_correction.webhooks.deployments.get_client", return_value=async_client):
        result = asyncio.run(ensure_deployment(settings, "test-course"))

    assert result == DeploymentEnsureResult(
        deployment_name="ccc-test-course-deployment",
        work_pool_name="test-pool",
        ensured=True,
        deployment_id="deployment-id-456",
    )
    mock_flow.deploy.assert_called_once()
    async_client.__aenter__.return_value.read_deployment_by_name.assert_awaited_once()


@patch("canvas_code_correction.webhooks.deployments._get_webhook_correction_flow")
def test_ensure_deployment_awaits_async_deploy(mock_get_flow: MagicMock) -> None:
    mock_flow = mock_get_flow.return_value
    mock_flow.name = "webhook-correction-flow"
    mock_flow.deploy = AsyncMock(return_value="deployment-id-async")

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

    result = asyncio.run(ensure_deployment(settings, "test-course"))

    assert result.deployment_id == "deployment-id-async"
    mock_flow.deploy.assert_called_once()
    mock_flow.deploy.assert_awaited_once()


@patch("canvas_code_correction.webhooks.deployments.run_deployment")
@patch("canvas_code_correction.webhooks.deployments._get_webhook_correction_flow")
def test_trigger_deployment_success(
    mock_get_flow: MagicMock,
    mock_run_deployment: MagicMock,
    mock_settings: Settings,
) -> None:
    """Test successful deployment triggering."""
    mock_get_flow.return_value.name = "webhook-correction-flow"
    mock_get_flow.return_value.deploy.return_value = "deployment-id-123"
    mock_run = MagicMock()
    mock_run.id = "flow-run-456"
    mock_run_deployment.return_value = mock_run

    result = asyncio.run(
        trigger_deployment(
            settings=mock_settings,
            course_block="test-course",
            assignment_id=123,
            submission_id=456,
        ),
    )

    assert result == TriggerDeploymentResult(
        deployment_name="ccc-test-course-deployment",
        success=True,
        flow_run_id="flow-run-456",
    )
    mock_get_flow.return_value.deploy.assert_called_once()
    settings_payload = _serialize_settings_for_flow(mock_settings)
    mock_run_deployment.assert_called_once_with(
        name="webhook-correction-flow/ccc-test-course-deployment",
        parameters={
            "course": {
                "course_block": "test-course",
                "settings": settings_payload,
            },
            "submission": {
                "assignment_id": 123,
                "submission_id": 456,
            },
            "download_dir": None,
            "dry_run": False,
        },
        timeout=0,
    )


@patch("canvas_code_correction.webhooks.deployments.run_deployment")
@patch("canvas_code_correction.webhooks.deployments._get_webhook_correction_flow")
def test_trigger_deployment_failure(
    mock_get_flow: MagicMock,
    mock_run_deployment: MagicMock,
    mock_settings: Settings,
) -> None:
    """Test deployment triggering failure."""
    mock_get_flow.return_value.name = "webhook-correction-flow"
    mock_get_flow.return_value.deploy.return_value = "deployment-id-123"
    mock_run_deployment.side_effect = Exception("Run failed")

    result = asyncio.run(
        trigger_deployment(
            settings=mock_settings,
            course_block="test-course",
            assignment_id=123,
            submission_id=456,
        ),
    )

    assert result == TriggerDeploymentResult(
        deployment_name="ccc-test-course-deployment",
        success=False,
        error="Run failed",
        stage="trigger",
        error_type="Exception",
    )
    mock_get_flow.return_value.deploy.assert_called_once()
    mock_run_deployment.assert_called_once()


@patch("canvas_code_correction.webhooks.deployments.run_deployment")
@patch("canvas_code_correction.webhooks.deployments._get_webhook_correction_flow")
def test_trigger_deployment_with_custom_name(
    mock_get_flow: MagicMock,
    mock_run_deployment: MagicMock,
) -> None:
    """Test deployment triggering with custom deployment name."""
    mock_get_flow.return_value.name = "webhook-correction-flow"
    mock_get_flow.return_value.deploy.return_value = "deployment-id-123"
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
            settings=settings,
            course_block="test-course",
            assignment_id=123,
            submission_id=456,
        ),
    )

    assert result == TriggerDeploymentResult(
        deployment_name="custom-deployment",
        success=True,
        flow_run_id="flow-run-456",
    )
    settings_payload = _serialize_settings_for_flow(settings)
    mock_get_flow.return_value.deploy.assert_called_once_with(
        name="custom-deployment",
        work_pool_name="test-pool",
        parameters={
            "course": {
                "course_block": "test-course",
                "settings": settings_payload,
            },
            "download_dir": None,
            "dry_run": False,
        },
        tags=["canvas-webhook", "course:test-course"],
        print_next_steps=False,
        ignore_warnings=True,
    )
    mock_run_deployment.assert_called_once_with(
        name="webhook-correction-flow/custom-deployment",
        parameters={
            "course": {
                "course_block": "test-course",
                "settings": settings_payload,
            },
            "submission": {
                "assignment_id": 123,
                "submission_id": 456,
            },
            "download_dir": None,
            "dry_run": False,
        },
        timeout=0,
    )
