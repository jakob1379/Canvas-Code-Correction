"""Authentication and validation for Canvas webhooks."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from http import HTTPStatus
from time import monotonic
from typing import TYPE_CHECKING, Any

import jwt
import requests
from jwt.exceptions import InvalidTokenError, PyJWTError
from pydantic import ValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pydantic import SecretStr

    from canvas_code_correction.config import Settings

from canvas_code_correction.config import WebhookAuthMode
from canvas_code_correction.webhooks.models import (
    CanvasWebhookPayload,
    UnsupportedSubmissionEventError,
)

_ASYMMETRIC_JWT_ALGORITHMS = frozenset({"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"})


@dataclass
class _CachedJwkSet:
    keys: list[dict[str, Any]]
    expires_at: float


_jwk_cache: dict[str, _CachedJwkSet] = {}


class _JwkSetUnavailableError(RuntimeError):
    """Raised when no usable Canvas signing key set can be obtained."""


def clear_jwk_cache() -> None:
    """Clear the process-local JWK cache, primarily for tests."""
    _jwk_cache.clear()


def _fetch_jwks(url: str) -> list[dict[str, Any]]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    document = response.json()
    keys = document.get("keys") if isinstance(document, dict) else None
    if not isinstance(keys, list):
        msg = "Canvas JWK endpoint returned an invalid key set"
        raise TypeError(msg)
    return [key for key in keys if isinstance(key, dict)]


def _matching_jwk(
    url: str,
    kid: str,
    cache_seconds: int,
) -> dict[str, Any] | None:
    cached = _jwk_cache.get(url)
    now = monotonic()
    if cached is not None and cached.expires_at > now:
        match = next((key for key in cached.keys if key.get("kid") == kid), None)
        if match is not None:
            return match

    old_match = None
    if cached is not None:
        old_match = next((key for key in cached.keys if key.get("kid") == kid), None)
    try:
        keys = _fetch_jwks(url)
    except (requests.RequestException, TypeError, ValueError) as exc:
        if old_match is not None:
            return old_match
        msg = "Canvas signing keys are unavailable"
        raise _JwkSetUnavailableError(msg) from exc
    _jwk_cache[url] = _CachedJwkSet(keys=keys, expires_at=now + cache_seconds)
    return next((key for key in keys if key.get("kid") == kid), None)


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
    payload: CanvasWebhookPayload | None = None


def _canvas_signed_jwt_verification_result(  # noqa: PLR0911
    settings: Settings,
    payload_body: bytes,
) -> WebhookVerificationResult:
    """Verify and decode a Canvas Live Events signed request body."""
    invalid_result = WebhookVerificationResult(
        success=False,
        message="Invalid Canvas signed webhook payload",
        status_code=HTTPStatus.UNAUTHORIZED.value,
        mode=WebhookAuthMode.CANVAS_SIGNED_JWT.value,
    )
    try:
        token = payload_body.decode("ascii").strip()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        algorithm = header.get("alg")
        if not isinstance(kid, str) or not kid:
            return invalid_result
        if not isinstance(algorithm, str) or algorithm not in _ASYMMETRIC_JWT_ALGORITHMS:
            return invalid_result
        jwk_data = _matching_jwk(
            str(settings.webhook.canvas_jwks_url),
            kid,
            settings.webhook.canvas_jwks_cache_seconds,
        )
        if jwk_data is None:
            return invalid_result
        if jwk_data.get("alg") not in {None, algorithm}:
            return invalid_result
        key = jwt.PyJWK.from_dict(jwk_data, algorithm=algorithm).key
        claims = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            options={"verify_exp": False},
        )
        payload = CanvasWebhookPayload.model_validate(claims)
    except _JwkSetUnavailableError:
        return WebhookVerificationResult(
            success=False,
            message="Canvas signing keys are temporarily unavailable",
            status_code=HTTPStatus.BAD_GATEWAY.value,
            mode=WebhookAuthMode.CANVAS_SIGNED_JWT.value,
        )
    except (UnicodeDecodeError, PyJWTError, ValidationError):
        return invalid_result
    return WebhookVerificationResult(
        success=True,
        message="Canvas signed JWT verification succeeded",
        status_code=HTTPStatus.OK.value,
        mode=WebhookAuthMode.CANVAS_SIGNED_JWT.value,
        payload=payload,
    )


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
    mode = settings.webhook.effective_auth_mode()
    if mode is WebhookAuthMode.CANVAS_SIGNED_JWT:
        return _canvas_signed_jwt_verification_result(settings, payload_body)
    if mode is WebhookAuthMode.LEGACY_BEARER_JWT:
        return _jwt_verification_result(settings, headers)

    if mode is WebhookAuthMode.HMAC:
        return _hmac_verification_result(settings, payload_body, headers)

    if mode is not WebhookAuthMode.CANVAS_API:
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
