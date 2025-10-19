"""Tests for the Canvas client."""

from pathlib import Path

from canvas_code_correction.canvas import CanvasClient


def test_get_submission_and_download(tmp_path: Path) -> None:
    attachment_download = "/api/v1/files/10/download"

    class DummySubmission:
        def __init__(self, payload: dict[str, object]) -> None:
            self.id = payload["id"]
            self.user_id = payload["user_id"]
            self.assignment_id = payload["assignment_id"]
            self.attachments = payload["attachments"]

    class DummyAssignment:
        def __init__(self, submission_payload: dict[str, object]) -> None:
            self._submission = DummySubmission(submission_payload)
            self.last_include: list[str] | None = None

        def get_submission(self, submission_id: int, include=None, **_: object) -> DummySubmission:  # type: ignore[override]
            if include is None:
                self.last_include = None
            else:
                self.last_include = list(include)
            return self._submission

    class DummyCourse:
        def __init__(self, assignment: DummyAssignment) -> None:
            self._assignment = assignment

        def get_assignment(self, assignment_id: int) -> DummyAssignment:
            return self._assignment

    class DummyFile:
        def __init__(self, file_id: int, name: str) -> None:
            self.id = file_id
            self.filename = name

        def download(self, location: str) -> str:
            destination = Path(location)
            destination.write_bytes(b"payload")
            return location

    class DummyCanvas:
        def __init__(self, course: DummyCourse) -> None:
            self._course = course
            self._files: dict[int, DummyFile] = {}

        def get_course(self, course_id: int) -> DummyCourse:
            return self._course

        def get_file(self, file_id: int) -> DummyFile:
            return self._files[file_id]

    submission_payload = {
        "id": 3,
        "user_id": 7,
        "assignment_id": 2,
        "attachments": [
            {
                "id": 10,
                "filename": "submission.zip",
                "display_name": "submission.zip",
                "url": f"https://canvas.example{attachment_download}",
                "content-type": "application/zip",
                "size": 5,
            }
        ],
    }

    assignment = DummyAssignment(submission_payload)
    dummy_canvas = DummyCanvas(DummyCourse(assignment))
    dummy_canvas._files[10] = DummyFile(10, "submission.zip")  # type: ignore[attr-defined]

    with CanvasClient(
        base_url="https://canvas.example",
        token="token",
        course_id=1,
        canvas=dummy_canvas,  # type: ignore[arg-type]
    ) as client:
        submission = client.get_submission(
            assignment_id=2,
            submission_id=3,
            include=["attachments"],
        )

        assert assignment.last_include == ["attachments"]
        files = client.get_submission_files(submission)
        assert files

        target = client.download_attachment(files[0], tmp_path)

    assert target.name == "submission.zip"
    assert target.read_bytes() == b"payload"
