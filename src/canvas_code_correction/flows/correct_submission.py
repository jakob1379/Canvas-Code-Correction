"""Prefect flow for correcting a single Canvas submission."""

from pathlib import Path

from canvasapi.submission import Submission as CanvasSubmission
from prefect import flow, get_run_logger, task

from ..canvas import CanvasClient
from ..config import Settings
from ..result_collector import collect_results
from ..runner_service import RunnerService
from ..submission_store import SubmissionStore
from ..uploader import Uploader

PERSISTED_TASK_OPTIONS = {
    "persist_result": True,
    "result_serializer": "json",
    "cache_result_in_memory": False,
}


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


@task(**PERSISTED_TASK_OPTIONS)
def run_grader_container(workspace: Path, settings: Settings) -> dict[str, object]:
    logger = get_run_logger()
    logger.info(
        "Launching grader container",
        extra={
            "workspace": workspace.as_posix(),
            "image": settings.runner.docker_image,
        },
    )
    service = RunnerService(settings, logger=logger)
    result = service.run(workspace)
    payload = result.as_dict()
    payload["workspace"] = workspace.as_posix()
    return payload


@task(**PERSISTED_TASK_OPTIONS)
def collect_results_task(workspace: Path, runner_payload: dict[str, object]) -> dict[str, object]:
    results = collect_results(workspace, runner_payload)
    return results.as_payload()


@task(**PERSISTED_TASK_OPTIONS)
def upload_feedback_task(
    settings: Settings,
    assignment_id: int,
    submission_id: int,
    collected: dict[str, object],
) -> dict[str, bool]:
    with CanvasClient.from_settings(settings) as client:
        uploader = Uploader(client)
        comment = str(collected.get("comment") or "").strip()
        feedback_zip = collected.get("feedback_zip")
        feedback_path = None
        if feedback_zip:
            feedback_path = Path(str(feedback_zip))
            if not feedback_path.exists():
                raise FileNotFoundError(f"Feedback archive missing at {feedback_path.as_posix()}")
        comment_uploaded, feedback_uploaded = uploader.upload_feedback(
            assignment_id,
            submission_id,
            comment,
            feedback_path,
        )
    return {
        "comment_uploaded": comment_uploaded,
        "feedback_uploaded": feedback_uploaded,
    }


@task(**PERSISTED_TASK_OPTIONS)
def upload_grade_task(
    settings: Settings,
    assignment_id: int,
    submission_id: int,
    collected: dict[str, object],
) -> bool:
    points = float(collected.get("points", 0.0))
    with CanvasClient.from_settings(settings) as client:
        uploader = Uploader(client)
        return uploader.upload_grade(assignment_id, submission_id, points)


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
    runner_payload = run_grader_container(workspace, settings)
    collected = collect_results_task(workspace, runner_payload)
    feedback_outcome = upload_feedback_task(
        settings,
        assignment_id,
        submission_id,
        collected,
    )
    grade_uploaded = upload_grade_task(
        settings,
        assignment_id,
        submission_id,
        collected,
    )

    return {
        "status": runner_payload.get("status", "unknown"),
        "exit_code": runner_payload.get("exit_code"),
        "attachments": [path.as_posix() for path in attachments],
        "submission_files": [path.as_posix() for path in staged_files],
        "submission_id": str(submission.id),
        "points": collected.get("points"),
        "points_breakdown": collected.get("points_breakdown"),
        "comment": collected.get("comment"),
        "feedback_zip": collected.get("feedback_zip"),
        "metadata": collected.get("metadata"),
        "feedback_uploaded": feedback_outcome,
        "grade_uploaded": grade_uploaded,
    }
