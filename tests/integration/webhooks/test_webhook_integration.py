"""Integration tests for webhook server with simulated Canvas payloads."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import SecretStr

from canvas_code_correction.webhooks import server as webhook_server
from canvas_code_correction.webhooks.deployments import TriggerDeploymentResult
from tests.webhooks_shared import create_canvas_webhook_payload, create_hmac_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from canvas_code_correction.config import Settings


@pytest.mark.integration
@pytest.mark.usefixtures("reset_rate_limiter_cache")
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_webhook_server_end_to_end(
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test end-to-end webhook server integration with simulated Canvas payload."""
    mock_settings.webhook.secret = SecretStr("shared-secret")
    mock_resolve_settings.return_value = mock_settings
    mock_runner = AsyncMock()
    mock_runner.return_value = TriggerDeploymentResult(
        deployment_name="ccc-test-course-deployment",
        success=True,
        flow_run_id="flow-run-456",
    )
    webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: mock_runner

    payload = create_canvas_webhook_payload()
    headers = create_hmac_headers(payload, "shared-secret")
    second_payload = dict(payload)
    second_payload["metadata"] = dict(payload["metadata"])
    second_payload["metadata"]["request_id"] = "duplicate-test-request"
    second_headers = create_hmac_headers(second_payload, "shared-secret")

    try:
        first_limiter = Mock()
        first_limiter.hit.return_value = True
        second_limiter = Mock()
        second_limiter.hit.return_value = False
        limiter_overrides = iter([first_limiter, second_limiter])
        webhook_server.app.dependency_overrides[webhook_server.get_rate_limiter] = lambda: next(
            limiter_overrides,
        )

        response = client.post(
            "/webhooks/canvas/test-course",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 202
        assert response.json()["success"] is True
        mock_runner.assert_awaited_once_with(
            mock_settings,
            "test-course",
            123,
            456,
        )

        # Second request with rate limit exceeded
        response = client.post(
            "/webhooks/canvas/test-course",
            json=second_payload,
            headers=second_headers,
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    finally:
        webhook_server.app.dependency_overrides.pop(webhook_server.get_webhook_runner, None)
        webhook_server.app.dependency_overrides.pop(webhook_server.get_rate_limiter, None)


@pytest.mark.integration
@pytest.mark.usefixtures("reset_rate_limiter_cache")
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
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
@pytest.mark.usefixtures("reset_rate_limiter_cache")
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_webhook_invalid_signature(
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook handling with invalid signature."""
    mock_settings.webhook.secret = SecretStr("shared-secret")
    mock_resolve_settings.return_value = mock_settings

    payload = create_canvas_webhook_payload()
    headers = {
        "content-type": "application/json",
        "x-canvas-signature": "sha256=bad",
    }

    response = client.post(
        "/webhooks/canvas/test-course",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 401
    assert "Invalid HMAC webhook signature" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.usefixtures("reset_rate_limiter_cache")
@patch("canvas_code_correction.webhooks.server.load_settings_from_course_block")
def test_webhook_prefect_handoff_failure_returns_unsuccessful_response(
    mock_resolve_settings: Mock,
    client: TestClient,
    mock_settings: Settings,
) -> None:
    """Test webhook response when the Prefect run handoff fails."""
    mock_settings.webhook.secret = SecretStr("shared-secret")
    mock_resolve_settings.return_value = mock_settings
    mock_runner = AsyncMock()
    mock_runner.return_value = TriggerDeploymentResult(
        deployment_name="ccc-test-course-deployment",
        success=False,
        error="Prefect unavailable",
        error_type="RuntimeError",
        stage="trigger",
    )
    webhook_server.app.dependency_overrides[webhook_server.get_webhook_runner] = lambda: mock_runner

    payload = create_canvas_webhook_payload()
    headers = create_hmac_headers(payload, "shared-secret")

    mock_limiter = Mock()
    mock_limiter.hit.return_value = True
    try:
        with patch(
            "canvas_code_correction.webhooks.server.get_rate_limiter",
            return_value=mock_limiter,
        ):
            response = client.post(
                "/webhooks/canvas/test-course",
                json=payload,
                headers=headers,
            )
    finally:
        webhook_server.app.dependency_overrides.pop(webhook_server.get_webhook_runner, None)

    assert response.status_code == 502
    body = response.json()
    assert body["success"] is False
    assert "Failed to trigger correction flow during trigger (RuntimeError)" in body["message"]
    assert body["assignment_id"] == 123
    assert body["submission_id"] == 456
    mock_runner.assert_awaited_once_with(mock_settings, "test-course", 123, 456)
