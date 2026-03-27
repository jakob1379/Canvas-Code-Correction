"""Unit tests for webhook authentication."""

import json
from collections.abc import Mapping
from typing import cast
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
    WebhookSignatureHeaders,
    WebhookVerificationResult,
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
            WebhookSignatureHeaders(authorization="Bearer valid.token"),
        )
        assert result == WebhookVerificationResult(
            success=True,
            message="JWT verification succeeded",
            status_code=200,
            mode="jwt",
        )
        mock_validate.assert_called_once_with("valid.token", settings.webhook.secret)

    # No Authorization header
    with patch("canvas_code_correction.webhooks.auth.validate_jwt_token") as mock_validate:
        result = validate_canvas_signature(
            settings,
            b"payload",
            WebhookSignatureHeaders(),
        )
        assert result == WebhookVerificationResult(
            success=False,
            message="Missing Authorization header for JWT webhook",
            status_code=401,
            mode="jwt",
        )
        mock_validate.assert_not_called()

    # Invalid Bearer format
    with patch("canvas_code_correction.webhooks.auth.validate_jwt_token") as mock_validate:
        result = validate_canvas_signature(
            settings,
            b"payload",
            WebhookSignatureHeaders(authorization="InvalidHeader"),
        )
        assert result == WebhookVerificationResult(
            success=False,
            message="Authorization header must use Bearer token format",
            status_code=401,
            mode="jwt",
        )
        mock_validate.assert_not_called()


def test_validate_canvas_signature_requires_explicit_canvas_api_fallback() -> None:
    """Test secret-less webhook auth is denied by default."""
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

    with patch("canvas_code_correction.webhooks.auth.verify_via_canvas_api") as mock_verify:
        result = validate_canvas_signature(
            settings,
            b"payload",
            WebhookSignatureHeaders(),
        )
        assert result == WebhookVerificationResult(
            success=False,
            message=(
                "Webhook verification is not configured; set a webhook secret, "
                "require JWT, or explicitly enable Canvas API fallback"
            ),
            status_code=401,
            mode="unconfigured",
        )
        mock_verify.assert_not_called()


def test_validate_canvas_signature_uses_explicit_canvas_api_fallback() -> None:
    """Test Canvas API fallback remains available when explicitly enabled."""
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
            allow_canvas_api_fallback=True,
        ),
    )

    with patch("canvas_code_correction.webhooks.auth.verify_via_canvas_api") as mock_verify:
        mock_verify.return_value = WebhookVerificationResult(
            success=True,
            message="Canvas API verification succeeded",
            status_code=200,
            mode="canvas_api",
        )
        result = validate_canvas_signature(
            settings,
            b"payload",
            WebhookSignatureHeaders(),
        )
        assert result == WebhookVerificationResult(
            success=True,
            message="Canvas API verification succeeded",
            status_code=200,
            mode="canvas_api",
        )
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
            "metadata": {
                "event_name": "submission_created",
                "event_time": "2026-03-12T00:00:00+00:00",
            },
            "body": {
                "assignment_id": "123",
                "submission_id": "456",
                "submission_type": "online_text_entry",
                "submitted_at": "2026-03-12T00:00:00+00:00",
                "updated_at": "2026-03-12T00:00:00+00:00",
                "user_id": "789",
                "workflow_state": "submitted",
            },
        },
    ).encode()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        result = verify_via_canvas_api(settings, payload_body)
        assert result == WebhookVerificationResult(
            success=True,
            message="Canvas API verification succeeded",
            status_code=200,
            mode="canvas_api",
        )
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
    assert result == WebhookVerificationResult(
        success=False,
        message="Webhook payload is not valid JSON",
        status_code=400,
        mode="canvas_api",
    )

    # Test missing event_name
    payload = json.dumps(
        {
            "metadata": {"event_time": "2026-03-12T00:00:00+00:00"},
            "body": {},
        },
    ).encode()
    result = verify_via_canvas_api(settings, payload)
    assert result == WebhookVerificationResult(
        success=False,
        message="Webhook payload missing assignment or submission id",
        status_code=401,
        mode="canvas_api",
    )

    # Test wrong event name
    payload = json.dumps(
        {
            "metadata": {
                "event_name": "other",
                "event_time": "2026-03-12T00:00:00+00:00",
            },
            "body": {},
        },
    ).encode()
    result = verify_via_canvas_api(settings, payload)
    assert result == WebhookVerificationResult(
        success=False,
        message="Webhook payload missing assignment or submission id",
        status_code=401,
        mode="canvas_api",
    )

    # Test missing IDs
    payload = json.dumps(
        {
            "metadata": {
                "event_name": "submission_created",
                "event_time": "2026-03-12T00:00:00+00:00",
            },
            "body": {},
        },
    ).encode()
    result = verify_via_canvas_api(settings, payload)
    assert result == WebhookVerificationResult(
        success=False,
        message="Webhook payload missing assignment or submission id",
        status_code=401,
        mode="canvas_api",
    )

    # Test non-integer IDs
    payload = json.dumps(
        {
            "metadata": {
                "event_name": "submission_created",
                "event_time": "2026-03-12T00:00:00+00:00",
            },
            "body": {
                "assignment_id": "abc",
                "submission_id": "def",
                "submission_type": "online_text_entry",
                "submitted_at": "2026-03-12T00:00:00+00:00",
                "updated_at": "2026-03-12T00:00:00+00:00",
                "user_id": "789",
                "workflow_state": "submitted",
            },
        },
    ).encode()
    result = verify_via_canvas_api(settings, payload)
    assert result == WebhookVerificationResult(
        success=False,
        message="Webhook payload missing assignment or submission id",
        status_code=401,
        mode="canvas_api",
    )

    # Test API request exception
    payload = json.dumps(
        {
            "metadata": {
                "event_name": "submission_created",
                "event_time": "2026-03-12T00:00:00+00:00",
            },
            "body": {
                "assignment_id": "123",
                "submission_id": "456",
                "submission_type": "online_text_entry",
                "submitted_at": "2026-03-12T00:00:00+00:00",
                "updated_at": "2026-03-12T00:00:00+00:00",
                "user_id": "789",
                "workflow_state": "submitted",
            },
        },
    ).encode()
    with patch("requests.get", side_effect=requests.RequestException):
        result = verify_via_canvas_api(settings, payload)
        assert result.success is False
        assert result.status_code == 502
        assert "Canvas API verification error" in result.message

    # Test non-200 response
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        result = verify_via_canvas_api(settings, payload)
        assert result == WebhookVerificationResult(
            success=False,
            message="Canvas API verification failed",
            status_code=401,
            mode="canvas_api",
        )


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
        result = validate_canvas_signature(
            settings,
            payload_body,
            WebhookSignatureHeaders(canvas_signature="some-signature"),
        )
        assert result == WebhookVerificationResult(
            success=True,
            message="HMAC verification succeeded",
            status_code=200,
            mode="hmac",
        )
        mock_hmac.assert_called_once_with(
            payload_body,
            settings.webhook.secret,
            "some-signature",
        )

    # Canvas-specific HMAC header should be preferred
    with patch("canvas_code_correction.webhooks.auth.validate_hmac_signature") as mock_hmac:
        mock_hmac.return_value = True
        result = validate_canvas_signature(
            settings,
            payload_body,
            WebhookSignatureHeaders(canvas_signature="some-signature"),
        )
        assert result == WebhookVerificationResult(
            success=True,
            message="HMAC verification succeeded",
            status_code=200,
            mode="hmac",
        )
        mock_hmac.assert_called_once_with(
            payload_body,
            settings.webhook.secret,
            "some-signature",
        )

    # Test missing signature header (should return False)
    with patch("canvas_code_correction.webhooks.auth.validate_hmac_signature") as mock_hmac:
        result = validate_canvas_signature(settings, payload_body, WebhookSignatureHeaders())
        assert result == WebhookVerificationResult(
            success=False,
            message="Missing HMAC signature header",
            status_code=401,
            mode="hmac",
        )
        mock_hmac.assert_not_called()


def test_verify_canvas_webhook() -> None:
    """Test webhook verification wrapper."""
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
    headers = {"Authorization": "Bearer token", "X-Canvas-Signature": "abc"}

    with patch("canvas_code_correction.webhooks.auth.validate_canvas_signature") as mock_validate:
        mock_validate.return_value = WebhookVerificationResult(
            success=True,
            message="Canvas API verification succeeded",
            status_code=200,
            mode="canvas_api",
        )
        result = verify_canvas_webhook(settings, payload_body, headers)
        assert result == WebhookVerificationResult(
            success=True,
            message="Canvas API verification succeeded",
            status_code=200,
            mode="canvas_api",
        )
        mock_validate.assert_called_once()
        args = mock_validate.call_args.args
        assert args[0] is settings
        assert args[1] == payload_body
        assert args[2] == WebhookSignatureHeaders(
            authorization="Bearer token",
            canvas_signature="abc",
            hub_signature_256=None,
        )


def test_verify_canvas_webhook_normalizes_header_values() -> None:
    """Test header normalization and whitespace trimming."""
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
    headers = {
        "Authorization": "  Bearer token  ",
        "X-Canvas-Signature": "  abc  ",
    }

    with patch("canvas_code_correction.webhooks.auth.validate_canvas_signature") as mock_validate:
        mock_validate.return_value = WebhookVerificationResult(
            success=True,
            message="ok",
            status_code=200,
            mode="jwt",
        )

        result = verify_canvas_webhook(settings, payload_body, headers)

        assert result == WebhookVerificationResult(
            success=True,
            message="ok",
            status_code=200,
            mode="jwt",
        )
        mock_validate.assert_called_once_with(
            settings,
            payload_body,
            WebhookSignatureHeaders(authorization="Bearer token", canvas_signature="abc"),
        )


def test_verify_canvas_webhook_bad_headers_type() -> None:
    """Test rejection of malformed header payload."""
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

    assert verify_canvas_webhook(
        settings,
        b"payload",
        cast("Mapping[str, str]", None),
    ) == WebhookVerificationResult(
        success=False,
        message="Webhook headers must be key/value string data",
        status_code=400,
        mode="signature",
    )
