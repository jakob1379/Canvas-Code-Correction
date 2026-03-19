"""Integration tests for Canvas webhook signals with mocked Canvas API."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import SecretStr

from canvas_code_correction.webhooks import server as webhook_server
from canvas_code_correction.webhooks.auth import WebhookVerificationResult
from canvas_code_correction.webhooks.deployments import TriggerDeploymentResult
from tests.webhooks_shared import create_canvas_webhook_payload

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from canvas_code_correction.config import Settings


pytestmark = pytest.mark.usefixtures("reset_rate_limiter_cache")


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_jwt_authentication(
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
    mock_verify.return_value = WebhookVerificationResult(
        success=True,
        message="verified",
        status_code=200,
        mode="test",
    )
    mock_runner = AsyncMock()
    mock_runner.return_value = TriggerDeploymentResult(
        deployment_name="test-course",
        success=True,
        flow_run_id="flow-run-456",
    )
    webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: mock_runner

    payload = create_canvas_webhook_payload()

    try:
        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer valid-jwt-token"},
        )
    finally:
        webhook_server.app.dependency_overrides.pop(webhook_server.get_webhook_runner, None)
    if response.status_code != 200:
        print(f"Response error: {response.status_code} {response.json()}")

    assert response.status_code == 202
    data = response.json()
    assert data["success"] is True
    assert data["flow_run_id"] == "flow-run-456"
    assert data["course_block"] == "test-course"
    assert data["assignment_id"] == 123
    assert data["submission_id"] == 456
    mock_verify.assert_called_once()
    mock_runner.assert_awaited_once_with(mock_settings, "test-course", 123, 456)


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_submission_updated_event(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with submission_updated event."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = WebhookVerificationResult(
        success=True,
        message="verified",
        status_code=200,
        mode="test",
    )
    mock_runner = AsyncMock()
    mock_runner.return_value = TriggerDeploymentResult(
        deployment_name="test-course",
        success=True,
        flow_run_id="flow-run-456",
    )
    webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: mock_runner

    payload = create_canvas_webhook_payload(event_name="submission_updated")

    try:
        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )
    finally:
        webhook_server.app.dependency_overrides.pop(webhook_server.get_webhook_runner, None)

    assert response.status_code == 202
    data = response.json()
    assert data["success"] is True
    assert data["flow_run_id"] == "flow-run-456"
    assert data["course_block"] == "test-course"
    assert data["assignment_id"] == 123
    assert data["submission_id"] == 456
    mock_runner.assert_awaited_once_with(mock_settings, "test-course", 123, 456)


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_unsupported_event_type(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with unsupported event type."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = WebhookVerificationResult(
        success=True,
        message="verified",
        status_code=200,
        mode="test",
    )

    payload = create_canvas_webhook_payload(event_name="assignment_created")
    # Override metadata event_name
    payload["metadata"]["event_name"] = "assignment_created"
    mock_runner = AsyncMock()
    mock_runner.return_value = TriggerDeploymentResult(
        deployment_name="test-course",
        success=True,
        flow_run_id="flow-run-456",
    )
    webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: mock_runner

    try:
        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )
    finally:
        webhook_server.app.dependency_overrides.pop(webhook_server.get_webhook_runner, None)

    assert response.status_code == 422
    data = response.json()
    assert "Unsupported event type" in data["detail"]
    mock_runner.assert_not_awaited()


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_missing_assignment_id(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with missing assignment_id in payload."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = WebhookVerificationResult(
        success=True,
        message="verified",
        status_code=200,
        mode="test",
    )

    payload = create_canvas_webhook_payload()
    del payload["body"]["assignment_id"]

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == "Invalid submission event payload"


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_invalid_ids_non_numeric(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with non-numeric assignment/submission IDs."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = WebhookVerificationResult(
        success=True,
        message="verified",
        status_code=200,
        mode="test",
    )

    payload = create_canvas_webhook_payload(assignment_id="not-a-number", submission_id="also-not")

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 422
    data = response.json()
    assert "Invalid ID format" in data["detail"]


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
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
    mock_verify.return_value = WebhookVerificationResult(
        success=False,
        message="Missing Authorization header for JWT webhook",
        status_code=401,
        mode="jwt",
    )

    payload = create_canvas_webhook_payload()

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        # No Authorization header
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Authorization header for JWT webhook"


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_deployment_failure(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling when deployment triggering fails."""
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = WebhookVerificationResult(
        success=True,
        message="verified",
        status_code=200,
        mode="test",
    )
    mock_runner = AsyncMock()
    mock_runner.return_value = TriggerDeploymentResult(
        deployment_name="test-course",
        success=False,
        error="Deployment failed",
        error_type="Exception",
        stage="trigger",
    )
    webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: mock_runner

    payload = create_canvas_webhook_payload()

    try:
        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )
    finally:
        webhook_server.app.dependency_overrides.pop(webhook_server.get_webhook_runner, None)

    # Should return 200 with success=False
    assert response.status_code == 502
    data = response.json()
    assert data["success"] is False
    assert "Failed to trigger correction flow during trigger" in data["message"]
    assert "Deployment failed" in data["message"]
    # Deployment should have been attempted
    mock_runner.assert_awaited_once_with(mock_settings, "test-course", 123, 456)


@pytest.mark.integration
@patch("canvas_code_correction.webhooks.server.get_rate_limiter")
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
@patch("canvas_code_correction.webhooks.server.verify_canvas_webhook")
def test_webhook_custom_deployment_name(
    mock_verify: AsyncMock,
    mock_resolve_settings: Mock,
    mock_get_rate_limiter: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with custom deployment name."""
    mock_settings.webhook.deployment_name = "custom-deployment-name"
    mock_resolve_settings.return_value = mock_settings
    mock_verify.return_value = WebhookVerificationResult(
        success=True,
        message="verified",
        status_code=200,
        mode="test",
    )
    mock_limiter = Mock()
    mock_limiter.hit.return_value = True
    mock_get_rate_limiter.return_value = mock_limiter
    mock_runner = AsyncMock()
    mock_runner.return_value = TriggerDeploymentResult(
        deployment_name="webhook-correction-flow/custom-deployment-name",
        success=True,
        flow_run_id="flow-run-456",
    )
    webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: mock_runner

    payload = create_canvas_webhook_payload()

    try:
        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )
    finally:
        webhook_server.app.dependency_overrides.pop(webhook_server.get_webhook_runner, None)

    assert response.status_code == 202
    data = response.json()
    assert data["success"] is True
    mock_runner.assert_awaited_once_with(
        mock_settings,
        "test-course",
        123,
        456,
    )
