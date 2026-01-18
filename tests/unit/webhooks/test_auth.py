"""Unit tests for webhook authentication."""

from __future__ import annotations

import json
from unittest.mock import patch

import jwt.exceptions
import requests
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WebhookSettings,
    WorkspaceSettings,
)
from canvas_code_correction.webhooks.auth import (
    validate_canvas_signature,
    validate_hmac_signature,
    validate_jwt_token,
    verify_canvas_webhook,
    verify_via_canvas_api,
)


def test_validate_jwt_token_valid() -> None:
    """Test JWT token validation with valid token."""
    secret = SecretStr("test-secret")
    token = "valid.jwt.token"

    with patch("jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": "webhook"}
        result = validate_jwt_token(token, secret)

    assert result is True
    mock_decode.assert_called_once_with(
        token,
        secret.get_secret_value(),
        algorithms=["HS256"],
        options={"verify_exp": False},
    )


def test_validate_jwt_token_invalid() -> None:
    """Test JWT token validation with invalid token."""
    secret = SecretStr("test-secret")
    token = "invalid.jwt.token"

    with patch("jwt.decode") as mock_decode:
        mock_decode.side_effect = jwt.exceptions.InvalidTokenError
        result = validate_jwt_token(token, secret)

    assert result is False


def test_validate_jwt_token_no_secret() -> None:
    """Test JWT token validation when secret is None."""
    result = validate_jwt_token("token", None)
    assert result is False


def test_validate_canvas_signature_jwt_required() -> None:
    """Test Canvas signature validation with JWT required."""
    from canvas_code_correction.webhooks.auth import validate_canvas_signature

    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(
            enabled=True,
            require_jwt=True,
            secret=SecretStr("secret"),
        ),
    )

    # Mock validate_jwt_token
    with patch("canvas_code_correction.webhooks.auth.validate_jwt_token") as mock_validate:
        mock_validate.return_value = True
        result = validate_canvas_signature(
            settings,
            b"payload",
            "Bearer valid.token",
        )
        assert result is True
        mock_validate.assert_called_once_with("valid.token", settings.webhook.secret)

    # No Authorization header
    with patch("canvas_code_correction.webhooks.auth.validate_jwt_token") as mock_validate:
        result = validate_canvas_signature(
            settings,
            b"payload",
            None,
        )
        assert result is False
        mock_validate.assert_not_called()

    # Invalid Bearer format
    with patch("canvas_code_correction.webhooks.auth.validate_jwt_token") as mock_validate:
        result = validate_canvas_signature(
            settings,
            b"payload",
            "InvalidHeader",
        )
        assert result is False
        mock_validate.assert_not_called()


def test_validate_canvas_signature_jwt_not_required() -> None:
    """Test Canvas signature validation when JWT not required."""
    from canvas_code_correction.webhooks.auth import validate_canvas_signature

    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(
            enabled=True,
            require_jwt=False,
            secret=None,
        ),
    )

    # When JWT not required, validation falls back to Canvas API verification
    with patch("canvas_code_correction.webhooks.auth.verify_via_canvas_api") as mock_verify:
        mock_verify.return_value = True
        result = validate_canvas_signature(
            settings,
            b"payload",
            None,
        )
        assert result is True
        mock_verify.assert_called_once_with(settings, b"payload")


def test_validate_hmac_signature_valid() -> None:
    """Test HMAC signature validation with valid signature."""
    secret = SecretStr("my-secret")
    payload = b"test payload"
    # Compute expected HMAC
    import hashlib
    import hmac

    expected = hmac.new(
        secret.get_secret_value().encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    # Test with prefix
    signature_header = f"sha256={expected}"
    result = validate_hmac_signature(payload, secret, signature_header)
    assert result is True

    # Test without prefix
    result = validate_hmac_signature(payload, secret, expected)
    assert result is True


def test_validate_hmac_signature_invalid() -> None:
    """Test HMAC signature validation with invalid signature."""
    secret = SecretStr("my-secret")
    payload = b"test payload"
    # Wrong signature
    signature_header = "sha256=wronghash"
    result = validate_hmac_signature(payload, secret, signature_header)
    assert result is False

    # No signature header
    result = validate_hmac_signature(payload, secret, None)
    assert result is False


def test_verify_via_canvas_api_success() -> None:
    """Test Canvas API verification with successful response."""
    settings = Settings(
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

    payload_body = json.dumps(
        {
            "metadata": {"event_name": "submission_created"},
            "body": {"assignment_id": "123", "submission_id": "456"},
        },
    ).encode()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        result = verify_via_canvas_api(settings, payload_body)
        assert result is True
        # Verify API call made to correct URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        url = call_args[0][0]
        assert url.endswith("/api/v1/courses/1/assignments/123/submissions/456")


def test_verify_via_canvas_api_failure() -> None:
    """Test Canvas API verification with various failure modes."""
    settings = Settings(
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

    # Test invalid JSON
    result = verify_via_canvas_api(settings, b"invalid json")
    assert result is False

    # Test missing event_name
    payload = json.dumps({"metadata": {}, "body": {}}).encode()
    result = verify_via_canvas_api(settings, payload)
    assert result is False

    # Test wrong event name
    payload = json.dumps({"metadata": {"event_name": "other"}, "body": {}}).encode()
    result = verify_via_canvas_api(settings, payload)
    assert result is False

    # Test missing IDs
    payload = json.dumps({"metadata": {"event_name": "submission_created"}, "body": {}}).encode()
    result = verify_via_canvas_api(settings, payload)
    assert result is False

    # Test non-integer IDs
    payload = json.dumps(
        {
            "metadata": {"event_name": "submission_created"},
            "body": {"assignment_id": "abc", "submission_id": "def"},
        },
    ).encode()
    result = verify_via_canvas_api(settings, payload)
    assert result is False

    # Test API request exception
    payload = json.dumps(
        {
            "metadata": {"event_name": "submission_created"},
            "body": {"assignment_id": "123", "submission_id": "456"},
        },
    ).encode()
    with patch("requests.get", side_effect=requests.RequestException):
        result = verify_via_canvas_api(settings, payload)
        assert result is False

    # Test non-200 response
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        result = verify_via_canvas_api(settings, payload)
        assert result is False


def test_validate_canvas_signature_hmac() -> None:
    """Test Canvas signature validation with HMAC secret."""
    settings = Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(
            enabled=True,
            require_jwt=False,
            secret=SecretStr("hmac-secret"),
        ),
    )

    payload_body = b"test payload"
    # Mock validate_hmac_signature to return True
    with patch("canvas_code_correction.webhooks.auth.validate_hmac_signature") as mock_hmac:
        mock_hmac.return_value = True
        result = validate_canvas_signature(settings, payload_body, "some-signature")
        assert result is True
        mock_hmac.assert_called_once_with(payload_body, settings.webhook.secret, "some-signature")

    # Test missing signature header (should return False)
    with patch("canvas_code_correction.webhooks.auth.validate_hmac_signature") as mock_hmac:
        result = validate_canvas_signature(settings, payload_body, None)
        assert result is False
        mock_hmac.assert_not_called()


def test_verify_canvas_webhook() -> None:
    """Test async webhook verification wrapper."""
    settings = Settings(
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

    payload_body = b"payload"
    headers = {"Authorization": "Bearer token"}

    with patch("canvas_code_correction.webhooks.auth.validate_canvas_signature") as mock_validate:
        mock_validate.return_value = True
        import asyncio

        result = asyncio.run(verify_canvas_webhook(settings, payload_body, headers))
        assert result is True
        mock_validate.assert_called_once_with(settings, payload_body, "Bearer token")
