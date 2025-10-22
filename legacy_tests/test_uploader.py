"""Tests for the Canvas uploader helpers."""

from pathlib import Path

from canvas_code_correction.uploader import Uploader


class _DummySubmission:
    def __init__(self) -> None:
        self.submission_comments: list[dict] = []
        self.grade_payload: dict | None = None
        self.upload_calls: list[tuple[str | None, str | None]] = []

    def upload_comment(self, comment: str | None = None, file: str | None = None) -> None:
        self.upload_calls.append((comment, file))
        if file:
            filename = Path(file).name
            self.submission_comments.append({"attachments": [{"display_name": filename}]})

    def edit(self, submission: dict[str, str]) -> None:
        self.grade_payload = submission


class _DummyCanvasClient:
    def __init__(self, submission: _DummySubmission) -> None:
        self._submission = submission

    def get_submission(self, assignment_id: int, submission_id: int, *, include=None):
        return self._submission


def test_upload_feedback_with_file(tmp_path: Path) -> None:
    zip_path = tmp_path / "feedback.zip"
    zip_path.write_bytes(b"zipdata")

    submission = _DummySubmission()
    uploader = Uploader(_DummyCanvasClient(submission))

    comment_uploaded, feedback_uploaded = uploader.upload_feedback(1, 2, "Nice!", zip_path)

    assert comment_uploaded is True
    assert feedback_uploaded is True
    assert submission.upload_calls[-1] == ("Nice!", str(zip_path))


def test_upload_feedback_skips_duplicate(tmp_path: Path) -> None:
    zip_path = tmp_path / "feedback.zip"
    zip_path.write_bytes(b"zipdata")

    submission = _DummySubmission()
    submission.submission_comments = [{"attachments": [{"display_name": zip_path.name}]}]
    uploader = Uploader(_DummyCanvasClient(submission))

    comment_uploaded, feedback_uploaded = uploader.upload_feedback(1, 2, "Repeat", zip_path)

    assert feedback_uploaded is False
    assert comment_uploaded is True
    assert submission.upload_calls[-1] == ("Repeat", None)


def test_upload_grade_sets_posted_grade(tmp_path: Path) -> None:
    submission = _DummySubmission()
    uploader = Uploader(_DummyCanvasClient(submission))

    outcome = uploader.upload_grade(1, 2, 9.5)

    assert outcome is True
    assert submission.grade_payload == {"posted_grade": "9.5"}
