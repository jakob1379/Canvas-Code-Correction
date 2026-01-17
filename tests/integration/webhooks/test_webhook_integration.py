"""Integration tests for webhook server with simulated Canvas payloads."""

from __future__ import annotations

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
def test_webhook_server_end_to_end(
    mock_run_deployment: Mock,
    mock_flow: AsyncMock,
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test end-to-end webhook server integration with simulated Canvas payload."""
    # Setup mocks
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True
    mock_flow.deploy.return_value = "deployment-id-123"
    mock_run = Mock()
    mock_run.id = "flow-run-456"
    mock_run_deployment.return_value = mock_run

    payload = create_canvas_webhook_payload()

    # First request should succeed
    with patch("canvas_code_correction.webhooks.server.limiter.hit") as mock_hit:
        mock_hit.return_value = True
        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )
        assert response.status_code == 200

    # Second request with rate limit exceeded
    with patch("canvas_code_correction.webhooks.server.limiter.hit") as mock_hit:
        mock_hit.return_value = False
        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
def test_webhook_disabled(
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling when webhook processing is disabled."""
    mock_settings.webhook.enabled = False
    mock_resolve_settings.return_value = mock_settings

    payload = create_canvas_webhook_payload(event_name="submission_created")

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 403
    assert "Webhook processing disabled" in response.json()["detail"]


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_invalid_signature(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with invalid signature."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = True
    mock_trigger.return_value = "flow-run-123"

    payload = create_canvas_webhook_payload()

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 401
    assert "Invalid webhook signature" in response.json()["detail"]
