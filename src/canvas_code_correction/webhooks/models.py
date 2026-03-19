"""Pydantic models for Canvas webhook payload validation."""

from __future__ import annotations

from datetime import datetime
from typing import Final, Literal, cast

from pydantic import BaseModel, HttpUrl

type SubmissionEventName = Literal["submission_created", "submission_updated"]

SUPPORTED_SUBMISSION_EVENTS: Final[frozenset[SubmissionEventName]] = frozenset(
    {"submission_created", "submission_updated"},
)


class UnsupportedSubmissionEventError(ValueError):
    """Raised when a webhook event is not a supported submission event."""


class InvalidSubmissionEventError(ValueError):
    """Raised when a supported submission event payload is malformed."""


class CanvasWebhookMetadata(BaseModel):
    """Metadata section of Canvas webhook payload."""

    client_ip: str | None = None
    context_account_id: str | None = None
    context_id: str | None = None
    context_role: str | None = None
    context_sis_source_id: str | None = None
    context_type: str | None = None
    event_name: str
    event_time: datetime
    hostname: str | None = None
    http_method: str | None = None
    producer: str = "canvas"
    referrer: HttpUrl | None = None
    request_id: str | None = None
    root_account_id: str | None = None
    root_account_lti_guid: str | None = None
    root_account_uuid: str | None = None
    session_id: str | None = None
    time_zone: str | None = None
    url: HttpUrl | None = None
    user_account_id: str | None = None
    user_agent: str | None = None
    user_id: str | None = None
    user_login: str | None = None
    user_sis_id: str | None = None


class SubmissionCreatedEvent(BaseModel):
    """Submission created event body from Canvas webhook."""

    assignment_id: int
    submission_id: int
    attempt: int | None = None
    body: str | None = None
    grade: str | None = None
    graded_at: datetime | None = None
    group_id: int | None = None
    late: bool = False
    lti_assignment_id: str | None = None
    lti_user_id: str | None = None
    missing: bool = False
    score: float | None = None
    submission_type: str
    submitted_at: datetime
    updated_at: datetime
    url: HttpUrl | None = None
    user_id: int
    workflow_state: str


class SubmissionUpdatedEvent(SubmissionCreatedEvent):
    """Submission updated event body from Canvas webhook."""


class CanvasWebhookPayload(BaseModel):
    """Complete Canvas webhook payload."""

    metadata: CanvasWebhookMetadata
    body: SubmissionCreatedEvent | SubmissionUpdatedEvent

    def get_event_type(self) -> str:
        """Extract event type from metadata."""
        return self.metadata.event_name

    def get_submission_event_type(self) -> SubmissionEventName:
        """Return the event name narrowed to supported submission events."""
        event_type = self.get_event_type()
        if event_type not in SUPPORTED_SUBMISSION_EVENTS:
            msg = f"Unsupported event type: {event_type}"
            raise UnsupportedSubmissionEventError(msg)
        return cast("SubmissionEventName", event_type)

    def parse_submission_event(self) -> SubmissionCreatedEvent | SubmissionUpdatedEvent:
        """Parse body into a specific submission event model."""
        event_type = self.get_submission_event_type()
        if event_type == "submission_created":
            return SubmissionCreatedEvent.model_validate(self.body.model_dump())
        if event_type == "submission_updated":
            return SubmissionUpdatedEvent.model_validate(self.body.model_dump())
        msg = f"Invalid payload for {event_type}"
        raise InvalidSubmissionEventError(msg)


class WebhookResponse(BaseModel):
    """Standardized webhook response."""

    success: bool
    message: str
    flow_run_id: str | None = None
    course_block: str | None = None
    assignment_id: int | None = None
    submission_id: int | None = None
