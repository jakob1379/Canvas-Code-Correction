"""Configuration helpers for Canvas Code Correction."""

import tempfile
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl, SecretStr

CANVAS_LIVE_EVENTS_JWKS_URL = "https://8axpcl50e4.execute-api.us-east-1.amazonaws.com/main/jwks"


class WebhookAuthMode(StrEnum):
    """Supported webhook authentication mechanisms."""

    CANVAS_SIGNED_JWT = "canvas-signed-jwt"
    HMAC = "hmac"
    LEGACY_BEARER_JWT = "legacy-bearer-jwt"
    CANVAS_API = "canvas-api"


def _default_workspace_root() -> Path:
    return Path(tempfile.gettempdir()) / "ccc" / "workspaces"


class CanvasSettings(BaseModel):
    """Canvas API connection settings."""

    api_url: HttpUrl
    token: SecretStr
    course_id: int


class CourseAssetsSettings(BaseModel):
    """Course assets storage settings."""

    bucket_block: str
    path_prefix: str = ""


class GraderSettings(BaseModel):
    """Grader execution settings."""

    docker_image: str | None = None
    work_pool_name: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    command: list[str] = Field(default_factory=lambda: ["sh", "/workspace/assets/main.sh"])
    timeout_seconds: int = 300
    memory_mb: int | None = 512
    upload_check_duplicates: bool = True
    upload_comments: bool = True
    upload_grades: bool = True
    upload_verbose: bool = False


class WorkspaceSettings(BaseModel):
    """Workspace directory settings."""

    root: Path = Field(
        default_factory=_default_workspace_root,
        description=(
            "Root directory for grading workspaces. "
            "If placed under a world-writable parent (e.g., /tmp), "
            "the system will enforce restrictive permissions (0o700). "
            "Consider using a user-private location (e.g., ~/.ccc/workspaces) "
            "in production."
        ),
    )


class WebhookSettings(BaseModel):
    """Canvas webhook configuration settings."""

    secret: SecretStr | None = Field(
        default=None,
        description="Shared secret for Canvas webhook JWT validation (optional)",
    )
    deployment_name: str | None = Field(
        default=None,
        description="Prefect deployment name for this course (default: ccc-{slug}-deployment)",
    )
    enabled: bool = Field(
        default=True,
        description="Enable webhook processing for this course",
    )
    require_jwt: bool = Field(
        default=False,
        description="Require JWT validation for Canvas webhooks (uses secret)",
    )
    rate_limit: str = Field(
        default="10/minute",
        description="Rate limit for webhook requests (e.g., '10/minute', '100/hour')",
    )
    allow_canvas_api_fallback: bool = Field(
        default=False,
        description=(
            "Allow webhook requests without JWT/HMAC signatures to fall back to "
            "Canvas API existence checks. Disabled by default because it weakens "
            "request authentication."
        ),
    )
    auth_mode: WebhookAuthMode | None = Field(
        default=None,
        description="Explicit authentication mode; omitted preserves legacy configuration",
    )
    canvas_jwks_url: HttpUrl = Field(default=CANVAS_LIVE_EVENTS_JWKS_URL, validate_default=True)
    canvas_jwks_cache_seconds: int = Field(default=3600, gt=0)

    def effective_auth_mode(self) -> WebhookAuthMode | None:
        """Resolve explicit mode or the equivalent legacy configuration."""
        if self.auth_mode is not None:
            return self.auth_mode
        if self.require_jwt:
            return WebhookAuthMode.LEGACY_BEARER_JWT
        if self.secret is not None:
            return WebhookAuthMode.HMAC
        if self.allow_canvas_api_fallback:
            return WebhookAuthMode.CANVAS_API
        return None


class Settings(BaseModel):
    """Aggregated settings for a course configuration."""

    canvas: CanvasSettings
    assets: CourseAssetsSettings
    grader: GraderSettings
    workspace: WorkspaceSettings
    webhook: WebhookSettings = Field(default_factory=WebhookSettings)

    def to_flow_payload(self) -> dict[str, object]:
        """Return a JSON-safe payload consumed by webhook-bound Prefect flows."""
        payload = self.model_dump(mode="json")
        payload["canvas"]["token"] = self.canvas.token.get_secret_value()
        payload["webhook"]["secret"] = (
            self.webhook.secret.get_secret_value() if self.webhook.secret else None
        )
        return payload
