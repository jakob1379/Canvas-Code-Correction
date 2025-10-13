# bandit: disable=B101,B105,B106
"""Submission store tests."""

import zipfile
from pathlib import Path

from canvas_code_correction.submission_store import SubmissionStore


def test_submission_store_layout(tmp_path: Path) -> None:
    store = SubmissionStore(tmp_path)
    workspace = store.workspace(assignment_id=5, submission_id=12)

    attachment_path = store.attachment_path(workspace, "file.txt")

    assert attachment_path.parent.exists()  # nosec B101
    assert attachment_path.name == "file.txt"  # nosec B101


def test_stage_attachments_unzips_and_flattens(tmp_path: Path) -> None:
    store = SubmissionStore(tmp_path)
    workspace = store.workspace(assignment_id=3, submission_id=4)

    attachments_dir = store.attachments_dir(workspace)
    archive_path = attachments_dir / "archive.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/code.py", "print('hi')\n")
        archive.writestr("__MACOSX/._junk", "")

    text_path = attachments_dir / "notes.txt"
    text_path.write_text("hello\n", encoding="utf-8")

    files = store.stage_attachments(workspace, [archive_path, text_path])

    submission_root = workspace / "submission"
    code_file = submission_root / "code.py"
    note_file = submission_root / "notes.txt"

    assert code_file.exists()  # nosec B101
    assert note_file.exists()  # nosec B101
    assert code_file.read_text(encoding="utf-8") == "print('hi')\n"  # nosec B101

    relative = {path.relative_to(submission_root).as_posix() for path in files}
    assert relative == {"code.py", "notes.txt"}  # nosec B101
    assert not any("__MACOSX" in str(path) for path in submission_root.rglob("*"))  # nosec B101
