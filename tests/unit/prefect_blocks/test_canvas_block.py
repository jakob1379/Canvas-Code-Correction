import uuid
from typing import cast

import pytest
from pydantic import HttpUrl, SecretStr

from canvas_code_correction.prefect_blocks import CourseConfigBlock

pytestmark = pytest.mark.usefixtures("prefect_testing_environment")


@pytest.mark.local
def test_course_config_block_round_trip() -> None:
    block_name = f"test-ccc-course-{uuid.uuid4()}"
    block = CourseConfigBlock(
        canvas_api_url=HttpUrl("https://canvas.example.com"),
        canvas_token=SecretStr("token-value"),
        canvas_course_id=123,
        asset_bucket_block="course-assets-block",
        asset_path_prefix="courses/123",
        assignment_asset_prefixes={123: "courses/123/assignments/123/assets"},
        storage_auth_mode="shared_environment",
        workspace_root="/tmp/workspaces",
        grader_image="example/image:latest",
        work_pool_name="course-pool",
        grader_env={"FOO": "BAR"},
        grader_command=["sh", "run.sh"],
        grader_timeout_seconds=600,
        grader_memory_mb=2048,
        grader_upload_check_duplicates=False,
        grader_upload_comments=False,
        grader_upload_grades=True,
        grader_upload_verbose=True,
    )

    block.save(block_name, overwrite=True)
    try:
        loaded = cast("CourseConfigBlock", CourseConfigBlock.load(block_name))
        assert str(loaded.canvas_api_url).rstrip("/") == "https://canvas.example.com"
        assert loaded.canvas_token.get_secret_value() == "token-value"
        assert loaded.canvas_course_id == 123
        assert loaded.asset_bucket_block == "course-assets-block"
        assert loaded.asset_path_prefix == "courses/123"
        assert loaded.assignment_asset_prefixes == {
            123: "courses/123/assignments/123/assets",
        }
        assert loaded.storage_auth_mode == "shared_environment"
        assert loaded.workspace_root == "/tmp/workspaces"
        assert loaded.grader_image == "example/image:latest"
        assert loaded.work_pool_name == "course-pool"
        assert loaded.grader_env == {"FOO": "BAR"}
        assert loaded.grader_command == ["sh", "run.sh"]
        assert loaded.grader_timeout_seconds == 600
        assert loaded.grader_memory_mb == 2048
        assert loaded.grader_upload_check_duplicates is False
        assert loaded.grader_upload_comments is False
        assert loaded.grader_upload_grades is True
        assert loaded.grader_upload_verbose is True
    finally:
        CourseConfigBlock.delete(block_name)
