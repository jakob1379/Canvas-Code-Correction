from __future__ import annotations

from unittest.mock import Mock

from canvas_code_correction.clients.canvas_resources import CanvasResources
from canvas_code_correction.config import Settings
from canvas_code_correction.flows.correction import (
    CorrectSubmissionPayload,
    fetch_submission_metadata,
)


def _make_settings() -> Settings:
    from pathlib import Path

    from pydantic import SecretStr

    from canvas_code_correction.config import (
        CanvasSettings,
        CourseAssetsSettings,
        GraderSettings,
        WorkspaceSettings,
    )

    return Settings(
        canvas=CanvasSettings(
            api_url="https://canvas.test",
            token=SecretStr("token"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="bucket-block", path_prefix="prefix"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(root=Path("/tmp/workspaces")),
    )


def test_fetch_submission_metadata_returns_serializable_dict(monkeypatch):
    assignment = Mock()
    submission = Mock()
    assignment.attributes = {"id": 10, "name": "Assignment"}
    submission.attributes = {"id": 20, "workflow_state": "submitted"}
    assignment.get_submission.return_value = submission

    course = Mock()
    course.get_assignment.return_value = assignment

    resources = CanvasResources(
        canvas=Mock(),
        course=course,
        settings=_make_settings(),
    )

    payload = CorrectSubmissionPayload(assignment_id=10, submission_id=20)

    result = fetch_submission_metadata.fn(resources, payload)

    course.get_assignment.assert_called_once_with(10)
    assignment.get_submission.assert_called_once_with(
        20,
        include=[
            "submission_comments",
            "submission_history",
            "full_rubric_assessment",
            "rubric_assessment",
        ],
    )

    assert result == {
        "assignment": {"id": 10, "name": "Assignment"},
        "submission": {"id": 20, "workflow_state": "submitted"},
    }
