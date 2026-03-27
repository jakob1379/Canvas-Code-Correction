"""Prefect flows for webhook-triggered correction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from prefect import flow
from pydantic import BaseModel

from canvas_code_correction.config import Settings
from canvas_code_correction.flows.correction import (
    CorrectSubmissionPayload,
    correct_submission_flow,
)


@dataclass(frozen=True)
class WebhookCourseContext:
    """Course-scoped inputs shared across webhook-triggered runs."""

    course_block: str
    settings: dict[str, object]

    @classmethod
    def _from_mapping(cls, value: Mapping[str, object]) -> WebhookCourseContext:
        settings = cast("Mapping[str, object]", value["settings"])
        return cls(
            course_block=str(value["course_block"]),
            settings=dict(settings),
        )

    @classmethod
    def from_value(cls, value: WebhookCourseContext | Mapping[str, object]) -> WebhookCourseContext:
        """Normalize Prefect-serialized input into a dataclass instance."""
        if isinstance(value, cls):
            return value
        return cls._from_mapping(cast("Mapping[str, object]", value))


class WebhookSubmissionPayloadModel(BaseModel):
    """Validated webhook submission payload accepted by the flow boundary."""

    assignment_id: int
    submission_id: int
    workspace_id: str | None = None


def _coerce_submission_payload(
    submission: CorrectSubmissionPayload | Mapping[str, object],
) -> CorrectSubmissionPayload:
    if isinstance(submission, CorrectSubmissionPayload):
        return submission
    if not isinstance(submission, Mapping):
        msg = "submission must be a mapping or CorrectSubmissionPayload"
        raise TypeError(msg)

    validated_submission = WebhookSubmissionPayloadModel.model_validate(submission)
    return CorrectSubmissionPayload(
        assignment_id=validated_submission.assignment_id,
        submission_id=validated_submission.submission_id,
        workspace_id=validated_submission.workspace_id,
    )


@dataclass(frozen=True)
class WebhookFlowSummary:
    """Normalized summary returned by the webhook-triggered flow."""

    course_block: str
    assignment_id: int
    submission_id: int
    submission_metadata_keys: list[str]
    downloaded_files_count: int
    workspace: str | None
    results_keys: list[str]


@flow
def webhook_correction_flow(
    course: WebhookCourseContext | Mapping[str, object],
    submission: CorrectSubmissionPayload | Mapping[str, object],
    download_dir: Path | None = None,
    *,
    dry_run: bool = False,
) -> WebhookFlowSummary:
    """Prefect flow triggered by Canvas webhooks.

    This flow receives already-loaded settings and runs the standard
    correction flow for the given submission.
    """
    download_dir = Path(download_dir) if download_dir is not None else None
    course_context = WebhookCourseContext.from_value(course)
    submission_payload = _coerce_submission_payload(submission)

    # Run the correction flow
    artifacts = correct_submission_flow(
        payload=submission_payload,
        settings=Settings.model_validate(course_context.settings),
        download_dir=download_dir,
        dry_run=dry_run,
    )

    # Return a summary of the execution
    return WebhookFlowSummary(
        course_block=course_context.course_block,
        assignment_id=submission_payload.assignment_id,
        submission_id=submission_payload.submission_id,
        submission_metadata_keys=list(artifacts.submission_metadata.keys()),
        downloaded_files_count=len(artifacts.downloaded_files),
        workspace=str(artifacts.workspace.root) if artifacts.workspace else None,
        results_keys=list(artifacts.results.keys()),
    )
