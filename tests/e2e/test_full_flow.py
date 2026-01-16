"""End-to-end test of the Canvas Code Correction pipeline."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path

import pytest
from pydantic import SecretStr

from canvas_code_correction.clients import canvas_resources
from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WorkspaceSettings,
)
from canvas_code_correction.flows.correction import (
    CorrectSubmissionPayload,
    download_submission_files,
    fetch_submission_metadata,
)
from canvas_code_correction.runner import (
    GraderConfig,
    GraderExecutor,
    ResourceLimits,
)
from canvas_code_correction.uploader import CanvasUploader, UploadConfig
from canvas_code_correction.workspace import WorkspaceConfig, prepare_workspace


@pytest.mark.e2e
def test_full_correction_pipeline(
    rustfs_config: dict[str, str],
    rustfs_available: bool,
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
    api_url = os.getenv("CANVAS_API_URL", "https://canvas.instructure.com")
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
            root=Path(os.getenv("CCC_WORKSPACE_ROOT", "/tmp/ccc/workspaces"))
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

    submission_id = int(first_submission.user_id)
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
    metadata = fetch_submission_metadata.fn(resources, payload)
    assert metadata["submission"]["user_id"] == submission_id

    # Download submission files to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        files = download_submission_files.fn(resources, payload, tmp_path)
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
            command=["sh", "main.sh"],
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
