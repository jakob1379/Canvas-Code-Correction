"""Unit tests for Canvas webhook models."""

from datetime import UTC, datetime

from canvas_code_correction.webhooks.models import (
    CanvasWebhookMetadata,
    CanvasWebhookPayload,
    SubmissionCreatedEvent,
    SubmissionUpdatedEvent,
)


def test_canvas_webhook_metadata() -> None:
    """Test CanvasWebhookMetadata validation."""
    metadata = CanvasWebhookMetadata(
        event_name="submission_created",
        event_time=datetime.now(UTC),
        producer="canvas",
    )
    assert metadata.event_name == "submission_created"
    assert metadata.producer == "canvas"
    assert metadata.client_ip is None


def test_submission_created_event() -> None:
    """Test SubmissionCreatedEvent validation."""
    event = SubmissionCreatedEvent(
        assignment_id="123",
        submission_id="456",
        submission_type="online_text_entry",
        submitted_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        user_id="789",
        workflow_state="submitted",
    )
    assert event.assignment_id == "123"
    assert event.submission_id == "456"
    assert event.user_id == "789"
    assert event.late is False
    assert event.missing is False


def test_submission_updated_event_inherits() -> None:
    """Test SubmissionUpdatedEvent inherits from SubmissionCreatedEvent."""
    event = SubmissionUpdatedEvent(
        assignment_id="123",
        submission_id="456",
        submission_type="online_text_entry",
        submitted_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        user_id="789",
        workflow_state="graded",
    )
    assert event.assignment_id == "123"
    assert isinstance(event, SubmissionCreatedEvent)


def test_canvas_webhook_payload_parsing() -> None:
    """Test CanvasWebhookPayload parsing and event extraction."""
    payload = CanvasWebhookPayload(
        metadata=CanvasWebhookMetadata(
            event_name="submission_created",
            event_time=datetime.now(UTC),
            producer="canvas",
        ),
        body={
            "assignment_id": "123",
            "submission_id": "456",
            "submission_type": "online_text_entry",
            "submitted_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "user_id": "789",
            "workflow_state": "submitted",
        },
    )
    assert payload.get_event_type() == "submission_created"
    event = payload.parse_submission_event()
    assert isinstance(event, SubmissionCreatedEvent)
    assert event.assignment_id == "123"
    assert event.submission_id == "456"


def test_canvas_webhook_payload_invalid_event() -> None:
    """Test CanvasWebhookPayload with unsupported event type."""
    payload = CanvasWebhookPayload(
        metadata=CanvasWebhookMetadata(
            event_name="assignment_created",
            event_time=datetime.now(UTC),
            producer="canvas",
        ),
        body={},
    )
    assert payload.get_event_type() == "assignment_created"
    assert payload.parse_submission_event() is None


def test_webhook_response() -> None:
    """Test WebhookResponse model."""
    from canvas_code_correction.webhooks.models import WebhookResponse

    response = WebhookResponse(
        success=True,
        message="Test",
        flow_run_id="run-123",
        course_block="ccc-course-math101",
        assignment_id=123,
        submission_id=456,
    )
    assert response.success is True
    assert response.flow_run_id == "run-123"
    assert response.course_block == "ccc-course-math101"
    assert response.assignment_id == 123
    assert response.submission_id == 456
