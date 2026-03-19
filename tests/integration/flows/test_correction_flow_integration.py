from __future__ import annotations

import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from canvas_code_correction.clients.canvas_resources import CanvasResources
from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WorkspaceSettings,
)
from canvas_code_correction.flows.correction import (
    CorrectSubmissionPayload,
    collect_results,
    correct_submission_flow,
    download_submission_files,
    execute_grader,
    fetch_submission_metadata,
    post_grade,
    prepare_workspace_task,
    upload_feedback,
)


class FakeCanvasFile:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self.display_name = filename
        self._content = content

    def download(self, destination: str) -> None:
        Path(destination).write_bytes(self._content)


class FakeSubmission:
    def __init__(self) -> None:
        self.attributes = {"id": 456, "user_id": "789", "workflow_state": "submitted"}
        self.attachments = [{"id": 101, "filename": "submission.py"}]
        self.submission_comments = []
        self.grade = "0"

    def refresh(self) -> FakeSubmission:
        return self


class FakeAssignment:
    def __init__(self, submission: FakeSubmission) -> None:
        self.attributes = {"id": 123, "name": "Project 1"}
        self._submission = submission

    def get_submission(
        self,
        submission_id: int,
        include: list[str] | None = None,
    ) -> FakeSubmission:
        del include
        assert submission_id == 456
        return self._submission


class FakeCourse:
    def __init__(self, assignment: FakeAssignment) -> None:
        self._assignment = assignment

    def get_assignment(self, assignment_id: int) -> FakeAssignment:
        assert assignment_id == 123
        return self._assignment


class FakeCanvas:
    def __init__(self, file_map: dict[int, FakeCanvasFile]) -> None:
        self._file_map = file_map

    def get_file(self, file_id: int) -> FakeCanvasFile:
        return self._file_map[file_id]


class FakeBucket:
    def download_folder(self, local_path: str, **_: str) -> None:
        assets_dir = Path(local_path)
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "grader-asset.txt").write_text("asset")


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        canvas=CanvasSettings(
            api_url="https://canvas.test",
            token=SecretStr("token"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="local-rustfs", path_prefix="course-assets"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(root=tmp_path / "workspaces"),
    )


@pytest.mark.integration
def test_correct_submission_flow_runs_offline_contract(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    submission = FakeSubmission()
    assignment = FakeAssignment(submission)
    resources = CanvasResources(
        canvas=FakeCanvas({101: FakeCanvasFile("submission.py", b'print("hello")\n')}),
        course=FakeCourse(assignment),
        settings=settings,
    )
    payload = CorrectSubmissionPayload(assignment_id=123, submission_id=456)

    def fake_execute_in_workspace(
        _executor,
        *,
        config,
        submission_dir,
        assets_dir,
    ) -> SimpleNamespace:
        del config, assets_dir
        (submission_dir / "points.txt").write_text("88.5\n")
        (submission_dir / "feedback.txt").write_text("Looks good\n")
        (submission_dir / "errors.log").write_text("warning\n")
        with zipfile.ZipFile(submission_dir / "artifacts.zip", "w") as archive:
            archive.writestr("report.txt", "ok")
        return SimpleNamespace(
            exit_code=0,
            timed_out=False,
            duration_seconds=1.25,
            stdout="ok",
            stderr="",
            container_id="container-123",
        )

    with (
        patch("canvas_code_correction.workspace.S3Bucket.load", return_value=FakeBucket()),
        patch(
            "canvas_code_correction.flows.correction.fetch_submission_metadata",
            new=fetch_submission_metadata.fn,
        ),
        patch(
            "canvas_code_correction.flows.correction.download_submission_files",
            new=download_submission_files.fn,
        ),
        patch(
            "canvas_code_correction.flows.correction.prepare_workspace_task",
            new=prepare_workspace_task.fn,
        ),
        patch(
            "canvas_code_correction.flows.correction.execute_grader",
            new=execute_grader.fn,
        ),
        patch(
            "canvas_code_correction.flows.correction.collect_results",
            new=collect_results.fn,
        ),
        patch(
            "canvas_code_correction.flows.correction.upload_feedback",
            new=upload_feedback.fn,
        ),
        patch(
            "canvas_code_correction.flows.correction.post_grade",
            new=post_grade.fn,
        ),
        patch(
            "canvas_code_correction.flows.correction.GraderExecutor.execute_in_workspace",
            new=fake_execute_in_workspace,
        ),
    ):
        result = correct_submission_flow.fn(
            payload,
            settings,
            resources=resources,
            download_dir=None,
            dry_run=True,
        )

    assert result.submission_metadata.assignment["id"] == 123
    assert result.submission_metadata.submission["id"] == 456
    assert len(result.downloaded_files) == 1
    assert result.downloaded_files[0].name == "submission.py"
    assert result.downloaded_files[0].exists()
    assert result.workspace is not None
    assert (result.workspace.submission_dir / "submission.py").exists()
    assert (result.workspace.assets_dir / "grader-asset.txt").exists()
    assert result.results.execution.exit_code == 0
    assert result.results.collection.points == pytest.approx(88.5)
    assert result.results.collection.feedback_zip_path is not None
    assert result.results.collection.feedback_zip_path.exists()
    assert result.results.feedback_upload.success is True
    assert "Dry run" in result.results.feedback_upload.message
    assert result.results.grade_upload.success is True
    assert "Dry run" in result.results.grade_upload.message
