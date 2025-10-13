# bandit: disable=B101,B105,B106
"""Submission store tests."""

from __future__ import annotations

from pathlib import Path

from canvas_code_correction.canvas import Attachment
from canvas_code_correction.submission_store import SubmissionStore


def test_submission_store_layout(tmp_path: Path) -> None:
    store = SubmissionStore(tmp_path)
    workspace = store.workspace(assignment_id=5, submission_id=12)

    attachment = Attachment(id=1, filename="file.txt", url="https://example.com/file")
    attachment_path = store.attachment_path(workspace, attachment)

    assert attachment_path.parent.exists()  # nosec B101
    assert attachment_path.name == "file.txt"  # nosec B101
