"""Top-level Prefect scaffolding for Canvas correction workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prefect import flow, task

from canvas_code_correction.clients import (
    CanvasResources,
    build_canvas_resources,
)
from canvas_code_correction.collector import ResultCollector
from canvas_code_correction.config import Settings
from canvas_code_correction.runner import (
    GraderConfig,
    GraderExecutor,
    create_default_grader_config,
)
from canvas_code_correction.uploader import CanvasUploader, UploadConfig
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
        candidates.extend(
            [attachment.get("filename"), attachment.get("display_name")],
        )
    else:
        candidates.extend(
            [
                getattr(attachment, "filename", None),
                getattr(attachment, "display_name", None),
            ],
        )

    candidates.extend(
        [
            getattr(file_obj, "filename", None),
            getattr(file_obj, "display_name", None),
        ],
    )

    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate

    identifier = _extract_attachment_id(attachment) or getattr(
        file_obj,
        "id",
        None,
    )
    return f"attachment-{identifier}"


@task
def execute_grader(
    config: GraderConfig,
    workspace: WorkspacePaths,
) -> dict[str, Any]:
    """Run the grader command inside the prepared workspace."""
    executor = GraderExecutor()
    result = executor.execute_in_workspace(
        config=config,
        submission_dir=workspace.submission_dir,
        assets_dir=workspace.assets_dir,
    )

    return {
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "duration_seconds": result.duration_seconds,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "container_id": result.container_id,
    }


@task
def collect_results(
    workspace: WorkspacePaths,
    submission_dir_name: str | None = None,
) -> dict[str, Any]:
    """Collect grader-produced artefacts ready for upload."""
    collector = ResultCollector(workspace.root)
    collection_result = collector.collect(submission_dir_name)

    # Create feedback zip
    feedback_zip = collector.create_feedback_zip(
        collection_result.grading_result,
        workspace.root / "feedback.zip",
    )

    # Validate results
    issues = collector.validate_result(collection_result.grading_result)

    return {
        "points": collection_result.grading_result.points,
        "comments": collection_result.grading_result.comments,
        "points_file_content": collection_result.grading_result.points_file_content,
        "feedback_zip_path": str(feedback_zip),
        "artifacts_zip_path": (
            str(collection_result.grading_result.artifacts_zip_path)
            if collection_result.grading_result.artifacts_zip_path
            else None
        ),
        "errors_log_path": (
            str(collection_result.grading_result.errors_log_path)
            if collection_result.grading_result.errors_log_path
            else None
        ),
        "discovered_files": [str(f) for f in collection_result.discovered_files],
        "validation_issues": issues,
        "metadata": collection_result.grading_result.metadata,
    }


@task
def upload_feedback(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    results: dict[str, Any],
    config: UploadConfig | None = None,
) -> dict[str, Any]:
    """Upload comments or feedback files back to Canvas."""
    config = config or UploadConfig()
    feedback_zip_path = results.get("feedback_zip_path")
    if not feedback_zip_path:
        return {
            "success": False,
            "message": "No feedback zip path in results",
            "upload_result": None,
        }

    uploader = CanvasUploader(
        resources.course.get_assignment(payload.assignment_id).get_submission(
            payload.submission_id,
        ),
    )

    upload_result = uploader.upload_feedback(Path(feedback_zip_path), config)

    return {
        "success": upload_result.success,
        "message": upload_result.message,
        "duplicate": upload_result.duplicate,
        "comment_posted": upload_result.comment_posted,
        "details": upload_result.details,
    }


@task
def post_grade(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    results: dict[str, Any],
    config: UploadConfig | None = None,
) -> dict[str, Any]:
    """Post the grade associated with the submission."""
    config = config or UploadConfig()
    points = results.get("points")
    if points is None:
        return {
            "success": False,
            "message": "No points in results",
            "grade_result": None,
        }

    uploader = CanvasUploader(
        resources.course.get_assignment(payload.assignment_id).get_submission(
            payload.submission_id,
        ),
    )

    # For now, upload raw points. Could be enhanced to support
    # complete/incomplete or percentage grading based on course config
    upload_result = uploader.upload_grade(str(points), config)

    return {
        "success": upload_result.success,
        "message": upload_result.message,
        "duplicate": upload_result.duplicate,
        "grade_posted": upload_result.grade_posted,
        "details": upload_result.details,
    }


@flow
def correct_submission_flow(
    payload: CorrectSubmissionPayload,
    settings: Settings,
    *,
    download_dir: Path | None = None,
    dry_run: bool = False,
) -> FlowArtifacts:
    """Prefect flow orchestrating the CCC correction stages."""
    resources = build_canvas_resources(settings)
    metadata = fetch_submission_metadata(resources, payload)

    if download_dir is None:
        raise NotImplementedError("download directory must be provided")

    downloaded = download_submission_files(resources, payload, download_dir)
    workspace = prepare_workspace_task(resources, payload, downloaded)

    # Create grader configuration from settings
    grader_config = create_default_grader_config(
        docker_image=settings.grader.docker_image or "jakob1379/canvas-grader:latest",
        command=["sh", "main.sh"],  # Default command, could be configurable
        timeout_seconds=300,
        memory_mb=512,
    )

    # Execute grader
    execution_result = execute_grader(grader_config, workspace)

    # Collect results
    results = collect_results(workspace)

    # Upload feedback
    upload_config = UploadConfig(
        check_duplicates=True,
        upload_comments=True,
        upload_grades=True,
        dry_run=dry_run,
        verbose=False,
    )
    feedback_result = upload_feedback(
        resources,
        payload,
        results,
        upload_config,
    )

    # Post grade
    grade_result = post_grade(resources, payload, results, upload_config)

    # Return aggregated artifacts
    return FlowArtifacts(
        submission_metadata=metadata,
        downloaded_files=downloaded,
        workspace=workspace,
        results={
            "execution": execution_result,
            "collection": results,
            "feedback_upload": feedback_result,
            "grade_upload": grade_result,
        },
        uploads={
            "feedback": feedback_result,
            "grade": grade_result,
        },
    )
