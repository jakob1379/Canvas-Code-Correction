"""Top-level Prefect scaffolding for Canvas correction workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prefect import flow, task

from canvas_code_correction.clients import CanvasResources, build_canvas_resources
from canvas_code_correction.config import Settings
from canvas_code_correction.workspace import (
    WorkspacePaths,
    build_workspace_config,
    prepare_workspace,
)


@dataclass(frozen=True)
class CorrectSubmissionPayload:
    """Inputs required for the correction flow."""

    assignment_id: int
    submission_id: int
    workspace_id: str | None = None


@dataclass(frozen=True)
class FlowArtifacts:
    """Aggregated outputs produced by the correction flow."""

    submission_metadata: dict[str, Any]
    downloaded_files: list[Path]
    workspace: WorkspacePaths | None
    results: dict[str, Any]
    uploads: dict[str, Any]


@task
def fetch_submission_metadata(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
) -> dict[str, Any]:
    """Retrieve metadata for the submission under correction.

    Prefect will handle retries and logging around this task.
    """
    assignment = resources.course.get_assignment(payload.assignment_id)
    submission = assignment.get_submission(
        payload.submission_id,
        include=[
            "submission_comments",
            "submission_history",
            "full_rubric_assessment",
            "rubric_assessment",
        ],
    )

    return {
        "assignment": _canvas_object_to_dict(assignment),
        "submission": _canvas_object_to_dict(submission),
    }


def _canvas_object_to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "attributes"):
        attributes = obj.attributes
        if isinstance(attributes, dict) and attributes:
            return attributes

    raw = getattr(obj, "__dict__", {})
    result: dict[str, Any] = {}
    for key, value in raw.items():
        if key.startswith("_"):
            continue
        result[key] = value
    return result


@task
def download_submission_files(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    destination: Path,
) -> list[Path]:
    """Download submission attachments into the provided destination."""
    destination.mkdir(parents=True, exist_ok=True)

    assignment = resources.course.get_assignment(payload.assignment_id)
    submission = assignment.get_submission(payload.submission_id)

    attachments = getattr(submission, "attachments", None) or []
    downloaded_files: list[Path] = []

    for attachment in attachments:
        attachment_id = _extract_attachment_id(attachment)
        if attachment_id is None:
            continue

        file_obj = resources.canvas.get_file(attachment_id)
        filename = _resolve_attachment_name(attachment, file_obj)
        local_path = destination / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)
        file_obj.download(local_path.as_posix())
        downloaded_files.append(local_path)

    return downloaded_files


@task
def prepare_workspace_task(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    submission_files: list[Path],
) -> WorkspacePaths:
    """Materialize a workspace that combines submission files with course assets."""

    config = build_workspace_config(
        resources.settings,
        assignment_id=payload.assignment_id,
        submission_id=payload.submission_id,
    )
    return prepare_workspace(config, submission_files)


def _extract_attachment_id(attachment: Any) -> int | None:
    if isinstance(attachment, dict):
        value = attachment.get("id")
        return int(value) if value is not None else None
    return getattr(attachment, "id", None)


def _resolve_attachment_name(attachment: Any, file_obj: Any) -> str:
    candidates = []

    if isinstance(attachment, dict):
        candidates.extend([attachment.get("filename"), attachment.get("display_name")])
    else:
        candidates.extend(
            [getattr(attachment, "filename", None), getattr(attachment, "display_name", None)]
        )

    candidates.extend(
        [getattr(file_obj, "filename", None), getattr(file_obj, "display_name", None)]
    )

    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate

    identifier = _extract_attachment_id(attachment) or getattr(file_obj, "id", "attachment")
    return f"attachment-{identifier}"


@task
def execute_grader(
    payload: CorrectSubmissionPayload,
    working_dir: Path,
) -> dict[str, Any]:
    """Run the grader command inside the prepared workspace."""

    raise NotImplementedError


@task
def collect_results(
    working_dir: Path,
) -> dict[str, Any]:
    """Collect grader-produced artefacts ready for upload."""

    raise NotImplementedError


@task
def upload_feedback(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    results: dict[str, Any],
) -> dict[str, Any]:
    """Upload comments or feedback files back to Canvas."""

    raise NotImplementedError


@task
def post_grade(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    results: dict[str, Any],
) -> dict[str, Any]:
    """Post the grade associated with the submission."""

    raise NotImplementedError


@flow
def correct_submission_flow(
    payload: CorrectSubmissionPayload,
    settings: Settings,
    *,
    download_dir: Path | None = None,
) -> FlowArtifacts:
    """Prefect flow orchestrating the CCC correction stages."""
    resources = build_canvas_resources(settings)
    metadata = fetch_submission_metadata(resources, payload)

    if download_dir is None:
        raise NotImplementedError("download directory must be provided")

    downloaded = download_submission_files(resources, payload, download_dir)
    workspace = prepare_workspace_task(resources, payload, downloaded)

    raise NotImplementedError
