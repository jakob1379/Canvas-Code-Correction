"""Canvas upload helpers for feedback and grades."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from canvasapi.submission import Submission

from .canvas import CanvasClient


@dataclass
class UploadOutcome:
    comment_uploaded: bool
    feedback_uploaded: bool
    grade_uploaded: bool


class Uploader:
    """High-level helper for uploading comments and grades to Canvas."""

    def __init__(self, client: CanvasClient) -> None:
        self._client = client

    def upload_feedback(
        self,
        assignment_id: int,
        submission_id: int,
        comment: str,
        feedback_zip: Path | None,
    ) -> tuple[bool, bool]:
        submission = self._client.get_submission(
            assignment_id,
            submission_id,
            include=["submission_comments"],
        )

        feedback_uploaded = False
        comment_uploaded = False

        if feedback_zip and feedback_zip.exists():
            filename = feedback_zip.name
            if not _has_attachment(submission, filename):
                submission.upload_comment(comment=comment or None, file=str(feedback_zip))
                feedback_uploaded = True
                comment_uploaded = True
            elif comment:
                submission.upload_comment(comment=comment)
                comment_uploaded = True
        elif comment:
            submission.upload_comment(comment=comment)
            comment_uploaded = True

        return comment_uploaded, feedback_uploaded

    def upload_grade(self, assignment_id: int, submission_id: int, points: float) -> bool:
        submission = self._client.get_submission(assignment_id, submission_id)
        submission.edit(submission={"posted_grade": str(points)})
        return True


def _has_attachment(submission: Submission, filename: str) -> bool:
    comments = getattr(submission, "submission_comments", []) or []
    for comment in comments:
        for attachment in comment.get("attachments", []) or []:
            if attachment.get("display_name") == filename:
                return True
    return False
