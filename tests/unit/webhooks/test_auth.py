"""Unit tests for webhook authentication."""

from __future__ import annotations

from unittest.mock import patch

import jwt.exceptions
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WebhookSettings,
    WorkspaceSettings,
)
from canvas_code_correction.webhooks.auth import validate_jwt_token


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

    # When JWT not required, validation passes (for now)
    result = validate_canvas_signature(
        settings,
        b"payload",
        None,
    )
    assert result is True
