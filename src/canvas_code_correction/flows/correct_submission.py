"""Prefect flow for correcting a single Canvas submission."""

from pathlib import Path

from canvasapi.submission import Submission as CanvasSubmission
from prefect import flow, get_run_logger, task

from ..canvas import CanvasClient
from ..config import Settings
from ..runner_service import RunnerService
from ..submission_store import SubmissionStore


@task
def prepare_workspace(settings: Settings, assignment_id: int, submission_id: int) -> Path:
    store = SubmissionStore(settings.working_dir)
    return store.workspace(assignment_id, submission_id)


@task
def fetch_submission(
    settings: Settings,
    assignment_id: int,
    submission_id: int,
) -> CanvasSubmission:
    with CanvasClient.from_settings(settings) as client:
        return client.get_submission(
            assignment_id,
            submission_id,
            include=["attachments"],
        )


@task
def download_submission_attachments(
    settings: Settings,
    submission: CanvasSubmission,
    workspace: Path,
) -> list[Path]:
    store = SubmissionStore(settings.working_dir)
    attachment_dir = store.attachments_dir(workspace)

    saved_paths: list[Path] = []
    with CanvasClient.from_settings(settings) as client:
        for attachment in client.get_submission_files(submission):
            saved_paths.append(client.download_attachment(attachment, attachment_dir))
    return saved_paths


@task
def normalise_submission_workspace(
    settings: Settings,
    workspace: Path,
    attachments: list[Path],
) -> list[Path]:
    store = SubmissionStore(settings.working_dir)
    return store.stage_attachments(workspace, attachments)


@task
def run_grader_container(workspace: Path, settings: Settings) -> dict[str, object]:
    logger = get_run_logger()
    logger.info(
        "Launching grader container",
        extra={
            "workspace": str(workspace),
            "image": settings.runner.docker_image,
        },
    )
    service = RunnerService(settings, logger=logger)
    result = service.run(workspace)
    payload = result.as_dict()
    payload["workspace"] = str(workspace)
    return payload


@flow
def correct_submission_flow(
    assignment_id: int,
    submission_id: int,
    settings: Settings,
) -> dict[str, object]:
    workspace = prepare_workspace(settings, assignment_id, submission_id)
    submission = fetch_submission(settings, assignment_id, submission_id)
    attachments = download_submission_attachments(settings, submission, workspace)
    staged_files = normalise_submission_workspace(settings, workspace, attachments)
    outcome = run_grader_container(workspace, settings)
    outcome["attachments"] = [str(path) for path in attachments]
    outcome["submission_files"] = [str(path) for path in staged_files]
    outcome["submission_id"] = str(submission.id)
    return outcome
