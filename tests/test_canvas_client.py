# bandit: disable=B101,B105,B106
"""Tests for the Canvas client."""

from __future__ import annotations

from pathlib import Path

import httpx

from canvas_code_correction.canvas import CanvasClient


def test_get_submission_and_download(tmp_path: Path) -> None:
    submission_url = "/api/v1/courses/1/assignments/2/submissions/3"
    attachment_download = "/api/v1/files/10/download"

    def responder(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == submission_url:
            return httpx.Response(
                status_code=200,
                json={
                    "id": 3,
                    "user_id": 7,
                    "assignment_id": 2,
                    "attachments": [
                        {
                            "id": 10,
                            "filename": "submission.zip",
                            "url": f"https://canvas.example{attachment_download}",
                        }
                    ],
                },
            )

        if request.method == "GET" and request.url.path == attachment_download:
            return httpx.Response(status_code=200, content=b"payload")

        raise AssertionError(f"Unexpected request {request.method} {request.url!s}")

    transport = httpx.MockTransport(responder)

    with CanvasClient(
        base_url="https://canvas.example",
        token="token",  # nosec B106
        course_id=1,
        transport=transport,
    ) as client:
        submission = client.get_submission(
            assignment_id=2,
            submission_id=3,
            include=["attachments"],
        )
        assert submission.id == 3  # nosec B101
        assert submission.attachments  # nosec B101

        attachment = submission.attachments[0]
        target = client.download_attachment(attachment, tmp_path)

    assert target.name == "submission.zip"  # nosec B101
    assert target.read_bytes() == b"payload"  # nosec B101
