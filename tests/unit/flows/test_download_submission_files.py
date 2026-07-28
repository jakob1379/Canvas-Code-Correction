from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

import pytest
from pydantic import HttpUrl, SecretStr

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
    _download_submission_files,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.test"),
            token=SecretStr("token"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="bucket-block", path_prefix="prefix"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(root=Path("/tmp/workspaces")),
    )


def _make_resources(course: Mock, settings: Settings) -> tuple[CanvasResources, Mock]:
    canvas = Mock()
    resources = CanvasResources(canvas=cast("Any", canvas), course=course, settings=settings)
    return resources, canvas


@pytest.mark.local
def test_download_submission_files(tmp_path: Path, settings: Settings) -> None:
    attachment = {"id": 101, "filename": "code.py"}

    submission = Mock()
    submission.id = 7
    submission.attachments = [attachment]

    assignment = Mock()
    assignment.get_submission.return_value = submission

    course = Mock()
    course.get_assignment.return_value = assignment

    file_obj = Mock()
    file_obj.download = Mock()

    resources, canvas = _make_resources(course, settings)
    canvas.get_file.return_value = file_obj

    payload = CorrectSubmissionPayload(assignment_id=5, submission_id=7)

    result = _download_submission_files(resources, payload, tmp_path)

    course.get_assignment.assert_called_once_with(5)  # type: ignore[attr-defined]
    assignment.get_submission.assert_called_once_with(7)  # type: ignore[attr-defined]
    canvas.get_file.assert_called_once_with(101)
    expected_path = tmp_path / "code.py"
    file_obj.download.assert_called_once_with(expected_path.as_posix())  # type: ignore[attr-defined]
    assert result == [expected_path]


@pytest.mark.local
def test_download_submission_files_missing_filename(tmp_path: Path, settings: Settings) -> None:
    attachment = {"id": 202}

    submission = Mock()
    submission.id = 2
    submission.attachments = [attachment]

    assignment = Mock()
    assignment.get_submission.return_value = submission

    course = Mock()
    course.get_assignment.return_value = assignment

    file_obj = Mock()
    file_obj.id = 202
    file_obj.download = Mock()

    resources, canvas = _make_resources(course, settings)
    canvas.get_file.return_value = file_obj

    payload = CorrectSubmissionPayload(assignment_id=1, submission_id=2)

    result = _download_submission_files(resources, payload, tmp_path)

    expected_path = tmp_path / "attachment-202"
    file_obj.download.assert_called_once_with(expected_path.as_posix())
    assert result == [expected_path]


@pytest.mark.local
def test_download_submission_files_no_attachments(tmp_path: Path, settings: Settings) -> None:
    submission = Mock()
    submission.id = 2
    submission.attachments = None

    assignment = Mock()
    assignment.get_submission.return_value = submission

    course = Mock()
    course.get_assignment.return_value = assignment

    resources, canvas = _make_resources(course, settings)

    payload = CorrectSubmissionPayload(assignment_id=1, submission_id=2)

    result = _download_submission_files(resources, payload, tmp_path)

    assert result == []
    canvas.get_file.assert_not_called()
