"""Prefect block definitions for course configuration."""

from prefect.blocks.core import Block
from pydantic import Field, HttpUrl, SecretStr


class CourseConfigBlock(Block):
    """Prefect block encapsulating per-course configuration."""

    _block_type_name = "CCC Course Config"

    canvas_api_url: HttpUrl
    canvas_token: SecretStr
    canvas_course_id: int

    asset_bucket_block: str
    asset_path_prefix: str = ""

    workspace_root: str | None = None

    grader_image: str | None = None
    work_pool_name: str | None = None
    grader_env: dict[str, str] = Field(default_factory=dict)
    grader_command: list[str] = Field(default_factory=lambda: ["sh", "main.sh"])
    grader_timeout_seconds: int = 300
    grader_memory_mb: int | None = 512
    grader_upload_check_duplicates: bool = True
    grader_upload_comments: bool = True
    grader_upload_grades: bool = True
    grader_upload_verbose: bool = False

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
    webhook_rate_limit: str = Field(
        default="10/minute",
        description="Rate limit for webhook requests (e.g., '10/minute', '100/hour')",
    )


__all__ = ["CourseConfigBlock"]
