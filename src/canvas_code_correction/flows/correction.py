"""Top-level Prefect scaffolding for Canvas correction workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from prefect import flow, task

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from canvas_code_correction.clients import CanvasResources
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

    submission_metadata: dict[str, Any]
    downloaded_files: list[Path]
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

    raise NotImplementedError


@task
def download_submission_files(
    resources: CanvasResources,
    payload: CorrectSubmissionPayload,
    destination: Path,
) -> list[Path]:
    """Download submission attachments into the provided destination."""

    raise NotImplementedError


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
) -> FlowArtifacts:
    """Prefect flow orchestrating the CCC correction stages."""

    raise NotImplementedError
