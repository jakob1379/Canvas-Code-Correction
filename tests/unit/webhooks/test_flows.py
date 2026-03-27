from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import HttpUrl, SecretStr, ValidationError

from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WorkspaceSettings,
)
from canvas_code_correction.flows.correction import (
    CollectedResults,
    CorrectionResults,
    CorrectionUploads,
    ExecutionSummary,
    FeedbackUploadResult,
    FlowArtifacts,
    GradeUploadResult,
    SubmissionMetadata,
)
from canvas_code_correction.webhooks.flows import (
    WebhookCourseContext,
    WebhookFlowSummary,
    webhook_correction_flow,
)
from canvas_code_correction.workspace import WorkspacePaths


def _make_settings() -> Settings:
    return Settings(
        canvas=CanvasSettings(
            api_url=HttpUrl("https://canvas.test"),
            token=SecretStr("token"),
            course_id=1,
        ),
        assets=CourseAssetsSettings(bucket_block="bucket-block", path_prefix="prefix"),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(root=Path("/tmp/workspaces")),
    )


@pytest.mark.local
def test_webhook_correction_flow_returns_execution_summary(tmp_path: Path) -> None:
    settings = _make_settings()
    settings_payload = settings.to_flow_payload()
    artifacts = FlowArtifacts(
        submission_metadata=SubmissionMetadata(
            assignment={"id": 123},
            submission={"id": 456},
        ),
        downloaded_files=[tmp_path / "submission.py", tmp_path / "feedback.txt"],
        workspace=WorkspacePaths(
            root=tmp_path / "workspace",
            submission_dir=tmp_path / "workspace" / "submission",
            assets_dir=tmp_path / "workspace" / "assets",
        ),
        results=CorrectionResults(
            execution=ExecutionSummary(
                exit_code=0,
                timed_out=False,
                duration_seconds=1.0,
                stdout="",
                stderr="",
                container_id=None,
            ),
            collection=CollectedResults(
                points=None,
                comments="",
                points_file_content="",
                feedback_zip_path=tmp_path / "feedback.zip",
                artifacts_zip_path=None,
                errors_log_path=None,
                discovered_files=[],
                validation_issues=[],
                metadata={},
            ),
            feedback_upload=FeedbackUploadResult(
                success=True,
                message="uploaded",
                duplicate=False,
                comment_posted=True,
                details=None,
            ),
            grade_upload=GradeUploadResult(
                success=True,
                message="posted",
                duplicate=False,
                grade_posted=True,
                details=None,
            ),
        ),
        uploads=CorrectionUploads(
            feedback=FeedbackUploadResult(
                success=True,
                message="uploaded",
                duplicate=False,
                comment_posted=True,
                details=None,
            ),
            grade=GradeUploadResult(
                success=True,
                message="posted",
                duplicate=False,
                grade_posted=True,
                details=None,
            ),
        ),
    )

    with (
        patch(
            "canvas_code_correction.webhooks.flows.correct_submission_flow",
            return_value=artifacts,
        ) as mock_correct_submission,
    ):
        result = webhook_correction_flow.fn(
            course=WebhookCourseContext(
                course_block="course-block",
                settings=settings_payload,
            ),
            submission={
                "assignment_id": 123,
                "submission_id": 456,
            },
            download_dir=tmp_path / "downloads",
            dry_run=True,
        )

    assert result == WebhookFlowSummary(
        course_block="course-block",
        assignment_id=123,
        submission_id=456,
        submission_metadata_keys=["assignment", "submission"],
        downloaded_files_count=2,
        workspace=str(tmp_path / "workspace"),
        results_keys=["execution", "collection", "feedback_upload", "grade_upload"],
    )
    mock_correct_submission.assert_called_once()


@pytest.mark.local
def test_webhook_correction_flow_validates_submission_mapping(tmp_path: Path) -> None:
    settings = _make_settings()

    with pytest.raises(ValidationError):
        webhook_correction_flow.fn(
            course=WebhookCourseContext(
                course_block="course-block",
                settings=settings.to_flow_payload(),
            ),
            submission={
                "assignment_id": "not-an-int",
                "submission_id": 456,
            },
            download_dir=tmp_path / "downloads",
        )
