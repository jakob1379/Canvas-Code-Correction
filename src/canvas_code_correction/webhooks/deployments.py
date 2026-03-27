"""Proper deployment management for webhook-triggered flows using Prefect 3.x."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from inspect import isawaitable
from typing import TYPE_CHECKING, Protocol, cast

from prefect.client.orchestration import get_client
from prefect.deployments.flow_runs import run_deployment
from prefect.exceptions import ObjectNotFound, PrefectException

from canvas_code_correction.webhooks import flows as webhook_flows

if TYPE_CHECKING:
    from prefect.client.schemas.objects import FlowRun

    from canvas_code_correction.config import Settings

    class _DeployableWebhookFlow(Protocol):
        name: str

        def deploy(self, *args: object, **kwargs: object) -> object: ...


logger = logging.getLogger(__name__)

WEBHOOK_FLOW_NAME = "webhook-correction-flow"
_EXPECTED_DEPLOYMENT_ERRORS = (PrefectException, OSError)


def _serialize_settings_for_flow(settings: Settings) -> dict[str, object]:
    return settings.to_flow_payload()


@dataclass(frozen=True)
class DeploymentTarget:
    """Resolved deployment identity for a course."""

    name: str
    work_pool_name: str


@dataclass(frozen=True)
class DeploymentEnsureResult:
    """Outcome of ensuring a deployment exists."""

    deployment_name: str
    work_pool_name: str
    ensured: bool
    deployment_id: str | None = None
    error: str | None = None
    error_type: str | None = None


@dataclass(frozen=True)
class TriggerDeploymentResult:
    """Outcome of triggering a Prefect deployment run."""

    deployment_name: str
    success: bool
    flow_run_id: str | None = None
    error: str | None = None
    stage: str | None = None
    error_type: str | None = None


def get_deployment_name(settings: Settings, course_block: str) -> str:
    """Get deployment name for a course block."""
    if settings.webhook.deployment_name:
        return settings.webhook.deployment_name

    slug = course_block
    if course_block.startswith("ccc-course-"):
        slug = course_block[11:]
    return f"ccc-{slug}-deployment"


def resolve_deployment_target(settings: Settings, course_block: str) -> DeploymentTarget:
    """Resolve deployment name and work pool for a course."""
    return DeploymentTarget(
        name=get_deployment_name(settings, course_block),
        work_pool_name=settings.grader.work_pool_name or "local-pool",
    )


async def ensure_deployment(
    settings: Settings,
    course_block: str,
) -> DeploymentEnsureResult:
    """Ensure a deployment exists for the given course block.

    Creates the deployment if it doesn't exist using flow.deploy() and returns
    a DeploymentEnsureResult describing the outcome.
    """
    target = resolve_deployment_target(settings, course_block)
    webhook_flow = cast("_DeployableWebhookFlow", webhook_flows.webhook_correction_flow)
    deployment_full_name = f"{webhook_flow.name}/{target.name}"

    deployment_exists = False
    async with get_client() as client:
        try:
            await client.read_deployment_by_name(deployment_full_name)
            deployment_exists = True
        except ObjectNotFound:
            deployment_exists = False
        except _EXPECTED_DEPLOYMENT_ERRORS as exc:
            logger.exception(
                "Failed to inspect deployment %s for course %s",
                target.name,
                course_block,
            )
            return DeploymentEnsureResult(
                deployment_name=target.name,
                work_pool_name=target.work_pool_name,
                ensured=False,
                error=str(exc),
                error_type=type(exc).__name__,
            )

    if deployment_exists:
        logger.debug("Updating deployment %s for course %s", target.name, course_block)
    else:
        logger.debug("Creating deployment %s for course %s", target.name, course_block)

    # Deploy the flow
    # flow.deploy() will create or update the deployment
    try:
        deployment_handle = webhook_flow.deploy(
            name=target.name,
            work_pool_name=target.work_pool_name,
            parameters={
                "course": {
                    "course_block": course_block,
                    "settings": _serialize_settings_for_flow(settings),
                },
                "download_dir": None,  # Let flow create temp dir
                "dry_run": False,
            },
            tags=["canvas-webhook", f"course:{course_block}"],
            print_next_steps=False,
            ignore_warnings=True,
        )

        deployment_id = (
            await deployment_handle if isawaitable(deployment_handle) else deployment_handle
        )
        deployment_id_str = str(deployment_id)

        logger.info(
            "Created/updated deployment %s (ID: %s) for course %s on work pool %s",
            target.name,
            deployment_id_str,
            course_block,
            target.work_pool_name,
        )
        return DeploymentEnsureResult(
            deployment_name=target.name,
            work_pool_name=target.work_pool_name,
            ensured=True,
            deployment_id=deployment_id_str,
        )

    except _EXPECTED_DEPLOYMENT_ERRORS as exc:
        logger.exception(
            "Failed to create deployment %s for course %s",
            target.name,
            course_block,
        )
        return DeploymentEnsureResult(
            deployment_name=target.name,
            work_pool_name=target.work_pool_name,
            ensured=False,
            error=str(exc),
            error_type=type(exc).__name__,
        )


async def trigger_deployment(
    settings: Settings,
    course_block: str,
    assignment_id: int,
    submission_id: int,
) -> TriggerDeploymentResult:
    """Trigger deployment for a submission using Prefect's run_deployment.

    Returns structured run outcome.
    """
    ensure_result = await ensure_deployment(settings, course_block)
    if not ensure_result.ensured:
        return TriggerDeploymentResult(
            deployment_name=ensure_result.deployment_name,
            success=False,
            error=ensure_result.error or "Deployment provisioning failed",
            stage="ensure",
            error_type=ensure_result.error_type,
        )

    try:
        run_target = resolve_deployment_target(settings, course_block)
        flow_run_result = run_deployment(
            name=f"{WEBHOOK_FLOW_NAME}/{run_target.name}",
            parameters={
                "course": {
                    "course_block": course_block,
                    "settings": _serialize_settings_for_flow(settings),
                },
                "submission": {
                    "assignment_id": assignment_id,
                    "submission_id": submission_id,
                },
                "download_dir": None,  # Let flow create temp dir
                "dry_run": False,
            },
            timeout=0,  # No timeout
        )
        flow_run = await flow_run_result if isawaitable(flow_run_result) else flow_run_result
        flow_run = cast("FlowRun", flow_run)

        flow_run_id = str(flow_run.id)
        logger.info(
            "Triggered deployment %s for assignment %s submission %s -> flow run %s",
            ensure_result.deployment_name,
            assignment_id,
            submission_id,
            flow_run_id,
        )

        return TriggerDeploymentResult(
            deployment_name=ensure_result.deployment_name,
            success=True,
            flow_run_id=flow_run_id,
        )

    except _EXPECTED_DEPLOYMENT_ERRORS as exc:
        logger.exception(
            "Failed to trigger deployment for %s (assignment %s, submission %s)",
            course_block,
            assignment_id,
            submission_id,
        )
        return TriggerDeploymentResult(
            deployment_name=ensure_result.deployment_name,
            success=False,
            error=str(exc),
            stage="trigger",
            error_type=type(exc).__name__,
        )
