from __future__ import annotations

from typing import ClassVar

from canvas_code_correction.flows.correction import (
    CorrectSubmissionPayload,
    _canvas_object_to_dict,
)


def test_correct_submission_payload_preserves_inputs() -> None:
    payload = CorrectSubmissionPayload(
        assignment_id=10,
        submission_id=20,
        workspace_id="run-1",
    )

    assert payload.assignment_id == 10
    assert payload.submission_id == 20
    assert payload.workspace_id == "run-1"


def test_canvas_object_to_dict_uses_attributes_when_available() -> None:
    class CanvasObject:
        attributes: ClassVar[dict[str, object]] = {"id": 7, "state": "submitted"}

    assert _canvas_object_to_dict(CanvasObject()) == {"id": 7, "state": "submitted"}
