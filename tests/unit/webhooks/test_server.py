"""Unit tests for webhook server endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from canvas_code_correction.bootstrap import CourseBlockLoadError
from canvas_code_correction.webhooks import server as webhook_server
from canvas_code_correction.webhooks.auth import WebhookVerificationResult
from canvas_code_correction.webhooks.deployments import TriggerDeploymentResult
from canvas_code_correction.webhooks.models import CanvasWebhookPayload
from tests.webhooks_shared import create_canvas_webhook_payload

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from canvas_code_correction.config import Settings


pytestmark = pytest.mark.usefixtures("reset_rate_limiter_cache")


def test_health_endpoint(client: TestClient) -> None:
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_success(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test successful webhook handling."""
    mock_resolve_settings.return_value = mock_settings

    # Mock verification to succeed
    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = WebhookVerificationResult(
            success=True,
            message="verified",
            status_code=200,
            mode="test",
        )
        mock_runner = AsyncMock()
        mock_runner.return_value = TriggerDeploymentResult(
            deployment_name="test-deployment",
            success=True,
            flow_run_id="flow-run-123",
        )
        webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: (
            mock_runner
        )

        try:
            payload = create_canvas_webhook_payload()

            response = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )
        finally:
            webhook_server.app.dependency_overrides.pop(
                webhook_server.get_webhook_runner,
                None,
            )

    assert response.status_code == 202
    data = response.json()
    assert data["success"] is True
    assert data["flow_run_id"] == "flow-run-123"
    assert data["course_block"] == "test-course"
    assert data["assignment_id"] == 123
    assert data["submission_id"] == 456
    call_args = mock_verify.call_args
    payload_arg = call_args.kwargs.get("payload")
    if payload_arg is None:
        payload_arg = call_args.args[3]
    assert isinstance(payload_arg, CanvasWebhookPayload)
    assert payload_arg.get_event_type() == "submission_created"
    mock_runner.assert_awaited_once_with(mock_settings, "test-course", 123, 456)


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
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


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_invalid_signature(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with invalid signature."""
    mock_resolve_settings.return_value = mock_settings

    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = WebhookVerificationResult(
            success=False,
            message="Invalid webhook signature",
            status_code=401,
            mode="test",
        )

        payload = create_canvas_webhook_payload()

        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid webhook signature"


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_unsupported_event(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with unsupported event type."""
    mock_resolve_settings.return_value = mock_settings

    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = WebhookVerificationResult(
            success=True,
            message="verified",
            status_code=200,
            mode="test",
        )

        payload = create_canvas_webhook_payload(event_name="assignment_created")

        mock_runner = AsyncMock()
        webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: (
            mock_runner
        )
        try:
            response = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )
        finally:
            webhook_server.app.dependency_overrides.pop(
                webhook_server.get_webhook_runner,
                None,
            )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Ignored unsupported event: assignment_created"
    mock_runner.assert_not_called()


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_invalid_event_payload(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling when the event payload shape is invalid."""
    mock_resolve_settings.return_value = mock_settings

    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = WebhookVerificationResult(
            success=True,
            message="verified",
            status_code=200,
            mode="test",
        )

        payload = create_canvas_webhook_payload()
        payload["body"] = {"assignment_id": "123"}

        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == "Invalid submission event payload"


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_rate_limit(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test rate limiting."""
    mock_resolve_settings.return_value = mock_settings

    with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
        mock_verify.return_value = WebhookVerificationResult(
            success=True,
            message="verified",
            status_code=200,
            mode="test",
        )

        mock_limiter = MagicMock()
        mock_limiter.hit.return_value = False  # Rate limit exceeded
        mock_runner = AsyncMock()
        mock_runner.return_value = TriggerDeploymentResult(
            deployment_name="test-deployment",
            success=True,
            flow_run_id="flow-run-123",
        )
        webhook_server.app.dependency_overrides[webhook_server.get_rate_limiter] = lambda: (
            mock_limiter
        )
        webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: (
            mock_runner
        )
        try:
            payload = create_canvas_webhook_payload()

            response = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )
        finally:
            webhook_server.app.dependency_overrides.pop(
                webhook_server.get_rate_limiter,
                None,
            )
            webhook_server.app.dependency_overrides.pop(
                webhook_server.get_webhook_runner,
                None,
            )

    assert response.status_code == 429
    data = response.json()
    assert "Rate limit exceeded" in data["detail"]
    mock_verify.assert_not_called()


def test_get_rate_limited_settings_skips_disabled_webhooks(mock_settings: Settings) -> None:
    """Disabled webhooks should still return a 403 from validation, not a 429."""
    mock_settings.webhook.enabled = False
    mock_limiter = MagicMock()

    result = webhook_server.get_rate_limited_settings(
        "test-course",
        settings=mock_settings,
        limiter=mock_limiter,
    )

    assert result is mock_settings
    mock_limiter.hit.assert_not_called()


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_ignores_duplicate_delivery(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test duplicate deliveries do not trigger a second flow run."""
    mock_resolve_settings.return_value = mock_settings

    payload = create_canvas_webhook_payload()
    payload["metadata"]["request_id"] = "delivery-123"

    with (
        patch(
            "canvas_code_correction.webhooks.server.verify_canvas_webhook",
            return_value=WebhookVerificationResult(
                success=True,
                message="verified",
                status_code=200,
                mode="test",
            ),
        ),
    ):
        mock_runner = AsyncMock()
        mock_runner.return_value = TriggerDeploymentResult(
            deployment_name="test-deployment",
            success=True,
            flow_run_id="flow-run-123",
        )
        webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: (
            mock_runner
        )
        try:
            first = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )
            second = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )
        finally:
            webhook_server.app.dependency_overrides.pop(
                webhook_server.get_webhook_runner,
                None,
            )

    assert first.status_code == 202
    assert first.json()["success"] is True
    assert second.status_code == 200
    assert second.json()["success"] is True
    assert second.json()["message"] == "Duplicate webhook ignored"
    mock_runner.assert_awaited_once()


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_injects_runtime_state(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test runtime state injection for rate limiter and run gate."""
    mock_resolve_settings.return_value = mock_settings

    mock_limiter = MagicMock()
    mock_limiter.hit.return_value = True

    mock_run_gate = MagicMock()
    mock_run_gate.try_acquire.side_effect = [True, False]

    state = webhook_server.WebhookRuntimeState(
        rate_limiter=mock_limiter,
        run_gate=mock_run_gate,
    )

    previous_factory = webhook_server.get_webhook_runtime_state_factory()
    webhook_server.set_webhook_runtime_state_factory(lambda: state)
    webhook_server.reset_runtime_state(webhook_server.app)

    try:
        with patch("canvas_code_correction.webhooks.server.verify_canvas_webhook") as mock_verify:
            mock_verify.return_value = WebhookVerificationResult(
                success=True,
                message="verified",
                status_code=200,
                mode="test",
            )
            mock_runner = AsyncMock()
            mock_runner.return_value = TriggerDeploymentResult(
                deployment_name="test-deployment",
                success=True,
                flow_run_id="flow-run-123",
            )
            webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: (
                mock_runner
            )

            payload = create_canvas_webhook_payload()
            payload["metadata"]["request_id"] = "injected-123"

            first = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )
            second = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers={"Authorization": "Bearer dummy"},
            )
    finally:
        webhook_server.app.dependency_overrides.pop(
            webhook_server.get_webhook_runner,
            None,
        )
        webhook_server.set_webhook_runtime_state_factory(previous_factory)

    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["message"] == "Duplicate webhook ignored"
    assert mock_limiter.hit.call_count == 2
    assert mock_run_gate.try_acquire.call_count == 2
    mock_runner.assert_awaited_once_with(mock_settings, "test-course", 123, 456)


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_returns_404_for_missing_course_block(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
) -> None:
    mock_resolve_settings.side_effect = CourseBlockLoadError(
        "missing-course",
        "course block missing",
        cause=ValueError("course block missing"),
    )

    response = client.post(
        "/webhooks/canvas/missing-course",
        json={},
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "course block missing"


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_returns_500_for_wrapped_internal_settings_error(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
) -> None:
    mock_resolve_settings.side_effect = CourseBlockLoadError(
        "test-course",
        "prefect offline",
        cause=RuntimeError("prefect offline"),
    )

    response = client.post(
        "/webhooks/canvas/test-course",
        json={},
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to load course block test-course"


@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_handle_canvas_webhook_returns_500_for_internal_settings_errors(
    mock_resolve_settings: AsyncMock,
    client: TestClient,
) -> None:
    mock_resolve_settings.side_effect = RuntimeError("prefect offline")

    response = client.post(
        "/webhooks/canvas/test-course",
        json={},
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to load course block test-course"
