"""FastAPI server for Canvas webhook handling."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from canvas_code_correction.config import Settings, resolve_settings_from_block
from canvas_code_correction.webhooks.auth import verify_canvas_webhook
from canvas_code_correction.webhooks.deployments import trigger_deployment
from canvas_code_correction.webhooks.models import (
    CanvasWebhookPayload,
    SubmissionCreatedEvent,
    SubmissionUpdatedEvent,
    WebhookResponse,
)

logger = logging.getLogger(__name__)

# Rate limiting setup
storage = MemoryStorage()
limiter = MovingWindowRateLimiter(storage)

app = FastAPI(
    title="Canvas Code Correction Webhook Server",
    description="Receives Canvas webhooks and triggers correction flows",
    version="2.0.0",
)


def get_settings(course_block: str) -> Settings:
    """Load settings for a course block."""
    try:
        return resolve_settings_from_block(course_block)
    except Exception as e:
        logger.error("Failed to load course block %s: %s", course_block, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course block '{course_block}' not found or invalid",
        ) from e


def rate_limit_check(course_block: str, limit_str: str = "10/minute") -> None:
    """Check rate limit for a course block."""
    limit = parse(limit_str)
    if not limiter.hit(limit, course_block, datetime.now()):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {course_block}",
        )


async def validate_webhook(
    request: Request,
    course_block: str,
    settings: Settings,
) -> CanvasWebhookPayload:
    """Validate webhook signature and parse payload."""
    # Check if webhook enabled
    if not settings.webhook.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook processing disabled for this course",
        )

    # Read raw body for signature verification
    body = await request.body()

    # Verify signature
    if not await verify_canvas_webhook(settings, body, request.headers):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {e}",
        ) from e

    # Validate with Pydantic
    try:
        canvas_payload = CanvasWebhookPayload(**payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid webhook payload structure: {e}",
        ) from e

    return canvas_payload


async def trigger_correction_flow(
    course_block: str,
    assignment_id: int,
    submission_id: int,
    settings: Settings,
) -> str | None:
    """Trigger Prefect correction flow for a submission.

    Returns flow run ID if successful, None otherwise.
    """
    return await trigger_deployment(
        course_block=course_block,
        assignment_id=assignment_id,
        submission_id=submission_id,
        settings=settings,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/webhooks/canvas/{course_block}")
async def handle_canvas_webhook(
    request: Request,
    course_block: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WebhookResponse:
    """Handle incoming Canvas webhook."""
    # Rate limiting
    rate_limit_check(course_block, settings.webhook.rate_limit)

    # Validate and parse webhook
    canvas_payload = await validate_webhook(request, course_block, settings)

    # Parse event type
    event_type = canvas_payload.get_event_type()
    if event_type not in ("submission_created", "submission_updated"):
        return WebhookResponse(
            success=False,
            message=f"Unsupported event type: {event_type}",
            course_block=course_block,
        )

    # Parse submission event
    submission_event = canvas_payload.parse_submission_event()
    if not submission_event:
        return WebhookResponse(
            success=False,
            message="Failed to parse submission event",
            course_block=course_block,
        )

    # Extract IDs
    try:
        assignment_id = int(submission_event.assignment_id)
        submission_id = int(submission_event.submission_id)
    except ValueError:
        return WebhookResponse(
            success=False,
            message=f"Invalid ID format: assignment={submission_event.assignment_id}, submission={submission_event.submission_id}",
            course_block=course_block,
        )

    # Trigger correction flow
    flow_run_id = await trigger_correction_flow(
        course_block, assignment_id, submission_id, settings
    )

    if flow_run_id:
        return WebhookResponse(
            success=True,
            message=f"Correction flow triggered for {event_type}",
            flow_run_id=flow_run_id,
            course_block=course_block,
            assignment_id=assignment_id,
            submission_id=submission_id,
        )
    else:
        return WebhookResponse(
            success=False,
            message="Failed to trigger correction flow",
            course_block=course_block,
            assignment_id=assignment_id,
            submission_id=submission_id,
        )


@app.post("/webhooks/canvas/{course_block}/test")
async def test_webhook(
    course_block: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WebhookResponse:
    """Manual test endpoint for webhook configuration."""
    if not settings.webhook.enabled:
        return WebhookResponse(
            success=False,
            message="Webhook processing disabled for this course",
            course_block=course_block,
        )

    # Return current configuration (without secret)
    return WebhookResponse(
        success=True,
        message="Webhook configuration test",
        course_block=course_block,
    )
