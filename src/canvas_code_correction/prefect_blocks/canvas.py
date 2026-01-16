"""Prefect block definitions for course configuration."""

from __future__ import annotations

from prefect.blocks.core import Block
from pydantic import Field, HttpUrl, SecretStr


class CourseConfigBlock(Block):
    """Prefect block encapsulating per-course configuration."""

    _block_type_name = "CCC Course Config"

    canvas_api_url: HttpUrl = Field(default=HttpUrl("https://canvas.instructure.com"))
    canvas_token: SecretStr
    canvas_course_id: int

    asset_bucket_block: str
    asset_path_prefix: str = ""

    workspace_root: str | None = None

    grader_image: str | None = None
    work_pool_name: str | None = None
    grader_env: dict[str, str] = Field(default_factory=dict)

    # Webhook configuration
    webhook_secret: SecretStr | None = Field(
        default=None,
        description="Shared secret for Canvas webhook JWT validation (optional)",
    )
    deployment_name: str | None = Field(
        default=None,
        description="Prefect deployment name for this course (default: ccc-{slug}-deployment)",
    )
    webhook_enabled: bool = Field(
        default=True,
        description="Enable webhook processing for this course",
    )
    webhook_require_jwt: bool = Field(
        default=False,
        description="Require JWT validation for Canvas webhooks (uses webhook_secret)",
    )
