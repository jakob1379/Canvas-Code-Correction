from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import SecretStr

from canvas_code_correction.clients.canvas_resources import CanvasResources
from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WorkspaceSettings,
)
from canvas_code_correction.flows.correction import (
    CorrectSubmissionPayload,
    download_submission_files,
)


@pytest.fixture
def settings() -> Settings:
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


def _make_resources(course: Mock, settings: Settings) -> CanvasResources:
    return CanvasResources(canvas=Mock(), course=course, settings=settings)


@pytest.mark.local
def test_download_submission_files(tmp_path: Path, settings: Settings) -> None:
    attachment = {"id": 101, "filename": "code.py"}

    submission = Mock()
    submission.attachments = [attachment]

    assignment = Mock()
    assignment.get_submission.return_value = submission

    course = Mock()
    course.get_assignment.return_value = assignment

    file_obj = Mock()
    file_obj.download = Mock()

    resources = _make_resources(course, settings)
    resources.canvas.get_file.return_value = file_obj

    payload = CorrectSubmissionPayload(assignment_id=5, submission_id=7)

    result = download_submission_files.fn(resources, payload, tmp_path)

    course.get_assignment.assert_called_once_with(5)  # type: ignore[attr-defined]
    assignment.get_submission.assert_called_once_with(7)  # type: ignore[attr-defined]
    resources.canvas.get_file.assert_called_once_with(101)  # type: ignore[attr-defined]
    expected_path = tmp_path / "code.py"
    file_obj.download.assert_called_once_with(expected_path.as_posix())  # type: ignore[attr-defined]
    assert result == [expected_path]


@pytest.mark.local
def test_download_submission_files_missing_filename(tmp_path: Path, settings: Settings) -> None:
    attachment = {"id": 202}

    submission = Mock()
    submission.attachments = [attachment]

    assignment = Mock()
    assignment.get_submission.return_value = submission

    course = Mock()
    course.get_assignment.return_value = assignment

    file_obj = Mock()
    file_obj.id = 202
    file_obj.download = Mock()

    resources = _make_resources(course, settings)
    resources.canvas.get_file.return_value = file_obj

    payload = CorrectSubmissionPayload(assignment_id=1, submission_id=2)

    result = download_submission_files.fn(resources, payload, tmp_path)

    expected_path = tmp_path / "attachment-202"
    file_obj.download.assert_called_once_with(expected_path.as_posix())
    assert result == [expected_path]


@pytest.mark.local
def test_download_submission_files_no_attachments(tmp_path: Path, settings: Settings) -> None:
    submission = Mock()
    submission.attachments = None

    assignment = Mock()
    assignment.get_submission.return_value = submission

    course = Mock()
    course.get_assignment.return_value = assignment

    resources = _make_resources(course, settings)

    payload = CorrectSubmissionPayload(assignment_id=1, submission_id=2)

    result = download_submission_files.fn(resources, payload, tmp_path)

    assert result == []
    resources.canvas.get_file.assert_not_called()  # type: ignore[attr-defined]
