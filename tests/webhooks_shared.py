"""Shared fixtures and helpers for webhook tests."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Iterator
from datetime import UTC, datetime

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
from canvas_code_correction.webhooks import server as webhook_server
from canvas_code_correction.webhooks.server import app


@pytest.fixture
def mock_settings() -> Settings:
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
    return TestClient(app)


@pytest.fixture
def reset_webhook_runtime_state() -> Iterator[None]:
    previous_factory = webhook_server.get_webhook_runtime_state_factory()
    webhook_server.set_webhook_runtime_state_factory(
        lambda: webhook_server.WebhookRuntimeState(
            rate_limiter=webhook_server.MovingWindowRateLimiter(webhook_server.MemoryStorage()),
            run_gate=webhook_server.WebhookRunGate(),
        ),
    )
    webhook_server.reset_runtime_state(app)
    try:
        yield None
    finally:
        webhook_server.set_webhook_runtime_state_factory(previous_factory)
        webhook_server.reset_runtime_state(app)


@pytest.fixture
def reset_rate_limiter_cache() -> None:
    # Backward-compatible alias retained for existing test modules.
    webhook_server.reset_runtime_state(app)


def create_canvas_webhook_payload(
    event_name: str = "submission_created",
    assignment_id: str = "123",
    submission_id: str = "456",
) -> dict:
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


def create_hmac_headers(payload: dict, secret: str) -> dict[str, str]:
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return {
        "content-type": "application/json",
        "x-canvas-signature": f"sha256={signature}",
    }
