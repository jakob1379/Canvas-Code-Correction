"""Prefect flow for correcting a single Canvas submission."""

from __future__ import annotations

import logging
from pathlib import Path

from prefect import flow, get_run_logger

from ..config import Settings


def prepare_workspace(settings: Settings, assignment_id: int, submission_id: int) -> Path:
    workspace = settings.working_dir / str(assignment_id) / str(submission_id)
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def run_grader_container(workspace: Path, settings: Settings) -> dict[str, str]:
    try:
        logger = get_run_logger()
    except RuntimeError:
        logger = logging.getLogger("canvas_code_correction")
    logger.info(
        "Launching grader container",
        extra={
            "workspace": str(workspace),
            "image": settings.runner.docker_image,
        },
    )
    return {
        "workspace": str(workspace),
        "image": settings.runner.docker_image,
        "status": "pending",
    }


@flow
def correct_submission_flow(
    assignment_id: int,
    submission_id: int,
    settings: Settings,
) -> dict[str, str]:
    workspace = prepare_workspace(settings, assignment_id, submission_id)
    outcome = run_grader_container(workspace, settings)
    return outcome
