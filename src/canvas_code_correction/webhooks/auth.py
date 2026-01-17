"""Authentication and validation for Canvas webhooks."""

from __future__ import annotations

import hashlib
import hmac
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

import jwt
import requests
from jwt.exceptions import InvalidTokenError

if TYPE_CHECKING:
    from pydantic import SecretStr

    from canvas_code_correction.config import Settings


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
        return True  # noqa: TRY300
    except InvalidTokenError:
        return False


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
) -> bool:
    """Verify webhook payload by checking submission exists in Canvas.

    Makes API call to Canvas to verify the submission/assignment IDs
    exist in the configured course.
    """
    try:
        # Parse payload
        payload = json.loads(payload_body.decode())
        metadata = payload.get("metadata", {})
        body = payload.get("body", {})

        # Extract event type
        event_name = metadata.get("event_name", "")
        if event_name not in ("submission_created", "submission_updated"):
            # Only verify submission events
            return False

        # Extract IDs
        assignment_id = body.get("assignment_id")
        submission_id = body.get("submission_id")
        if not assignment_id or not submission_id:
            return False

        # Convert to integers
        try:
            assignment_id_int = int(assignment_id)
            submission_id_int = int(submission_id)
        except ValueError:
            return False

        # Make API call to Canvas
        api_url = str(settings.canvas.api_url)
        token = settings.canvas.token.get_secret_value()
        course_id = settings.canvas.course_id

        # Check submission exists
        headers = {"Authorization": f"Bearer {token}"}
        submission_url = (
            f"{api_url}/api/v1/courses/{course_id}/assignments/"
            f"{assignment_id_int}/submissions/{submission_id_int}"
        )

        response = requests.get(submission_url, headers=headers, timeout=10)
        return response.status_code == HTTPStatus.OK.value  # noqa: TRY300

    except (json.JSONDecodeError, KeyError, requests.RequestException):
        return False


def validate_canvas_signature(
    settings: Settings,
    payload_body: bytes,
    signature_header: str | None,
) -> bool:
    """Validate Canvas webhook signature using JWT or Canvas API verification.

    If webhook_require_jwt is True, validates JWT token from Authorization header.
    Otherwise, falls back to HMAC signature verification or Canvas API verification.
    """
    # JWT validation
    if settings.webhook.require_jwt:
        if not signature_header:
            return False
        # Extract Bearer token
        if not signature_header.startswith("Bearer "):
            return False
        token = signature_header[7:]  # Remove "Bearer "
        return validate_jwt_token(token, settings.webhook.secret)

    # HMAC signature validation (if secret provided)
    if settings.webhook.secret is not None:
        # Try X-Canvas-Signature first, then X-Hub-Signature-256
        hmac_header = signature_header
        if not hmac_header:
            # Check for X-Canvas-Signature or X-Hub-Signature-256 in additional headers
            # Note: signature_header parameter is currently only Authorization header
            # We need to modify the caller to pass all headers
            return False
        return validate_hmac_signature(
            payload_body,
            settings.webhook.secret,
            hmac_header,
        )

    # Canvas API verification as fallback
    return verify_via_canvas_api(settings, payload_body)


async def verify_canvas_webhook(
    settings: Settings,
    payload_body: bytes,
    headers: dict[str, str],
) -> bool:
    """Async wrapper for Canvas webhook verification."""
    # Extract Authorization header for JWT
    auth_header = headers.get("Authorization")

    # For HMAC verification, we need to check signature headers
    # Currently only passing Authorization header to validate_canvas_signature
    # This needs to be updated to pass appropriate signature header
    # For now, use Authorization header as signature header
    return validate_canvas_signature(settings, payload_body, auth_header)
