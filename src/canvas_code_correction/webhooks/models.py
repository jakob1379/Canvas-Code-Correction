"""Pydantic models for Canvas webhook payload validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, HttpUrl


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

    assignment_id: str
    submission_id: str
    attempt: int | None = None
    body: str | None = None
    grade: str | None = None
    graded_at: datetime | None = None
    group_id: str | None = None
    late: bool = False
    lti_assignment_id: str | None = None
    lti_user_id: str | None = None
    missing: bool = False
    score: float | None = None
    submission_type: str
    submitted_at: datetime
    updated_at: datetime
    url: HttpUrl | None = None
    user_id: str
    workflow_state: str


class SubmissionUpdatedEvent(SubmissionCreatedEvent):
    """Submission updated event body from Canvas webhook."""


class CanvasWebhookPayload(BaseModel):
    """Complete Canvas webhook payload."""

    metadata: CanvasWebhookMetadata
    body: dict[str, Any]

    def get_event_type(self) -> str:
        """Extract event type from metadata."""
        return self.metadata.event_name

    def parse_submission_event(self) -> SubmissionCreatedEvent | SubmissionUpdatedEvent | None:
        """Parse body into specific event model based on event type."""
        event_type = self.get_event_type()
        if event_type == "submission_created":
            return SubmissionCreatedEvent(**self.body)
        if event_type == "submission_updated":
            return SubmissionUpdatedEvent(**self.body)
        return None


class WebhookResponse(BaseModel):
    """Standardized webhook response."""

    success: bool
    message: str
    flow_run_id: str | None = None
    course_block: str | None = None
    assignment_id: int | None = None
    submission_id: int | None = None
