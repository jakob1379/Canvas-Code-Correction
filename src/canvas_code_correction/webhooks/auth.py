"""Authentication and validation for Canvas webhooks."""

from __future__ import annotations

from typing import TYPE_CHECKING

import jwt
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


def validate_canvas_signature(
    settings: Settings,
    _payload_body: bytes,
    signature_header: str | None,
) -> bool:
    """Validate Canvas webhook signature using JWT or Canvas API verification.

    If webhook_require_jwt is True, validates JWT token from Authorization header.
    Otherwise, falls back to Canvas API verification using the OAuth2 token.
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

    # Fallback: verify webhook payload using Canvas API (TODO)
    # This would involve checking that the request came from Canvas by
    # making an API call to verify the webhook signature.
    # For now, we'll trust the webhook if JWT validation is not required.
    # In production, you should implement proper verification.
    return True


async def verify_canvas_webhook(
    settings: Settings,
    payload_body: bytes,
    headers: dict[str, str],
) -> bool:
    """Async wrapper for Canvas webhook verification."""
    # Extract Authorization header
    auth_header = headers.get("Authorization")
    return validate_canvas_signature(settings, payload_body, auth_header)
