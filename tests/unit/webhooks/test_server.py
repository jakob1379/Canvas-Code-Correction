"""Unit tests for webhook server endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

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
    """Mock settings for testing."""
    return Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake-token"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test-bucket"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(
            enabled=True,
            require_jwt=False,
            secret=None,
            rate_limit="10/minute",
        ),
    )


@pytest.fixture
def client() -> TestClient:
    """Test client for FastAPI app."""
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
def test_handle_canvas_webhook_success(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test successful webhook handling."""
    mock_resolve_settings.return_value = mock_settings

    # Mock verification to succeed
    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = True

        # Mock deployment triggering
        with patch("canvas_code_correction.webhooks.server.trigger_deployment") as mock_trigger:
            mock_trigger.return_value = "flow-run-123"

            payload = {
                "metadata": {
                    "event_name": "submission_created",
                    "event_time": datetime.now(UTC).isoformat(),
                    "producer": "canvas",
                },
                "body": {
                    "assignment_id": "123",
                    "submission_id": "456",
                    "submission_type": "online_text_entry",
                    "submitted_at": datetime.now(UTC).isoformat(),
                    "updated_at": datetime.now(UTC).isoformat(),
                    "user_id": "789",
                    "workflow_state": "submitted",
                },
            }

            response = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["flow_run_id"] == "flow-run-123"
    assert data["course_block"] == "test-course"
    assert data["assignment_id"] == 123
    assert data["submission_id"] == 456


@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
def test_handle_canvas_webhook_disabled(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling when webhook disabled."""
    mock_settings.webhook.enabled = False
    mock_resolve_settings.return_value = mock_settings

    response = client.post(
        "/webhooks/canvas/test-course",
        json={"metadata": {}, "body": {}},
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Webhook processing disabled for this course"


@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
def test_handle_canvas_webhook_invalid_signature(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with invalid signature."""
    mock_resolve_settings.return_value = mock_settings

    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = False

        response = client.post(
            "/webhooks/canvas/test-course",
            json={"metadata": {}, "body": {}},
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid webhook signature"


@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
def test_handle_canvas_webhook_unsupported_event(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with unsupported event type."""
    mock_resolve_settings.return_value = mock_settings

    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = True

        payload = {
            "metadata": {
                "event_name": "assignment_created",
                "event_time": datetime.now(UTC).isoformat(),
                "producer": "canvas",
            },
            "body": {},
        }

        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == 200  # Returns 200 with success=False
    data = response.json()
    assert data["success"] is False
    assert "Unsupported event type" in data["message"]


@patch("canvas_code_correction.webhooks.server.resolve_settings_from_block")
def test_handle_canvas_webhook_rate_limit(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test rate limiting."""
    mock_resolve_settings.return_value = mock_settings

    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = True

        with patch("canvas_code_correction.webhooks.server.limiter.hit") as mock_hit:
            mock_hit.return_value = False  # Rate limit exceeded

            payload = {
                "metadata": {
                    "event_name": "submission_created",
                    "event_time": datetime.now(UTC).isoformat(),
                    "producer": "canvas",
                },
                "body": {
                    "assignment_id": "123",
                    "submission_id": "456",
                    "submission_type": "online_text_entry",
                    "submitted_at": datetime.now(UTC).isoformat(),
                    "updated_at": datetime.now(UTC).isoformat(),
                    "user_id": "789",
                    "workflow_state": "submitted",
                },
            }

            response = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )

    assert response.status_code == 429
    data = response.json()
    assert "Rate limit exceeded" in data["detail"]


def test_test_webhook_endpoint(client: TestClient) -> None:
    """Test manual test endpoint."""
    with patch(
        "canvas_code_correction.webhooks.server.resolve_settings_from_block",
    ) as mock_resolve:
        mock_resolve.return_value = Settings(
            canvas=CanvasSettings(
                api_url=HttpUrl("https://canvas.instructure.com"),
                token=SecretStr("fake"),
                course_id=1,
            ),
            assets=CourseAssetsSettings(bucket_block="test"),
            grader=GraderSettings(),
            workspace=WorkspaceSettings(),
            webhook=WebhookSettings(enabled=True),
        )

        response = client.post("/webhooks/canvas/test-course/test")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Webhook configuration test"
