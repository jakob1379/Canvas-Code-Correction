"""Prefect flows for webhook-triggered correction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from prefect import flow, task

from canvas_code_correction.config import Settings, resolve_settings_from_block
from canvas_code_correction.flows import (
    CorrectSubmissionPayload,
    correct_submission_flow,
)

if TYPE_CHECKING:
    from pathlib import Path


@task
async def load_course_settings(course_block: str) -> Settings:
    """Load settings from Prefect course configuration block."""
    return resolve_settings_from_block(course_block)


@flow
async def webhook_correction_flow(
    course_block: str,
    assignment_id: int,
    submission_id: int,
    download_dir: Path | None = None,
    dry_run: bool = False,  # noqa: FBT001, FBT002
) -> dict[str, Any]:
    """Prefect flow triggered by Canvas webhooks.

    This flow loads course settings from the specified block and runs
    the standard correction flow for the given submission.
    """
    settings = await load_course_settings(course_block)

    payload = CorrectSubmissionPayload(
        assignment_id=assignment_id,
        submission_id=submission_id,
    )

    # Run the correction flow
    artifacts = correct_submission_flow(
        payload=payload,
        settings=settings,
        download_dir=download_dir,
        dry_run=dry_run,
    )

    # Return a summary of the execution
    return {
        "course_block": course_block,
        "assignment_id": assignment_id,
        "submission_id": submission_id,
        "submission_metadata_keys": list(artifacts.submission_metadata.keys()),
        "downloaded_files_count": len(artifacts.downloaded_files),
        "workspace": str(artifacts.workspace.root) if artifacts.workspace else None,
        "results_keys": list(artifacts.results.keys()),
    }
