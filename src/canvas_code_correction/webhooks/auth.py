"""Authentication and validation for Canvas webhooks."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

import jwt
import requests
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pydantic import SecretStr

    from canvas_code_correction.config import Settings

from canvas_code_correction.webhooks.models import (
    CanvasWebhookPayload,
    UnsupportedSubmissionEventError,
)


def _is_json_parse_error(error: ValidationError) -> bool:
    return any(item.get("type") == "json_invalid" for item in error.errors())


@dataclass(frozen=True)
class WebhookSignatureHeaders:
    """Headers relevant to webhook signature validation."""

    authorization: str | None = None
    canvas_signature: str | None = None
    hub_signature_256: str | None = None

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> WebhookSignatureHeaders:
        """Extract supported signature headers from a request header mapping."""
        normalized = {key.lower(): value for key, value in headers.items()}
        return cls(
            authorization=normalized.get("authorization"),
            canvas_signature=normalized.get("x-canvas-signature"),
            hub_signature_256=normalized.get("x-hub-signature-256"),
        )

    def hmac_signature(self) -> str | None:
        """Return the preferred HMAC signature header value, if present."""
        return self.canvas_signature or self.hub_signature_256


def _jwt_verification_result(
    settings: Settings,
    headers: WebhookSignatureHeaders,
) -> WebhookVerificationResult:
    if not headers.authorization:
        return WebhookVerificationResult(
            success=False,
            message="Missing Authorization header for JWT webhook",
            status_code=HTTPStatus.UNAUTHORIZED.value,
            mode="jwt",
        )

    if not headers.authorization.startswith("Bearer "):
        return WebhookVerificationResult(
            success=False,
            message="Authorization header must use Bearer token format",
            status_code=HTTPStatus.UNAUTHORIZED.value,
            mode="jwt",
        )

    token = headers.authorization[7:]
    if validate_jwt_token(token, settings.webhook.secret):
        return WebhookVerificationResult(
            success=True,
            message="JWT verification succeeded",
            status_code=HTTPStatus.OK.value,
            mode="jwt",
        )

    return WebhookVerificationResult(
        success=False,
        message="Invalid JWT webhook signature",
        status_code=HTTPStatus.UNAUTHORIZED.value,
        mode="jwt",
    )


def _hmac_verification_result(
    settings: Settings,
    payload_body: bytes,
    headers: WebhookSignatureHeaders,
) -> WebhookVerificationResult:
    secret = settings.webhook.secret
    if secret is None:
        return WebhookVerificationResult(
            success=False,
            message="Missing HMAC secret for webhook verification",
            status_code=HTTPStatus.UNAUTHORIZED.value,
            mode="hmac",
        )

    hmac_header = headers.hmac_signature()
    if not hmac_header:
        return WebhookVerificationResult(
            success=False,
            message="Missing HMAC signature header",
            status_code=HTTPStatus.UNAUTHORIZED.value,
            mode="hmac",
        )

    if validate_hmac_signature(payload_body, secret, hmac_header):
        return WebhookVerificationResult(
            success=True,
            message="HMAC verification succeeded",
            status_code=HTTPStatus.OK.value,
            mode="hmac",
        )

    return WebhookVerificationResult(
        success=False,
        message="Invalid HMAC webhook signature",
        status_code=HTTPStatus.UNAUTHORIZED.value,
        mode="hmac",
    )


@dataclass(frozen=True)
class WebhookVerificationResult:
    """Structured result of webhook verification."""

    success: bool
    message: str
    status_code: int
    mode: str


def validate_jwt_token(token: str, secret: SecretStr | None) -> bool:
    """Validate JWT token using shared secret.

    Canvas webhooks can be signed with JWT using HS256 algorithm.
    The token is typically provided in the Authorization header as Bearer token.
    """
    if secret is None:
        return False

    try:
        jwt.decode(
            token,
            secret.get_secret_value(),
            algorithms=["HS256"],
            options={"verify_exp": False},  # Canvas JWTs may not have expiry
        )
    except InvalidTokenError:
        return False
    else:
        return True


def validate_hmac_signature(
    payload_body: bytes,
    secret: SecretStr,
    signature_header: str | None,
) -> bool:
    """Validate HMAC signature for Canvas webhook.

    Supports X-Canvas-Signature and X-Hub-Signature-256 headers.
    Expected format: "sha256=HEX_SIGNATURE" or just HEX_SIGNATURE.
    """
    if not signature_header:
        return False

    # Remove prefix if present
    signature = signature_header.strip().removeprefix("sha256=")

    # Compute HMAC-SHA256
    expected = hmac.new(
        secret.get_secret_value().encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(expected, signature)


def verify_via_canvas_api(
    settings: Settings,
    payload_body: bytes,
    payload: CanvasWebhookPayload | None = None,
) -> WebhookVerificationResult:
    """Verify webhook payload by checking submission exists in Canvas.

    Makes API call to Canvas to verify the submission/assignment IDs
    exist in the configured course.
    """
    success = False
    message = "Canvas API verification failed"
    status_code = HTTPStatus.UNAUTHORIZED.value

    try:
        payload_model = payload or CanvasWebhookPayload.model_validate_json(payload_body)
        event = payload_model.parse_submission_event()

        # Make API call to Canvas
        api_url = str(settings.canvas.api_url)
        token = settings.canvas.token.get_secret_value()
        course_id = settings.canvas.course_id

        # Check submission exists
        headers = {"Authorization": f"Bearer {token}"}
        submission_url = (
            f"{api_url}/api/v1/courses/{course_id}/assignments/"
            f"{event.assignment_id}/submissions/{event.submission_id}"
        )

        response = requests.get(submission_url, headers=headers, timeout=10)
        if response.status_code == HTTPStatus.OK.value:
            success = True
            message = "Canvas API verification succeeded"
            status_code = HTTPStatus.OK.value

    except UnsupportedSubmissionEventError:
        message = "Canvas API verification only supports submission events"
    except ValidationError as exc:
        if payload is None and _is_json_parse_error(exc):
            message = "Webhook payload is not valid JSON"
            status_code = HTTPStatus.BAD_REQUEST.value
        else:
            message = "Webhook payload missing assignment or submission id"
    except requests.RequestException as exc:
        message = f"Canvas API verification error: {exc}"
        status_code = HTTPStatus.BAD_GATEWAY.value

    return WebhookVerificationResult(
        success=success,
        message=message,
        status_code=status_code,
        mode="canvas_api",
    )


def validate_canvas_signature(
    settings: Settings,
    payload_body: bytes,
    headers: WebhookSignatureHeaders,
    payload: CanvasWebhookPayload | None = None,
) -> WebhookVerificationResult:
    """Validate Canvas webhook signature using configured verification mode.

    If webhook_require_jwt is True, validates JWT token from Authorization header.
    Otherwise, validates HMAC when a shared webhook secret is configured. Canvas
    API fallback is only allowed when explicitly enabled.
    """
    if settings.webhook.require_jwt:
        return _jwt_verification_result(settings, headers)

    if settings.webhook.secret is not None:
        return _hmac_verification_result(settings, payload_body, headers)

    if not settings.webhook.allow_canvas_api_fallback:
        return WebhookVerificationResult(
            success=False,
            message=(
                "Webhook verification is not configured; set a webhook secret, "
                "require JWT, or explicitly enable Canvas API fallback"
            ),
            status_code=HTTPStatus.UNAUTHORIZED.value,
            mode="unconfigured",
        )

    if payload is None:
        return verify_via_canvas_api(settings, payload_body)
    return verify_via_canvas_api(settings, payload_body, payload)


def verify_canvas_webhook(
    settings: Settings,
    payload_body: bytes,
    headers: Mapping[str, str],
    payload: CanvasWebhookPayload | None = None,
) -> WebhookVerificationResult:
    """Verify a webhook request using the relevant signature headers."""
    try:
        normalized_headers = {
            str(name).lower(): str(value).strip() for name, value in headers.items()
        }
    except (AttributeError, TypeError):
        return WebhookVerificationResult(
            success=False,
            message="Webhook headers must be key/value string data",
            status_code=HTTPStatus.BAD_REQUEST.value,
            mode="signature",
        )

    if payload is None:
        return validate_canvas_signature(
            settings,
            payload_body,
            WebhookSignatureHeaders.from_headers(normalized_headers),
        )
    return validate_canvas_signature(
        settings,
        payload_body,
        WebhookSignatureHeaders.from_headers(normalized_headers),
        payload=payload,
    )
