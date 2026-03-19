import os
import tempfile
import zipfile
from pathlib import Path

import pytest
from canvasapi.exceptions import CanvasException
from pydantic import SecretStr
from requests.exceptions import RequestException

from canvas_code_correction.clients import canvas_resources
from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WorkspaceSettings,
)
from canvas_code_correction.uploader import CanvasUploader, UploadConfig


def build_resources_or_skip():
    """Build Canvas resources or skip test if credentials invalid."""
    token = os.getenv("CANVAS_API_TOKEN")
    course_id = 13122436
    assignment_id = os.getenv("CANVAS_TEST_ASSIGNMENT_ID", "59160606")
    if not token:
        pytest.skip("Canvas credentials not configured")

    api_url = os.getenv("CANVAS_API_URL", "https://canvas.instructure.com")

    settings = Settings(
        canvas=CanvasSettings(
            api_url=api_url,
            token=SecretStr(token),
            course_id=course_id,
        ),
        assets=CourseAssetsSettings(bucket_block="dummy", path_prefix=""),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(root=Path("/tmp")),
    )
    try:
        resources = canvas_resources.build_canvas_resources(settings)
    except (CanvasException, RequestException) as e:
        # If token is expired or invalid, skip with appropriate message
        error_msg = str(e).lower()
        if "expired" in error_msg or "invalid" in error_msg or "unauthorized" in error_msg:
            pytest.skip(f"Canvas credentials invalid: {e}")
        raise

    assignment = resources.course.get_assignment(int(assignment_id))
    submissions = assignment.get_submissions()
    try:
        submission = next(iter(submissions))
    except StopIteration:
        pytest.skip("No submissions available for integration test")

    return resources, submission


@pytest.mark.integration
def test_uploader_initialization_live() -> None:
    """Test that we can initialize CanvasUploader with a real submission."""
    _, submission = build_resources_or_skip()

    uploader = CanvasUploader(submission)
    assert uploader.submission is submission
    assert uploader.submission.id == submission.id


@pytest.mark.integration
def test_upload_feedback_dry_run_live() -> None:
    """Test feedback upload dry-run with real Canvas API (no side effects)."""
    _, submission = build_resources_or_skip()

    uploader = CanvasUploader(submission)

    # Create a dummy feedback zip file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        with zipfile.ZipFile(tmp_path, "w") as zf:
            zf.writestr("feedback.txt", "Test feedback content")

    try:
        config = UploadConfig(dry_run=True, upload_comments=True)
        result = uploader.upload_feedback(tmp_path, config=config)
        assert result.success is True
        assert result.details.get("dry_run") is True
        assert "dry run" in result.message.lower()
        assert result.duplicate is False  # Should not check duplicates in dry_run
    finally:
        tmp_path.unlink(missing_ok=True)


@pytest.mark.integration
def test_upload_grade_dry_run_live() -> None:
    """Test grade upload dry-run with real Canvas API (no side effects)."""
    _, submission = build_resources_or_skip()

    uploader = CanvasUploader(submission)

    config = UploadConfig(dry_run=True, upload_grades=True)
    result = uploader.upload_grade("85.5", config=config)
    assert result.success is True
    assert result.details.get("dry_run") is True
    assert "dry run" in result.message.lower()
    assert result.duplicate is False


@pytest.mark.integration
def test_upload_feedback_and_grade_dry_run_live() -> None:
    """Test combined feedback and grade upload dry-run."""
    _, submission = build_resources_or_skip()

    uploader = CanvasUploader(submission)

    # Create dummy feedback zip
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        with zipfile.ZipFile(tmp_path, "w") as zf:
            zf.writestr("feedback.txt", "Test feedback content")

    try:
        config = UploadConfig(dry_run=True, upload_comments=True, upload_grades=True)
        batch_result = uploader.upload_feedback_and_grade(
            feedback_file=tmp_path,
            grade="90.0",
            config=config,
        )
        assert batch_result.feedback is not None
        assert batch_result.grade is not None
        assert batch_result.feedback.success is True
        assert batch_result.grade.success is True
        assert batch_result.feedback.details.get("dry_run") is True
        assert batch_result.grade.details.get("dry_run") is True
    finally:
        tmp_path.unlink(missing_ok=True)
