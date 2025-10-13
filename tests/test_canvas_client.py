# bandit: disable=B101,B105,B106
"""Tests for the Canvas client."""

from __future__ import annotations

from pathlib import Path

import httpx

from canvas_code_correction.canvas import CanvasClient


def test_get_submission_and_download(tmp_path: Path) -> None:
    attachment_download = "/api/v1/files/10/download"

    class DummySubmission:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def to_dict(self) -> dict[str, object]:
            return self._payload

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

    class DummyCanvas:
        def __init__(self, course: DummyCourse) -> None:
            self._course = course

        def get_course(self, course_id: int) -> DummyCourse:
            return self._course

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

    def responder(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == attachment_download:
            return httpx.Response(status_code=200, content=b"payload")
        raise AssertionError(f"Unexpected request {request.method} {request.url!s}")

    transport = httpx.MockTransport(responder)
    http_client = httpx.Client(transport=transport)

    with CanvasClient(
        base_url="https://canvas.example",
        token="token",  # nosec B106
        course_id=1,
        canvas=dummy_canvas,  # type: ignore[arg-type]
        http_client=http_client,
    ) as client:
        submission = client.get_submission(
            assignment_id=2,
            submission_id=3,
            include=["attachments"],
        )

        assert assignment.last_include == ["attachments"]  # nosec B101
        assert submission.id == 3  # nosec B101
        assert submission.attachments  # nosec B101
        attachment_obj = submission.attachments[0]
        assert attachment_obj.content_type == "application/zip"  # nosec B101

        target = client.download_attachment(attachment_obj, tmp_path)

    http_client.close()

    assert target.name == "submission.zip"  # nosec B101
    assert target.read_bytes() == b"payload"  # nosec B101
