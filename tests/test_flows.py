# bandit: disable=B101,B105,B106
"""Flow orchestration tests."""

from pathlib import Path

from prefect.client.orchestration import SyncPrefectClient
from pytest import MonkeyPatch

from canvas_code_correction.config import Settings
from canvas_code_correction.flows import correct_submission
from canvas_code_correction.flows.correct_submission import correct_submission_flow


class _StubCanvasClient:
    def __init__(self) -> None:
        self._attachment_payload = {
            "id": 1,
            "filename": "submission.zip",
            "display_name": "submission.zip",
        }

    def __enter__(self) -> "_StubCanvasClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - no cleanup required
        return None

    @classmethod
    def from_settings(cls, *args, **kwargs) -> "_StubCanvasClient":  # noqa: D401 - simple wrapper
        return cls()

    def get_submission(self, assignment_id: int, submission_id: int, *, include=None):
        class _Submission:
            def __init__(
                self, submission_id: int, assignment_id: int, attachments: list[dict[str, object]]
            ) -> None:
                self.id = submission_id
                self.assignment_id = assignment_id
                self.user_id = 55
                self.attachments = attachments

        return _Submission(submission_id, assignment_id, [self._attachment_payload])

    def get_submission_files(self, submission) -> list[object]:
        class _File:
            def __init__(self, file_id: int, name: str) -> None:
                self.id = file_id
                self.filename = name

            def download(self, location: str) -> str:
                target = Path(location)
                target.write_bytes(b"stub")
                return location

        return [_File(self._attachment_payload["id"], self._attachment_payload["filename"])]

    def download_attachment(self, attachment, destination_dir: Path) -> Path:
        target = destination_dir / attachment.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"stub")
        return target


def test_correct_submission_flow(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("PREFECT_API_URL", "")
    monkeypatch.setattr(SyncPrefectClient, "raise_for_api_version_mismatch", lambda self: None)
    monkeypatch.setattr(correct_submission, "CanvasClient", _StubCanvasClient)

    settings = Settings.model_validate(
        {
            "canvas": {
                "api_url": "https://canvas.example",
                "token": "token",
                "course_id": 123,
            },
            "working_dir": tmp_path,
        }
    )

    result = correct_submission_flow.fn(
        assignment_id=1,
        submission_id=42,
        settings=settings,
    )

    assert result["status"] == "pending"  # nosec B101
    assert (tmp_path / "1" / "42").exists()  # nosec B101
    assert result["attachments"]  # nosec B101
    assert result["submission_files"]  # nosec B101
    assert (tmp_path / "1" / "42" / "submission" / "submission.zip").exists()  # nosec B101
