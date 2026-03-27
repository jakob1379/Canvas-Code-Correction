"""Webhook orchestration for Canvas submission deliveries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from fastapi import status

from canvas_code_correction.webhooks.models import (
    SUPPORTED_SUBMISSION_EVENTS,
    CanvasWebhookPayload,
    WebhookResponse,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from canvas_code_correction.config import Settings
    from canvas_code_correction.webhooks.deployments import TriggerDeploymentResult


class _WebhookDeploymentRunner(Protocol):
    def __call__(
        self,
        settings: Settings,
        course_block: str,
        assignment_id: int,
        submission_id: int,
    ) -> Awaitable[TriggerDeploymentResult]: ...


WebhookDeploymentRunner = _WebhookDeploymentRunner


@dataclass(frozen=True)
class WebhookOrchestrationResult:
    """Final webhook response and HTTP status."""

    status_code: int
    response: WebhookResponse


class _WebhookRunGate(Protocol):
    def try_acquire(self, key: str) -> bool: ...

    def release(self, key: str) -> None: ...


def _build_delivery_key(
    course_block: str,
    payload: CanvasWebhookPayload,
    assignment_id: int,
    submission_id: int,
) -> str:
    request_id = payload.metadata.request_id or payload.metadata.event_time.isoformat()
    return f"{course_block}:{payload.get_event_type()}:{assignment_id}:{submission_id}:{request_id}"


def _parse_submission_target(
    canvas_payload: CanvasWebhookPayload,
) -> tuple[int, int, str]:
    event_type = canvas_payload.get_event_type()
    submission_event = canvas_payload.parse_submission_event()

    return submission_event.assignment_id, submission_event.submission_id, event_type


async def process_webhook_orchestration(
    course_block: str,
    settings: Settings,
    canvas_payload: CanvasWebhookPayload,
    run_gate: _WebhookRunGate,
    run_webhook_flow: WebhookDeploymentRunner,
) -> WebhookOrchestrationResult:
    """Run duplicate suppression and deployment orchestration."""
    event_type = canvas_payload.get_event_type()
    if event_type not in SUPPORTED_SUBMISSION_EVENTS:
        return WebhookOrchestrationResult(
            status_code=status.HTTP_200_OK,
            response=WebhookResponse(
                success=True,
                message=f"Ignored unsupported event: {event_type}",
                course_block=course_block,
            ),
        )

    assignment_id, submission_id, event_type = _parse_submission_target(canvas_payload)

    delivery_key = _build_delivery_key(
        course_block,
        canvas_payload,
        assignment_id,
        submission_id,
    )
    if not run_gate.try_acquire(delivery_key):
        return WebhookOrchestrationResult(
            status_code=status.HTTP_200_OK,
            response=WebhookResponse(
                success=True,
                message="Duplicate webhook ignored",
                course_block=course_block,
                assignment_id=assignment_id,
                submission_id=submission_id,
            ),
        )

    deployment_result = await run_webhook_flow(
        settings,
        course_block,
        assignment_id,
        submission_id,
    )

    if deployment_result.success:
        return WebhookOrchestrationResult(
            status_code=status.HTTP_202_ACCEPTED,
            response=WebhookResponse(
                success=True,
                message=f"Correction flow triggered for {event_type}",
                flow_run_id=deployment_result.flow_run_id,
                course_block=course_block,
                assignment_id=assignment_id,
                submission_id=submission_id,
            ),
        )

    run_gate.release(delivery_key)
    return WebhookOrchestrationResult(
        status_code=status.HTTP_502_BAD_GATEWAY,
        response=WebhookResponse(
            success=False,
            message=(
                f"Failed to trigger correction flow during {deployment_result.stage} "
                f"({deployment_result.error_type or 'unknown'}): {deployment_result.error}"
            ),
            course_block=course_block,
            assignment_id=assignment_id,
            submission_id=submission_id,
        ),
    )
