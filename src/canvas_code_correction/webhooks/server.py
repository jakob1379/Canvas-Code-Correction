"""FastAPI server for Canvas webhook handling."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import monotonic
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from pydantic import ValidationError

import canvas_code_correction.webhooks.handler as webhook_handler
from canvas_code_correction.bootstrap import CourseBlockLoadError, load_settings_from_course_block
from canvas_code_correction.config import Settings  # noqa: TC001
from canvas_code_correction.webhooks.auth import verify_canvas_webhook
from canvas_code_correction.webhooks.deployments import trigger_deployment
from canvas_code_correction.webhooks.models import CanvasWebhookPayload

if TYPE_CHECKING:
    from collections.abc import Callable

    from canvas_code_correction.webhooks.models import WebhookResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Canvas Code Correction Webhook Server",
    description="Receives Canvas webhooks and triggers correction flows",
    version="2.0.0",
)


@dataclass(frozen=True)
class WebhookRuntimeState:
    """Process-local limiter and gate state shared by webhook requests."""

    rate_limiter: MovingWindowRateLimiter
    run_gate: WebhookRunGate


@dataclass
class RuntimeStateFactoryHolder:
    """Mutable holder used to override runtime state factories in tests."""

    factory: Callable[[], WebhookRuntimeState]


@dataclass(frozen=True)
class ValidatedWebhookRequest:
    """Validated webhook request data needed by the route handler."""

    settings: Settings
    canvas_payload: CanvasWebhookPayload


def _build_runtime_state() -> WebhookRuntimeState:
    return WebhookRuntimeState(
        rate_limiter=MovingWindowRateLimiter(MemoryStorage()),
        run_gate=WebhookRunGate(),
    )


_runtime_state_factory_holder = RuntimeStateFactoryHolder(factory=_build_runtime_state)


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


def ensure_webhook_runtime_state(request: Request) -> WebhookRuntimeState:
    """Return cached runtime state for the current app, creating it if needed."""
    state = getattr(request.app.state, "webhook_runtime_state", None)
    if state is None:
        state = get_webhook_runtime_state_factory()()
        request.app.state.webhook_runtime_state = state
    return state


def get_rate_limiter(
    state: Annotated[WebhookRuntimeState, Depends(ensure_webhook_runtime_state)],
) -> MovingWindowRateLimiter:
    """Expose the request-shared rate limiter dependency."""
    return state.rate_limiter


def get_run_gate(
    state: Annotated[WebhookRuntimeState, Depends(ensure_webhook_runtime_state)],
) -> WebhookRunGate:
    """Expose the request-shared duplicate-run gate dependency."""
    return state.run_gate


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


def load_settings_or_404(course_block: str) -> Settings:
    """Load settings for a course block."""
    try:
        return load_settings_from_course_block(course_block)
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


def get_webhook_runner() -> webhook_handler.WebhookDeploymentRunner:
    """Return the deployment trigger callable used by webhook requests."""
    return trigger_deployment


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


async def get_validated_webhook_request(
    request: Request,
    course_block: str,
    settings: Annotated[Settings, Depends(load_settings_or_404)],
) -> ValidatedWebhookRequest:
    """Load settings and validate the inbound webhook before route handling."""
    canvas_payload = await validate_webhook(request, course_block, settings)
    return ValidatedWebhookRequest(settings=settings, canvas_payload=canvas_payload)


def _json_webhook_response(
    status_code: int,
    response: WebhookResponse,
) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=response.model_dump())


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}


@app.post("/webhooks/canvas/{course_block}")
async def handle_canvas_webhook(
    course_block: str,
    validated: Annotated[ValidatedWebhookRequest, Depends(get_validated_webhook_request)],
    limiter: Annotated[MovingWindowRateLimiter, Depends(get_rate_limiter)],
    run_gate: Annotated[WebhookRunGate, Depends(get_run_gate)],
    run_webhook_flow: Annotated[
        webhook_handler.WebhookDeploymentRunner,
        Depends(get_webhook_runner),
    ],
) -> JSONResponse:
    """Handle incoming Canvas webhook."""
    rate_limit_check(course_block, validated.settings.webhook.rate_limit, limiter)
    orchestration = await webhook_handler.process_webhook_orchestration(
        course_block,
        validated.settings,
        validated.canvas_payload,
        run_gate,
        run_webhook_flow,
    )

    return _json_webhook_response(orchestration.status_code, orchestration.response)
