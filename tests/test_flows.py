# bandit: disable=B101,B105,B106
"""Flow orchestration tests."""

from pathlib import Path

from prefect.client.orchestration import SyncPrefectClient
from pytest import MonkeyPatch

from canvas_code_correction.canvas import Attachment, Submission
from canvas_code_correction.config import Settings
from canvas_code_correction.flows import correct_submission
from canvas_code_correction.flows.correct_submission import correct_submission_flow


class _StubCanvasClient:
    def __init__(self) -> None:
        self._attachment = Attachment(
            id=1,
            filename="submission.zip",
            url="https://canvas.example/api/v1/files/1/download",
        )

    def __enter__(self) -> "_StubCanvasClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - no cleanup required
        return None

    @classmethod
    def from_settings(cls, *args, **kwargs) -> "_StubCanvasClient":  # noqa: D401 - simple wrapper
        return cls()

    def get_submission(self, assignment_id: int, submission_id: int, *, include=None) -> Submission:
        return Submission(
            id=submission_id,
            user_id=55,
            assignment_id=assignment_id,
            attachments=[self._attachment],
        )

    def download_attachment(self, attachment: Attachment, destination_dir: Path) -> Path:
        target = destination_dir / attachment.suggested_name
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
