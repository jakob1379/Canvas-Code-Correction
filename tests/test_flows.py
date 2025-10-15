# bandit: disable=B101,B105,B106
"""Flow orchestration tests."""

from pathlib import Path

from prefect.client.orchestration import SyncPrefectClient
from pytest import MonkeyPatch, approx

from canvas_code_correction.config import Settings
from canvas_code_correction.flows import correct_submission
from canvas_code_correction.flows.correct_submission import correct_submission_flow
from canvas_code_correction.runner_service import RunnerResult


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


class _StubRunnerService:
    def __init__(self, settings, logger=None) -> None:  # noqa: D401 - simple stub
        self.settings = settings
        self.logger = logger

    def run(self, workspace: Path) -> RunnerResult:
        results_file = workspace / "results.json"
        results_file.write_text("{}", encoding="utf-8")
        points_file = workspace / "points.txt"
        points_file.write_text("10\n", encoding="utf-8")
        comments_file = workspace / "comments.txt"
        comments_file.write_text("Great job!\n", encoding="utf-8")
        return RunnerResult(
            status="success",
            exit_code=0,
            stdout="ok",
            stderr="",
            results_file=results_file,
            points_file=points_file,
            comments_file=comments_file,
        )


class _StubCollected:
    def as_payload(self) -> dict[str, object]:
        return {
            "points": 10.0,
            "points_breakdown": [10.0],
            "comment": "Great job!\n",
            "feedback_zip": None,
            "metadata": {"custom": True},
        }


class _StubUploader:
    def __init__(self, client) -> None:  # noqa: D401
        self.client = client

    def upload_feedback(self, *args, **kwargs):  # noqa: D401
        return True, False

    def upload_grade(self, *args, **kwargs):  # noqa: D401
        return True


def test_correct_submission_flow(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("PREFECT_API_URL", "")
    monkeypatch.setattr(SyncPrefectClient, "raise_for_api_version_mismatch", lambda self: None)
    monkeypatch.setattr(correct_submission, "CanvasClient", _StubCanvasClient)
    monkeypatch.setattr(correct_submission, "RunnerService", _StubRunnerService)
    monkeypatch.setattr(
        correct_submission, "collect_results", lambda workspace, payload: _StubCollected()
    )
    monkeypatch.setattr(correct_submission, "Uploader", _StubUploader)

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

    assert result["status"] == "success"  # nosec B101
    assert (tmp_path / "1" / "42").exists()  # nosec B101
    assert result["attachments"]  # nosec B101
    assert result["submission_files"]  # nosec B101
    assert result["points"] == approx(10.0)  # nosec B101
    assert result["grade_uploaded"] is True  # nosec B101
    assert result["feedback_uploaded"] == {"comment_uploaded": True, "feedback_uploaded": False}  # nosec B101
