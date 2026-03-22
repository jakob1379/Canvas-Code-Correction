"""FastAPI server for Canvas webhook handling."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import monotonic
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from pydantic import ValidationError

from canvas_code_correction.bootstrap import CourseBlockLoadError, load_settings_from_course_block
from canvas_code_correction.config import Settings
from canvas_code_correction.webhooks.auth import verify_canvas_webhook
from canvas_code_correction.webhooks.deployments import trigger_deployment
from canvas_code_correction.webhooks.models import (
    SUPPORTED_SUBMISSION_EVENTS,
    CanvasWebhookPayload,
    InvalidSubmissionEventError,
    UnsupportedSubmissionEventError,
    WebhookResponse,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from canvas_code_correction.webhooks.deployments import TriggerDeploymentResult

app = FastAPI(
    title="Canvas Code Correction Webhook Server",
    description="Receives Canvas webhooks and triggers correction flows",
    version="2.0.0",
)


WebhookDeploymentRunner = Callable[
    [Settings, str, int, int],
    Awaitable["TriggerDeploymentResult"],
]


def _new_rate_limiter() -> MovingWindowRateLimiter:
    return MovingWindowRateLimiter(MemoryStorage())


def _new_run_gate() -> WebhookRunGate:
    return WebhookRunGate()


def _default_webhook_runtime_state_factory() -> WebhookRuntimeState:
    return _build_runtime_state()


@dataclass(frozen=True)
class WebhookRuntimeState:
    """Process-local limiter and gate state shared by webhook requests."""

    rate_limiter: MovingWindowRateLimiter
    run_gate: WebhookRunGate


@dataclass(frozen=True)
class WebhookRequestContext:
    """Typed request-scoped dependencies for webhook handling."""

    settings: Settings
    limiter: MovingWindowRateLimiter
    run_gate: WebhookRunGate
    run_webhook_flow: WebhookDeploymentRunner


@dataclass
class RuntimeStateFactoryHolder:
    """Mutable holder used to override runtime state factories in tests."""

    factory: Callable[[], WebhookRuntimeState]


_runtime_state_factory_holder = RuntimeStateFactoryHolder(
    factory=_default_webhook_runtime_state_factory,
)


def _build_runtime_state() -> WebhookRuntimeState:
    return WebhookRuntimeState(
        rate_limiter=_new_rate_limiter(),
        run_gate=_new_run_gate(),
    )


def get_webhook_runtime_state_factory() -> Callable[[], WebhookRuntimeState]:
    """Return the active runtime-state factory."""
    return _runtime_state_factory_holder.factory


def set_webhook_runtime_state_factory(factory: Callable[[], WebhookRuntimeState]) -> None:
    """Override the runtime-state factory, typically for tests."""
    _runtime_state_factory_holder.factory = factory


def reset_runtime_state(fastapi_app: FastAPI | None = None) -> None:
    """Reset cached webhook runtime state on the target FastAPI app."""
    target_app = fastapi_app or app
    target_app.state.webhook_runtime_state = get_webhook_runtime_state_factory()()


def get_webhook_runtime_state(request: Request) -> WebhookRuntimeState:
    """Return cached runtime state for the current app, creating it if needed."""
    state = getattr(request.app.state, "webhook_runtime_state", None)
    if state is None:
        state = get_webhook_runtime_state_factory()()
        request.app.state.webhook_runtime_state = state
    return state


def get_rate_limiter(
    state: Annotated[WebhookRuntimeState, Depends(get_webhook_runtime_state)],
) -> MovingWindowRateLimiter:
    """Expose the request-shared rate limiter dependency."""
    return state.rate_limiter


def get_run_gate(
    state: Annotated[WebhookRuntimeState, Depends(get_webhook_runtime_state)],
) -> WebhookRunGate:
    """Expose the request-shared duplicate-run gate dependency."""
    return state.run_gate


def get_webhook_settings(course_block: str) -> Settings:
    """Load course settings for a webhook request."""
    return load_settings_from_course_block(course_block)


@dataclass
class WebhookRunGate:
    """Track in-flight webhook deliveries to suppress duplicate runs."""

    ttl_seconds: float = 300.0
    _entries: dict[str, float] = field(default_factory=dict)

    def try_acquire(self, key: str) -> bool:
        """Reserve a delivery key if it is not already active."""
        now = monotonic()
        self._entries = {
            existing_key: expires_at
            for existing_key, expires_at in self._entries.items()
            if expires_at > now
        }
        if key in self._entries:
            return False
        self._entries[key] = now + self.ttl_seconds
        return True

    def release(self, key: str) -> None:
        """Release a delivery key after a failed downstream trigger."""
        self._entries.pop(key, None)


def _build_delivery_key(
    course_block: str,
    payload: CanvasWebhookPayload,
    assignment_id: int,
    submission_id: int,
) -> str:
    request_id = payload.metadata.request_id or payload.metadata.event_time.isoformat()
    return f"{course_block}:{payload.get_event_type()}:{assignment_id}:{submission_id}:{request_id}"


def load_settings_or_404(course_block: str) -> Settings:
    """Load settings for a course block."""
    try:
        return get_webhook_settings(course_block)
    except CourseBlockLoadError as exc:
        if isinstance(exc.cause, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.reason,
            ) from exc
        logger.exception("Failed to load course block %s", course_block)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load course block {course_block}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to load course block %s", course_block)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load course block {course_block}",
        ) from exc


def rate_limit_check(
    course_block: str,
    limit_str: str,
    limiter: MovingWindowRateLimiter,
) -> None:
    """Check rate limit for a course block."""
    limit = parse(limit_str)
    if not limiter.hit(limit, course_block):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {course_block}",
        )


def _parse_submission_target(
    canvas_payload: CanvasWebhookPayload,
) -> tuple[int, int, str]:
    event_type = canvas_payload.get_event_type()
    if event_type not in SUPPORTED_SUBMISSION_EVENTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unsupported event type: {event_type}",
        )

    try:
        submission_event = canvas_payload.parse_submission_event()
    except UnsupportedSubmissionEventError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except InvalidSubmissionEventError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid submission event payload",
        ) from exc

    assignment_id = submission_event.assignment_id
    submission_id = submission_event.submission_id
    return assignment_id, submission_id, event_type


def get_webhook_runner() -> WebhookDeploymentRunner:
    """Return the deployment trigger callable used by webhook requests."""
    return trigger_deployment


def _build_webhook_request_context(
    settings: Annotated[Settings, Depends(load_settings_or_404)],
    limiter: Annotated[MovingWindowRateLimiter, Depends(get_rate_limiter)],
    run_gate: Annotated[WebhookRunGate, Depends(get_run_gate)],
    run_webhook_flow: Annotated[
        WebhookDeploymentRunner,
        Depends(get_webhook_runner),
    ],
) -> WebhookRequestContext:
    return WebhookRequestContext(
        settings=settings,
        limiter=limiter,
        run_gate=run_gate,
        run_webhook_flow=run_webhook_flow,
    )


def _payload_validation_detail(error: ValidationError) -> str:
    for item in error.errors():
        field = item["loc"][-1]
        error_type = item["type"]
        if field in {"assignment_id", "submission_id"} and error_type == "missing":
            return "Invalid submission event payload"
        if field in {"assignment_id", "submission_id"} and error_type == "int_parsing":
            return "Invalid ID format in submission event payload"
    return f"Invalid webhook payload structure: {error}"


async def validate_webhook(
    request: Request,
    _course_block: str,
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

    # Parse and validate JSON payload once
    try:
        canvas_payload = CanvasWebhookPayload.model_validate_json(body)
    except ValidationError as exc:
        for item in exc.errors():
            if item["type"] == "json_invalid":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON payload: {item['msg']}",
                ) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_payload_validation_detail(exc),
        ) from exc

    # Verify webhook signature using parsed payload
    verification = verify_canvas_webhook(
        settings,
        body,
        dict(request.headers),
        payload=canvas_payload,
    )
    if not verification.success:
        raise HTTPException(
            status_code=verification.status_code,
            detail=verification.message,
        )

    return canvas_payload


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}


@app.post("/webhooks/canvas/{course_block}")
async def handle_canvas_webhook(
    request: Request,
    response: Response,
    course_block: str,
    context: Annotated[WebhookRequestContext, Depends(_build_webhook_request_context)],
) -> WebhookResponse:
    """Handle incoming Canvas webhook."""
    rate_limit_check(course_block, context.settings.webhook.rate_limit, context.limiter)
    canvas_payload = await validate_webhook(request, course_block, context.settings)

    assignment_id, submission_id, event_type = _parse_submission_target(canvas_payload)

    delivery_key = _build_delivery_key(
        course_block,
        canvas_payload,
        assignment_id,
        submission_id,
    )
    if not context.run_gate.try_acquire(delivery_key):
        return WebhookResponse(
            success=True,
            message="Duplicate webhook ignored",
            course_block=course_block,
            assignment_id=assignment_id,
            submission_id=submission_id,
        )

    deployment_result = await context.run_webhook_flow(
        context.settings,
        course_block,
        assignment_id,
        submission_id,
    )

    if deployment_result.success:
        response.status_code = status.HTTP_202_ACCEPTED
        return WebhookResponse(
            success=True,
            message=f"Correction flow triggered for {event_type}",
            flow_run_id=deployment_result.flow_run_id,
            course_block=course_block,
            assignment_id=assignment_id,
            submission_id=submission_id,
        )
    context.run_gate.release(delivery_key)
    response.status_code = status.HTTP_502_BAD_GATEWAY
    return WebhookResponse(
        success=False,
        message=(
            f"Failed to trigger correction flow during {deployment_result.stage} "
            f"({deployment_result.error_type or 'unknown'}): {deployment_result.error}"
        ),
        course_block=course_block,
        assignment_id=assignment_id,
        submission_id=submission_id,
    )
