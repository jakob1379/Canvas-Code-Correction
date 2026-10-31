"""Unit tests for webhook authentication."""

import io
import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock, patch

import jwt
import jwt.algorithms
import jwt.exceptions
import pytest
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WebhookAuthMode,
    WebhookSettings,
    WorkspaceSettings,
)
from canvas_code_correction.webhooks.auth import (
    WebhookSignatureHeaders,
    WebhookVerificationResult,
    clear_jwk_cache,
    validate_canvas_signature,
    validate_hmac_signature,
    validate_jwt_token,
    verify_canvas_webhook,
    verify_via_canvas_api,
)
from tests.webhooks_shared import create_canvas_webhook_payload


def _signed_jwt_settings() -> Settings:
    return Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.instructure.com"),
            token=SecretStr("fake"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="test"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(),
        webhook=WebhookSettings(auth_mode=WebhookAuthMode.CANVAS_SIGNED_JWT),
    )


_SIGNING_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _course_claims(
    context_id: str | None = "1",
    *,
    context_type: str = "Course",
    event_time: datetime | None = None,
) -> dict:
    claims = create_canvas_webhook_payload()
    claims["metadata"].update(context_type=context_type, context_id=context_id)
    if event_time is not None:
        claims["metadata"]["event_time"] = event_time.isoformat()
    return claims


def _sign(claims: dict, key: rsa.RSAPrivateKey = _SIGNING_KEY) -> bytes:
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "current"}).encode()


def _jwks(alg: str = "RS256") -> dict:
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(_SIGNING_KEY.public_key(), as_dict=True)
    return {"keys": [{**jwk, "kid": "current", "alg": alg}]}


@contextmanager
def _serve_jwks(jwks: dict | None = None) -> Iterator[MagicMock]:
    clear_jwk_cache()
    document = json.dumps(jwks or _jwks()).encode()
    with patch("jwt.jwks_client.urllib.request.build_opener") as build_opener:
        opener = build_opener.return_value
        opener.open.side_effect = lambda *_args, **_kwargs: io.BytesIO(document)
        yield opener.open


def _verify_signed(body: bytes) -> WebhookVerificationResult:
    return validate_canvas_signature(_signed_jwt_settings(), body, WebhookSignatureHeaders())


def test_validate_canvas_signed_jwt_body() -> None:
    """A body signed by the Canvas key exposes its decoded event payload."""
    with _serve_jwks():
        result = _verify_signed(_sign(_course_claims()))

    assert result.success is True
    assert result.mode == "canvas-signed-jwt"
    assert result.payload is not None
    assert result.payload.metadata.event_name == "submission_created"


def test_validate_canvas_signed_jwt_rejects_body_signed_by_another_key() -> None:
    """A body signed by any key other than the published Canvas key is rejected."""
    with _serve_jwks():
        result = _verify_signed(_sign(_course_claims(), key=_OTHER_KEY))

    assert result.success is False
    assert result.status_code == 401


def test_validate_canvas_signed_jwt_reports_invalid_signed_body_as_unprocessable() -> None:
    """A genuine signature over an unusable event is a payload error, not an auth failure."""
    claims = _course_claims()
    del claims["body"]["submitted_at"]
    with _serve_jwks():
        result = _verify_signed(_sign(claims))

    assert result.success is False
    assert result.status_code == 422


def test_validate_canvas_signed_jwt_rejects_expired_token() -> None:
    """An exp claim in the past is enforced."""
    claims = {**_course_claims(), "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp())}
    with _serve_jwks():
        result = _verify_signed(_sign(claims))

    assert result.success is False
    assert result.status_code == 401


@pytest.mark.parametrize(
    ("context_type", "context_id", "accepted"),
    [
        ("Course", "1", True),
        ("Course", "21070000000000001", True),
        ("Course", "2", False),
        ("Course", None, False),
        ("Account", "1", False),
    ],
)
def test_validate_canvas_signed_jwt_binds_event_to_course(
    context_type: str,
    context_id: str | None,
    *,
    accepted: bool,
) -> None:
    """A valid signature only authorizes events whose context is the configured course."""
    with _serve_jwks():
        result = _verify_signed(_sign(_course_claims(context_id, context_type=context_type)))

    assert result.success is accepted
    if not accepted:
        assert result.status_code == 403


@pytest.mark.parametrize("offset", [timedelta(hours=-2), timedelta(hours=2)])
def test_validate_canvas_signed_jwt_rejects_events_outside_time_window(offset: timedelta) -> None:
    """A captured signed body cannot be replayed indefinitely."""
    with _serve_jwks():
        result = _verify_signed(_sign(_course_claims(event_time=datetime.now(UTC) + offset)))

    assert result.success is False
    assert result.status_code == 401


def test_validate_canvas_signed_jwt_rejects_jwk_published_for_another_algorithm() -> None:
    """The JWK's own alg must match the token's, closing key confusion via a relabelled key."""
    with _serve_jwks(_jwks(alg="RS512")):
        result = _verify_signed(_sign(_course_claims()))

    assert result.success is False
    assert result.status_code == 401


def test_validate_canvas_signed_jwt_does_not_refetch_for_each_unknown_kid() -> None:
    """Unknown key IDs cannot force an upstream JWKS fetch per request."""
    unknown_kid = jwt.encode(
        _course_claims(),
        _SIGNING_KEY,
        algorithm="RS256",
        headers={"kid": "unknown"},
    ).encode()
    with _serve_jwks() as fetch:
        results = [_verify_signed(unknown_kid) for _ in range(5)]

    assert all(result.status_code == 401 for result in results)
    assert fetch.call_count == 1


def test_validate_canvas_signed_jwt_refresh_failure_returns_bad_gateway() -> None:
    """An unavailable JWK endpoint is retryable when no cached key exists."""
    with _serve_jwks() as fetch:
        fetch.side_effect = TimeoutError
        result = _verify_signed(_sign(_course_claims()))

    assert result.status_code == 502
    assert result.success is False


def test_validate_canvas_signed_jwt_rejects_symmetric_algorithm() -> None:
    """Signed Canvas events never accept attacker-selected symmetric algorithms."""
    body = jwt.encode(
        _course_claims(),
        "shared-secret-at-least-32-bytes-long",
        algorithm="HS256",
        headers={"kid": "current"},
    ).encode()
    with _serve_jwks():
        result = _verify_signed(body)

    assert result.status_code == 401
    assert result.success is False


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
            mode="legacy-bearer-jwt",
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
            mode="legacy-bearer-jwt",
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
            mode="legacy-bearer-jwt",
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
            mode="canvas-api",
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
            mode="canvas-api",
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
            mode="canvas-api",
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
        mode="canvas-api",
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
        mode="canvas-api",
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
        mode="canvas-api",
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
        mode="canvas-api",
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
        mode="canvas-api",
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
            mode="canvas-api",
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
            mode="canvas-api",
        )
        result = verify_canvas_webhook(settings, payload_body, headers)
        assert result == WebhookVerificationResult(
            success=True,
            message="Canvas API verification succeeded",
            status_code=200,
            mode="canvas-api",
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
            mode="legacy-bearer-jwt",
        )

        result = verify_canvas_webhook(settings, payload_body, headers)

        assert result == WebhookVerificationResult(
            success=True,
            message="ok",
            status_code=200,
            mode="legacy-bearer-jwt",
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
