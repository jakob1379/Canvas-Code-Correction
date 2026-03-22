"""Top-level Prefect scaffolding for Canvas correction workflows."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from prefect import flow, task

from canvas_code_correction.clients.canvas_resources import (
    CanvasResources,
    build_canvas_resources,
)
from canvas_code_correction.collector import CanvasMetadataValue, ResultCollector
from canvas_code_correction.runner import (
    GraderConfig,
    GraderExecutor,
    create_default_grader_config,
)
from canvas_code_correction.uploader import (
    UploadConfig,
    UploadDetailValue,
    create_uploader_from_resources,
)
from canvas_code_correction.workspace import (
    WorkspaceConfig,
    WorkspacePaths,
    prepare_workspace,
)

if TYPE_CHECKING:
    from canvas_code_correction.config import Settings


@dataclass(frozen=True)
class CorrectSubmissionPayload:
    """Inputs required for the correction flow."""

    assignment_id: int
    submission_id: int
    workspace_id: str | None = None


@dataclass(frozen=True)
class FlowArtifacts:
    """Aggregated outputs produced by the correction flow."""

    submission_metadata: SubmissionMetadata
    downloaded_files: list[Path]
    workspace: WorkspacePaths | None
    results: CorrectionResults
    uploads: CorrectionUploads


@dataclass(frozen=True)
class SubmissionMetadata:
    """Serializable submission context fetched from Canvas."""

    assignment: dict[str, CanvasMetadataValue]
    submission: dict[str, CanvasMetadataValue]

    def keys(self) -> tuple[str, str]:
        """Return metadata tuple keys used for serialization."""
        return ("assignment", "submission")


@dataclass(frozen=True)
class ExecutionSummary:
    """Normalized grader execution details."""

    exit_code: int
    timed_out: bool
    duration_seconds: float
    stdout: str
    stderr: str
    container_id: str | None


@dataclass(frozen=True)
class CollectedResults:
    """Normalized artifacts collected after grading."""

    points: float | int | str | None
    comments: str | None
    points_file_content: str
    feedback_zip_path: Path | None
    artifacts_zip_path: Path | None
    errors_log_path: Path | None
    discovered_files: list[Path]
    validation_issues: list[str]
    metadata: dict[str, CanvasMetadataValue]


@dataclass(frozen=True)
class FeedbackUploadResult:
    """Outcome of uploading feedback artifacts to Canvas."""

    success: bool
    message: str
    duplicate: bool
    comment_posted: bool
    details: dict[str, UploadDetailValue] | None


@dataclass(frozen=True)
class GradeUploadResult:
    """Outcome of posting the grade to Canvas."""

    success: bool
    message: str
    duplicate: bool
    grade_posted: bool
    details: dict[str, UploadDetailValue] | None


class SubmissionAttachment(Protocol):
    """Protocol for a submission attachment reference."""

    id: int | str | None
    filename: str | None
    display_name: str | None


@dataclass(frozen=True)
class CorrectionResults:
    """Typed outputs from each correction stage."""

    execution: ExecutionSummary
    collection: CollectedResults
    feedback_upload: FeedbackUploadResult
    grade_upload: GradeUploadResult

    def keys(self) -> tuple[str, str, str, str]:
        """Return result tuple keys used for serialization."""
        return ("execution", "collection", "feedback_upload", "grade_upload")


@dataclass(frozen=True)
class CorrectionUploads:
    """Subset of final upload outcomes."""

    feedback: FeedbackUploadResult
    grade: GradeUploadResult


def _resolve_download_dir(download_dir: Path | None) -> Path:
    """Return a usable download directory for the correction flow."""
    if download_dir is not None:
        return download_dir
    return Path(tempfile.mkdtemp(prefix="ccc-download-"))


def _resolve_grader_config(
    settings: Settings,
    grader_config: GraderConfig | None = None,
) -> GraderConfig:
    if grader_config is not None:
        return grader_config

    return create_default_grader_config(
        docker_image=settings.grader.docker_image or "jakob1379/canvas-grader:latest",
        command=list(settings.grader.command),
        timeout_seconds=settings.grader.timeout_seconds,
        memory_mb=settings.grader.memory_mb,
    )


def _resolve_upload_config(
    settings: Settings,
    *,
    dry_run: bool,
    upload_config: UploadConfig | None = None,
) -> UploadConfig:
    if upload_config is not None:
        return upload_config

    return UploadConfig(
        check_duplicates=settings.grader.upload_check_duplicates,
        upload_comments=settings.grader.upload_comments,
        upload_grades=settings.grader.upload_grades,
        dry_run=dry_run,
        verbose=settings.grader.upload_verbose,
    )


@task
def fetch_submission_metadata(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
) -> SubmissionMetadata:
    """Retrieve metadata for the submission under correction.

    Prefect will handle retries and logging around this task.
    """
    return _fetch_submission_metadata(resources, payload)


def _fetch_submission_metadata(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
) -> SubmissionMetadata:
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

    return SubmissionMetadata(
        assignment=_canvas_object_to_dict(assignment),
        submission=_canvas_object_to_dict(submission),
    )


def _canvas_object_to_dict(obj: object) -> dict[str, CanvasMetadataValue]:
    if hasattr(obj, "attributes"):
        attributes = obj.attributes
        if isinstance(attributes, dict) and attributes:
            return _filter_canvas_value_dict(attributes)

    raw = getattr(obj, "__dict__", {})
    return _filter_canvas_value_dict(raw)


def _filter_canvas_value_dict(raw: object) -> dict[str, CanvasMetadataValue]:
    if not isinstance(raw, dict):
        return {}

    result: dict[str, CanvasMetadataValue] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or key.startswith("_"):
            continue

        filtered_value = _to_canvas_json_value(value)
        if filtered_value is not None:
            result[key] = filtered_value

    return result


def _to_canvas_json_value(value: object) -> CanvasMetadataValue | None:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    if isinstance(value, list) and all(
        isinstance(item, (str, int, float, bool)) or item is None for item in value
    ):
        return cast("CanvasMetadataValue", value)

    if isinstance(value, dict) and all(
        isinstance(map_key, str)
        and (isinstance(map_value, (str, int, float, bool)) or map_value is None)
        for map_key, map_value in value.items()
    ):
        return cast("CanvasMetadataValue", value)

    return None


@task
def download_submission_files(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    destination: Path,
) -> list[Path]:
    """Download submission attachments into the provided destination."""
    return _download_submission_files(resources, payload, destination)


def _download_submission_files(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    destination: Path,
) -> list[Path]:
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
    config = WorkspaceConfig(
        workspace_root=resources.settings.workspace.root,
        bucket_block=resources.settings.assets.bucket_block,
        path_prefix=resources.settings.assets.path_prefix,
        assignment_id=payload.assignment_id,
        submission_id=payload.submission_id,
    )
    return prepare_workspace(config, submission_files)


def _extract_attachment_id(attachment: SubmissionAttachment | dict[str, object]) -> int | None:
    if isinstance(attachment, dict):
        attachment_dict = cast("dict[str, object]", attachment)
        value = attachment_dict.get("id")
    else:
        value = getattr(attachment, "id", None)

    if value is None:
        return None

    if not isinstance(value, (str, int, float, bool)):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_attachment_name(
    attachment: SubmissionAttachment | dict[str, object],
    file_obj: object,
) -> str:
    candidates = []

    if isinstance(attachment, dict):
        attachment_dict = cast("dict[str, object]", attachment)
        candidates.extend(
            [attachment_dict.get("filename"), attachment_dict.get("display_name")],
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
) -> ExecutionSummary:
    """Run the grader command inside the prepared workspace."""
    executor = GraderExecutor()
    result = executor.execute_in_workspace(
        config=config,
        submission_dir=workspace.submission_dir,
        assets_dir=workspace.assets_dir,
    )

    return ExecutionSummary(
        exit_code=result.exit_code,
        timed_out=result.timed_out,
        duration_seconds=result.duration_seconds,
        stdout=result.stdout,
        stderr=result.stderr,
        container_id=result.container_id,
    )


@task
def collect_results(
    workspace: WorkspacePaths,
    submission_dir_name: str | None = None,
) -> CollectedResults:
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

    metadata = cast(
        "dict[str, CanvasMetadataValue]",
        collection_result.grading_result.metadata.model_dump(),
    )

    return CollectedResults(
        points=collection_result.grading_result.points,
        comments=collection_result.grading_result.comments,
        points_file_content=collection_result.grading_result.points_file_content,
        feedback_zip_path=feedback_zip,
        artifacts_zip_path=collection_result.grading_result.artifacts_zip_path,
        errors_log_path=collection_result.grading_result.errors_log_path,
        discovered_files=list(collection_result.discovered_files),
        validation_issues=list(issues),
        metadata=metadata,
    )


@task
def upload_feedback(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    results: CollectedResults,
    config: UploadConfig | None = None,
) -> FeedbackUploadResult:
    """Upload comments or feedback files back to Canvas."""
    config = config or UploadConfig()
    if not results.feedback_zip_path:
        return FeedbackUploadResult(
            success=False,
            message="No feedback zip path in results",
            duplicate=False,
            comment_posted=False,
            details=None,
        )

    uploader = create_uploader_from_resources(
        resources,
        payload.assignment_id,
        payload.submission_id,
    )

    upload_result = uploader.upload_feedback(results.feedback_zip_path, config)

    return FeedbackUploadResult(
        success=upload_result.success,
        message=upload_result.message,
        duplicate=upload_result.duplicate,
        comment_posted=upload_result.comment_posted,
        details=upload_result.details,
    )


@task
def post_grade(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    results: CollectedResults,
    config: UploadConfig | None = None,
) -> GradeUploadResult:
    """Post the grade associated with the submission."""
    config = config or UploadConfig()
    if results.points is None:
        return GradeUploadResult(
            success=False,
            message="No points in results",
            duplicate=False,
            grade_posted=False,
            details=None,
        )

    uploader = create_uploader_from_resources(
        resources,
        payload.assignment_id,
        payload.submission_id,
    )

    # For now, upload raw points. Could be enhanced to support
    # complete/incomplete or percentage grading based on course config
    upload_result = uploader.upload_grade(str(results.points), config)

    return GradeUploadResult(
        success=upload_result.success,
        message=upload_result.message,
        duplicate=upload_result.duplicate,
        grade_posted=upload_result.grade_posted,
        details=upload_result.details,
    )


@flow
def correct_submission_flow(
    payload: CorrectSubmissionPayload,
    settings: Settings,
    *,
    resources: CanvasResources | None = None,
    download_dir: Path | None = None,
    dry_run: bool = False,
) -> FlowArtifacts:
    """Prefect flow orchestrating the CCC correction stages."""
    resources = resources or build_canvas_resources(settings)
    metadata = fetch_submission_metadata(resources, payload)

    download_dir = _resolve_download_dir(download_dir)

    downloaded = download_submission_files(resources, payload, download_dir)
    workspace = prepare_workspace_task(resources, payload, downloaded)

    resolved_grader_config = _resolve_grader_config(
        settings,
    )
    resolved_upload_config = _resolve_upload_config(
        settings,
        dry_run=dry_run,
    )

    execution_result = execute_grader(resolved_grader_config, workspace)
    results = collect_results(workspace)
    feedback_result = upload_feedback(
        resources,
        payload,
        results,
        resolved_upload_config,
    )
    grade_result = post_grade(
        resources,
        payload,
        results,
        resolved_upload_config,
    )
    return FlowArtifacts(
        submission_metadata=metadata,
        downloaded_files=downloaded,
        workspace=workspace,
        results=CorrectionResults(
            execution=execution_result,
            collection=results,
            feedback_upload=feedback_result,
            grade_upload=grade_result,
        ),
        uploads=CorrectionUploads(
            feedback=feedback_result,
            grade=grade_result,
        ),
    )
