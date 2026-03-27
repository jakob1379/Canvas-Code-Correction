"""End-to-end test of the Canvas Code Correction pipeline."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.clients import canvas_resources
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
    _download_submission_files,
    _fetch_submission_metadata,
    collect_results,
    correct_submission_flow,
    download_submission_files,
    execute_grader,
    fetch_submission_metadata,
    post_grade,
    prepare_workspace_task,
    upload_feedback,
)
from canvas_code_correction.runner import (
    GraderConfig,
    GraderExecutor,
    ResourceLimits,
)
from canvas_code_correction.uploader import CanvasUploader, UploadConfig
from canvas_code_correction.workspace import WorkspaceConfig, prepare_workspace


class _FakeCanvasFile:
    """Canvas-like file object used by offline e2e flow tests."""

    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self.display_name = filename
        self._content = content

    def download(self, destination: str) -> None:
        Path(destination).write_bytes(self._content)


class _FakeSubmission:
    """Canvas-like submission used by offline e2e flow tests."""

    def __init__(self) -> None:
        self.attributes = {"id": 456, "user_id": "789", "workflow_state": "submitted"}
        self.attachments = [{"id": 101, "filename": "submission.py"}]
        self.submission_comments = []
        self.grade = "0"

    def refresh(self) -> _FakeSubmission:
        return self


class _FakeAssignment:
    """Canvas-like assignment used by offline e2e flow tests."""

    def __init__(self, submission: _FakeSubmission) -> None:
        self.attributes = {"id": 123, "name": "Project 1"}
        self._submission = submission

    def get_submission(
        self,
        submission_id: int,
        include: list[str] | None = None,
    ) -> _FakeSubmission:
        del include
        assert submission_id == 456
        return self._submission


class _FakeCourse:
    """Canvas-like course used by offline e2e flow tests."""

    def __init__(self, assignment: _FakeAssignment) -> None:
        self._assignment = assignment

    def get_assignment(self, assignment_id: int) -> _FakeAssignment:
        assert assignment_id == 123
        return self._assignment


class _FakeCanvas:
    """Canvas-like API client used by offline e2e flow tests."""

    def __init__(self, file_map: dict[int, _FakeCanvasFile]) -> None:
        self._file_map = file_map

    def get_file(self, file_id: int) -> _FakeCanvasFile:
        return self._file_map[file_id]


class _FakeBucket:
    """Local assets bucket adapter for offline e2e flow tests."""

    def download_folder(self, local_path: str, **_: str) -> None:
        Path(local_path).mkdir(parents=True, exist_ok=True)
        (Path(local_path) / "grader-asset.txt").write_text("asset")


def _build_offline_flow_settings(tmp_path: Path) -> Settings:
    return Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.test"),
            token=SecretStr("token"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(
            bucket_block="local-rustfs",
            path_prefix="course-assets",
        ),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(root=tmp_path / "workspaces"),
    )


@pytest.mark.e2e
def test_full_correction_pipeline(
    rustfs_config: dict[str, str],
    rustfs_available: bool,
    ensure_local_rustfs_block: bool,
    s3_client,
    ensure_test_bucket: str,
) -> None:
    """Test the full correction pipeline using real Canvas and RustFS."""
    # Skip if Canvas credentials not available
    token = os.getenv("CANVAS_API_TOKEN")
    course_id = os.getenv("CANVAS_COURSE_ID", "13121974")
    assignment_id = os.getenv("CANVAS_TEST_ASSIGNMENT_ID", "59160606")
    if not token:
        pytest.skip("Canvas credentials not configured")

    # Get a submission from the assignment
    api_url = HttpUrl(
        os.getenv("CANVAS_API_URL", "https://canvas.instructure.com"),
    )
    settings = Settings(
        canvas=CanvasSettings(
            api_url=api_url,
            token=SecretStr(token),
            course_id=int(course_id),
        ),
        assets=CourseAssetsSettings(
            bucket_block="local-rustfs",  # Should be registered via setup
            path_prefix=rustfs_config["prefix"],
        ),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(
            root=Path(os.getenv("CCC_WORKSPACE_ROOT", "/tmp/ccc/workspaces")),
        ),
    )

    # Build Canvas resources
    resources = canvas_resources.build_canvas_resources(settings)
    assignment = resources.course.get_assignment(int(assignment_id))
    submissions = assignment.get_submissions()
    try:
        first_submission = next(iter(submissions))
    except StopIteration:
        pytest.skip("No submissions available for e2e test")

    first_submission_user_id = first_submission.user_id
    submission_id = (
        int(first_submission_user_id) if isinstance(first_submission_user_id, (int, str)) else 0
    )
    print(f"Testing with submission {submission_id}")

    # Upload a test asset to RustFS bucket
    bucket_name = ensure_test_bucket
    prefix = rustfs_config["prefix"]
    asset_key = f"{prefix}/main.sh" if prefix else "main.sh"
    asset_content = b"""#!/bin/sh
echo "Running test grader"
echo "25.5" > points.txt
echo "Good job!" > comments.txt
"""
    s3_client.put_object(Bucket=bucket_name, Key=asset_key, Body=asset_content)
    print(f"Uploaded test asset to {bucket_name}/{asset_key}")

    # Create payload for flow tasks
    payload = CorrectSubmissionPayload(
        assignment_id=int(assignment_id),
        submission_id=submission_id,
    )

    # Fetch submission metadata
    metadata = _fetch_submission_metadata(resources, payload)
    raw_user_id = metadata.submission["user_id"]
    assert isinstance(raw_user_id, str | int)
    assert int(raw_user_id) == submission_id

    # Download submission files to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        files = _download_submission_files(resources, payload, tmp_path)
        assert isinstance(files, list)
        for file_path in files:
            assert file_path.exists()

        # Prepare workspace
        workspace_config = WorkspaceConfig(
            workspace_root=settings.workspace.root,
            bucket_block="local-rustfs",
            path_prefix=rustfs_config["prefix"],
            assignment_id=payload.assignment_id,
            submission_id=payload.submission_id,
        )
        workspace_paths = prepare_workspace(workspace_config, files)
        assert workspace_paths.submission_dir.exists()
        assert workspace_paths.assets_dir.exists()

        # Run grader (simple test using alpine image)
        config = GraderConfig(
            docker_image="alpine:latest",
            command=["sh", "/workspace/assets/main.sh"],
            working_directory=Path("/workspace/submission"),
            resource_limits=ResourceLimits(timeout_seconds=30),
        )
        executor = GraderExecutor()
        result = executor.execute_in_workspace(
            config,
            workspace_paths.submission_dir,
            workspace_paths.assets_dir,
        )
        assert result.exit_code == 0
        assert "Running test grader" in result.stdout

        # Verify grader outputs
        points_file = workspace_paths.submission_dir / "points.txt"
        comments_file = workspace_paths.submission_dir / "comments.txt"
        assert points_file.exists()
        assert comments_file.exists()
        assert points_file.read_text().strip() == "25.5"
        assert comments_file.read_text().strip() == "Good job!"

        # Test uploader (dry-run)
        uploader = CanvasUploader(first_submission)
        config = UploadConfig(dry_run=True, upload_comments=True, upload_grades=True)

        # Create feedback zip
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = Path(tmp.name)
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("points.txt", "25.5")
                zf.writestr("comments.txt", "Good job!")

        try:
            feedback_result = uploader.upload_feedback(zip_path, config=config)
            grade_result = uploader.upload_grade("25.5", config=config)
            assert feedback_result.success is True
            assert grade_result.success is True
            assert feedback_result.details.get("dry_run") is True
            assert grade_result.details.get("dry_run") is True
        finally:
            zip_path.unlink(missing_ok=True)

    print("✓ Full pipeline test passed")


@pytest.mark.e2e
def test_full_correction_pipeline_offline_contract(tmp_path: Path) -> None:
    """Test the full correction pipeline with mocked Canvas and storage services."""
    settings = _build_offline_flow_settings(tmp_path)
    submission = _FakeSubmission()
    assignment = _FakeAssignment(submission)
    resources = CanvasResources(
        canvas=cast(
            "Any",
            _FakeCanvas({101: _FakeCanvasFile("submission.py", b'print("hello")\n')}),
        ),
        course=cast("Any", _FakeCourse(assignment)),
        settings=settings,
    )

    payload = CorrectSubmissionPayload(assignment_id=123, submission_id=456)

    def fake_execute_in_workspace(
        _executor: GraderExecutor,
        *,
        config: GraderConfig,
        submission_dir: Path,
        assets_dir: Path,
    ) -> SimpleNamespace:
        del config, assets_dir
        (submission_dir / "points.txt").write_text("88.5\n")
        (submission_dir / "feedback.txt").write_text("looks good\n")
        (submission_dir / "errors.log").write_text("warning\n")
        return SimpleNamespace(
            exit_code=0,
            timed_out=False,
            duration_seconds=1.25,
            stdout="ok",
            stderr="",
            container_id="container-123",
        )

    with (
        patch("canvas_code_correction.workspace.S3Bucket.load", return_value=_FakeBucket()),
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
            download_dir=tmp_path / "downloads",
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
    assert result.results.feedback_upload.success is True
    assert "Dry run" in result.results.feedback_upload.message
    assert result.results.grade_upload.success is True
    assert "Dry run" in result.results.grade_upload.message
