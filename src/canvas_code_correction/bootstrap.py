"""Boundary helpers for loading runtime configuration from external systems."""

from http import HTTPStatus
from pathlib import Path
from typing import Final, cast

from prefect.client.orchestration import get_client
from prefect.exceptions import PrefectHTTPStatusError

from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WebhookSettings,
    WorkspaceSettings,
    _default_workspace_root,
)
from canvas_code_correction.prefect_blocks.canvas import CourseConfigBlock

BLOCK_DOCUMENT_PAGE_SIZE: Final[int] = 200


class CourseBlockLoadError(RuntimeError):
    """Raised when a course block cannot be loaded into application settings."""

    def __init__(
        self,
        block_name: str,
        reason: str,
        *,
        cause: Exception | None = None,
    ) -> None:
        """Store the block name, user-facing reason, and original exception."""
        self.block_name = block_name
        self.reason = reason
        self.cause = cause
        super().__init__(f"Unable to load course block '{block_name}': {reason}")


def load_course_block(block_name: str) -> CourseConfigBlock:
    """Load a typed Prefect course block."""
    try:
        return cast("CourseConfigBlock", CourseConfigBlock.load(block_name))
    except Exception as exc:
        raise CourseBlockLoadError(block_name, str(exc), cause=exc) from exc


def find_course_block_names() -> list[str]:
    """Return every available course block name.

    Returns an empty list when the block type has never been registered, which is
    the state of a fresh install before the first `ccc course setup`.
    """
    block_type_slug = CourseConfigBlock.get_block_type_slug()
    names: list[str] = []
    offset = 0
    with get_client(sync_client=True) as client:
        while True:
            try:
                page = client.read_block_documents_by_type(
                    block_type_slug=block_type_slug,
                    include_secrets=False,
                    offset=offset,
                    limit=BLOCK_DOCUMENT_PAGE_SIZE,
                )
            except PrefectHTTPStatusError as exc:
                if exc.response.status_code != HTTPStatus.NOT_FOUND:
                    raise
                return []

            # Anonymous block documents have no name and are not selectable courses.
            names.extend(str(doc.name) for doc in page if doc.name)
            offset += len(page)
            if len(page) < BLOCK_DOCUMENT_PAGE_SIZE:
                return sorted(names)


def load_settings_from_course_block(block_name: str) -> Settings:
    """Load application settings from a Prefect course block."""
    block = load_course_block(block_name)
    workspace_root = (
        Path(block.workspace_root).expanduser()
        if block.workspace_root
        else _default_workspace_root()
    )
    return Settings(
        canvas=CanvasSettings(
            api_url=block.canvas_api_url,
            token=block.canvas_token,
            course_id=block.canvas_course_id,
        ),
        assets=CourseAssetsSettings(
            bucket_block=block.asset_bucket_block,
            path_prefix=block.asset_path_prefix,
            assignment_path_prefixes=dict(block.assignment_asset_prefixes),
            storage_auth_mode=block.storage_auth_mode,
        ),
        grader=GraderSettings(
            docker_image=block.grader_image,
            work_pool_name=block.work_pool_name,
            env=dict(block.grader_env),
            command=list(block.grader_command),
            timeout_seconds=block.grader_timeout_seconds,
            memory_mb=block.grader_memory_mb,
            upload_check_duplicates=block.grader_upload_check_duplicates,
            upload_comments=block.grader_upload_comments,
            upload_grades=block.grader_upload_grades,
            upload_verbose=block.grader_upload_verbose,
        ),
        workspace=WorkspaceSettings(root=workspace_root),
        webhook=WebhookSettings(
            secret=block.webhook_secret,
            deployment_name=block.deployment_name,
            enabled=block.webhook_enabled,
            require_jwt=block.webhook_require_jwt,
            rate_limit=block.webhook_rate_limit,
        ),
    )
