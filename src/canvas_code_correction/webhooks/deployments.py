"""Proper deployment management for webhook-triggered flows using Prefect 3.x deployment patterns."""

from __future__ import annotations

import logging
from typing import Any

from prefect.deployments.flow_runs import run_deployment

from canvas_code_correction.config import Settings
from canvas_code_correction.webhooks.flows import webhook_correction_flow

logger = logging.getLogger(__name__)


def get_deployment_name(settings: Settings, course_block: str) -> str:
    """Get deployment name for a course block."""
    if settings.webhook.deployment_name:
        return settings.webhook.deployment_name

    # Default: ccc-{slug}-deployment
    # Remove "ccc-course-" prefix if present
    slug = course_block
    if course_block.startswith("ccc-course-"):
        slug = course_block[11:]
    return f"ccc-{slug}-deployment"


async def ensure_deployment(
    course_block: str,
    settings: Settings,
) -> str:
    """Ensure a deployment exists for the given course block.

    Creates the deployment if it doesn't exist using flow.deploy().
    Returns deployment name.
    """
    deployment_name = get_deployment_name(settings, course_block)

    # Use work pool from settings, fallback to "local-pool" (from docker-compose)
    work_pool_name = settings.grader.work_pool_name or "local-pool"

    logger.debug("Ensuring deployment %s exists for course %s", deployment_name, course_block)

    # Deploy the flow
    # flow.deploy() will create or update the deployment
    try:
        deployment_id = await webhook_correction_flow.deploy(
            name=deployment_name,
            work_pool_name=work_pool_name,
            parameters={
                "course_block": course_block,
                # assignment_id and submission_id will be provided at runtime
                "download_dir": None,  # Let flow create temp dir
                "dry_run": False,
            },
            tags=["canvas-webhook", f"course:{course_block}"],
            print_next_steps=False,
            ignore_warnings=True,
        )

        logger.info(
            "Created/updated deployment %s (ID: %s) for course %s on work pool %s",
            deployment_name,
            deployment_id,
            course_block,
            work_pool_name,
        )

    except Exception as e:
        logger.error(
            "Failed to create deployment %s for course %s: %s",
            deployment_name,
            course_block,
            e,
            exc_info=True,
        )
        # If deployment fails, we can still try to run it (might already exist)
        # Don't re-raise, as the deployment might already exist

    return deployment_name


async def trigger_deployment(
    course_block: str,
    assignment_id: int,
    submission_id: int,
    settings: Settings,
) -> str | None:
    """Trigger deployment for a submission using Prefect's run_deployment.

    Returns flow run ID if successful, None otherwise.
    """
    try:
        # Ensure deployment exists (idempotent)
        deployment_name = await ensure_deployment(course_block, settings)

        # Run deployment
        flow_run = await run_deployment(
            deployment_name=deployment_name,
            parameters={
                "assignment_id": assignment_id,
                "submission_id": submission_id,
                "download_dir": None,  # Let flow create temp dir
                "dry_run": False,
            },
            timeout=0,  # No timeout
        )

        logger.info(
            "Triggered deployment %s for assignment %s submission %s -> flow run %s",
            deployment_name,
            assignment_id,
            submission_id,
            flow_run.id,
        )

        return str(flow_run.id)

    except Exception as e:
        logger.error(
            "Failed to trigger deployment for %s (assignment %s, submission %s): %s",
            course_block,
            assignment_id,
            submission_id,
            e,
            exc_info=True,
        )
        return None


# Legacy alias for backward compatibility
async def trigger_flow(*args: Any, **kwargs: Any) -> str | None:
    """Legacy alias for trigger_deployment."""
    return await trigger_deployment(*args, **kwargs)
