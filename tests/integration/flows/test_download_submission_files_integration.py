import os
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
    _download_submission_files,
    _fetch_submission_metadata,
)
from canvas_code_correction.workspace import WorkspaceConfig, prepare_workspace

pytestmark = pytest.mark.usefixtures("clean_bucket", "mock_s3bucket_load")


@pytest.mark.integration
def test_download_submission_files_live(tmp_path: Path) -> None:
    token = os.getenv("CANVAS_API_TOKEN")
    course_id = 13122436
    assignment_id = os.getenv("CANVAS_TEST_ASSIGNMENT_ID", "59160606")
    if not token:
        pytest.skip("Canvas credentials not configured")

    api_url = os.getenv("CANVAS_API_URL", "https://canvas.instructure.com")

    bucket_block = os.getenv("CCC_ASSET_BUCKET_BLOCK", "local-rustfs")

    settings = Settings(
        canvas=CanvasSettings(
            api_url=api_url,
            token=SecretStr(token),
            course_id=course_id,
        ),
        assets=CourseAssetsSettings(
            bucket_block=bucket_block,
            path_prefix=os.getenv("CCC_ASSET_PREFIX", "dev"),
        ),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(
            root=Path(os.getenv("CCC_WORKSPACE_ROOT", "/tmp/ccc/workspaces")),
        ),
    )
    resources = canvas_resources.build_canvas_resources(settings)

    assignment = resources.course.get_assignment(int(assignment_id))
    submissions = assignment.get_submissions()
    try:
        first_submission = next(iter(submissions))
    except StopIteration:
        pytest.skip("No submissions available for integration test")

    submission_id = int(first_submission.user_id)

    payload = CorrectSubmissionPayload(
        assignment_id=int(assignment_id),
        submission_id=int(submission_id),
    )

    metadata = _fetch_submission_metadata(resources, payload)
    assert metadata.submission["user_id"] == submission_id

    files = _download_submission_files(resources, payload, tmp_path)

    assert isinstance(files, list)
    for file_path in files:
        assert file_path.exists()
        assert file_path.is_file()

    workspace_config = WorkspaceConfig(
        workspace_root=settings.workspace.root,
        bucket_block=settings.assets.bucket_block,
        path_prefix=settings.assets.path_prefix,
        assignment_id=payload.assignment_id,
        submission_id=payload.submission_id,
    )
    workspace_paths = prepare_workspace(workspace_config, files)

    assert workspace_paths.submission_dir.exists()
    assert workspace_paths.assets_dir.exists()
