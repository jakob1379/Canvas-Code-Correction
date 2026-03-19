"""Integration tests for Canvas webhook signals with mocked Canvas API."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WebhookSettings,
    WorkspaceSettings,
)
from canvas_code_correction.webhooks.server import app


@pytest.fixture
def mock_settings() -> Settings:
    """Mock settings for webhook testing."""
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


@pytest.fixture
def client() -> TestClient:
    """Test client for FastAPI app."""
    return TestClient(app)


def create_canvas_webhook_payload(
    event_name: str = "submission_created",
    assignment_id: str = "123",
    submission_id: str = "456",
) -> dict:
    """Create a simulated Canvas webhook payload."""
    return {
        "metadata": {
            "event_name": event_name,
            "event_time": datetime.now(UTC).isoformat(),
            "producer": "canvas",
        },
        "body": {
            "assignment_id": assignment_id,
            "submission_id": submission_id,
            "submission_type": "online_text_entry",
            "submitted_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "user_id": "789",
            "workflow_state": "submitted",
        },
    }


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
@patch("canvas_code_correction.webhooks.deployments.run_deployment")
def test_webhook_jwt_authentication(
    mock_run_deployment: Mock,
    mock_flow: AsyncMock,
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with JWT authentication enabled."""
    # Modify settings to require JWT with secret
    mock_settings.webhook.require_jwt = True
    mock_settings.webhook.secret = SecretStr("jwt-secret")
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True
    mock_flow.deploy.return_value = "deployment-id-123"
    mock_run = Mock()
    mock_run.id = "flow-run-456"
    mock_run_deployment.return_value = mock_run

    payload = create_canvas_webhook_payload()

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer valid-jwt-token"},
    )
    if response.status_code != 200:
        print(f"Response error: {response.status_code} {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["flow_run_id"] == "flow-run-456"
    assert data["course_block"] == "test-course"
    assert data["assignment_id"] == 123
    assert data["submission_id"] == 456
    mock_verify.assert_called_once()


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
@patch("canvas_code_correction.webhooks.deployments.run_deployment")
def test_webhook_submission_updated_event(
    mock_run_deployment: Mock,
    mock_flow: AsyncMock,
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with submission_updated event."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True
    mock_flow.deploy.return_value = "deployment-id-123"
    mock_run = Mock()
    mock_run.id = "flow-run-456"
    mock_run_deployment.return_value = mock_run

    payload = create_canvas_webhook_payload(event_name="submission_updated")

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["flow_run_id"] == "flow-run-456"
    assert data["course_block"] == "test-course"
    assert data["assignment_id"] == 123
    assert data["submission_id"] == 456


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
@patch("canvas_code_correction.webhooks.deployments.run_deployment")
def test_webhook_unsupported_event_type(
    mock_run_deployment: Mock,
    mock_flow: AsyncMock,
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with unsupported event type."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True

    payload = create_canvas_webhook_payload(event_name="assignment_created")
    # Override metadata event_name
    payload["metadata"]["event_name"] = "assignment_created"

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    # Should return 200 with success=False
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Unsupported event type" in data["message"]
    # Verify deployment was not created or run
    mock_flow.deploy.assert_not_called()
    mock_run_deployment.assert_not_called()


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_missing_assignment_id(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with missing assignment_id in payload."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True

    payload = create_canvas_webhook_payload()
    del payload["body"]["assignment_id"]

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    # Should return 200 with success=False
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Failed to parse submission event" in data["message"]


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_invalid_ids_non_numeric(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with non-numeric assignment/submission IDs."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True

    payload = create_canvas_webhook_payload(assignment_id="not-a-number", submission_id="also-not")

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Invalid ID format" in data["message"]


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_missing_authorization_header_jwt_required(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling when JWT required but Authorization header missing."""
    mock_settings.webhook.require_jwt = True
    mock_settings.webhook.secret = SecretStr("secret")
    mock_resolve_settings.return_value = mock_settings
    # verify_canvas_webhook will return False because missing header
    mock_verify.return_value = False

    payload = create_canvas_webhook_payload()

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        # No Authorization header
    )

    assert response.status_code == 401
    assert "Invalid webhook signature" in response.json()["detail"]


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
@patch("canvas_code_correction.webhooks.deployments.run_deployment")
def test_webhook_deployment_failure(
    mock_run_deployment: Mock,
    mock_flow: AsyncMock,
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling when deployment triggering fails."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True
    mock_flow.deploy.return_value = "deployment-id-123"
    # Simulate deployment run failure
    mock_run_deployment.side_effect = Exception("Deployment failed")

    payload = create_canvas_webhook_payload()

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    # Should return 200 with success=False
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Failed to trigger correction flow" in data["message"]
    # Deployment should have been attempted
    mock_run_deployment.assert_called_once()


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.limiter.hit")
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
@patch("canvas_code_correction.webhooks.deployments.webhook_correction_flow")
@patch("canvas_code_correction.webhooks.deployments.run_deployment")
def test_webhook_custom_deployment_name(
    mock_run_deployment: Mock,
    mock_flow: AsyncMock,
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    mock_limiter_hit: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with custom deployment name."""
    mock_settings.webhook.deployment_name = "custom-deployment-name"
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True
    mock_limiter_hit.return_value = True
    mock_flow.deploy.return_value = "deployment-id-123"
    mock_run = Mock()
    mock_run.id = "flow-run-456"
    mock_run_deployment.return_value = mock_run

    payload = create_canvas_webhook_payload()

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Verify deployment created with custom name
    mock_flow.deploy.assert_called_once_with(
        name="custom-deployment-name",
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
    # Verify deployment run with custom name
    mock_run_deployment.assert_called_once_with(
        name="custom-deployment-name",
        parameters={
            "assignment_id": 123,
            "submission_id": 456,
            "download_dir": None,
            "dry_run": False,
        },
        timeout=0,
    )
