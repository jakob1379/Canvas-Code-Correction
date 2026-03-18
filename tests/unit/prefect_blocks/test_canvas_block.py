from __future__ import annotations

import uuid

import pytest
from pydantic import SecretStr

from canvas_code_correction.prefect_blocks import CourseConfigBlock


@pytest.mark.local
def test_course_config_block_round_trip() -> None:
    block_name = f"test-ccc-course-{uuid.uuid4()}"
    block = CourseConfigBlock(
        canvas_api_url="https://canvas.example.com",  # type: ignore[assignment]
        canvas_token=SecretStr("token-value"),
        canvas_course_id=123,
        asset_bucket_block="course-assets-block",
        asset_path_prefix="courses/123",
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
        loaded = CourseConfigBlock.load(block_name)
        assert str(loaded.canvas_api_url).rstrip("/") == "https://canvas.example.com"  # type: ignore[attr-defined]
        assert loaded.canvas_token.get_secret_value() == "token-value"  # type: ignore[attr-defined]
        assert loaded.canvas_course_id == 123  # type: ignore[attr-defined]
        assert loaded.asset_bucket_block == "course-assets-block"  # type: ignore[attr-defined]
        assert loaded.asset_path_prefix == "courses/123"  # type: ignore[attr-defined]
        assert loaded.workspace_root == "/tmp/workspaces"  # type: ignore[attr-defined]
        assert loaded.grader_image == "example/image:latest"  # type: ignore[attr-defined]
        assert loaded.work_pool_name == "course-pool"  # type: ignore[attr-defined]
        assert loaded.grader_env == {"FOO": "BAR"}  # type: ignore[attr-defined]
        assert loaded.grader_command == ["sh", "run.sh"]  # type: ignore[attr-defined]
        assert loaded.grader_timeout_seconds == 600  # type: ignore[attr-defined]
        assert loaded.grader_memory_mb == 2048  # type: ignore[attr-defined]
        assert loaded.grader_upload_check_duplicates is False  # type: ignore[attr-defined]
        assert loaded.grader_upload_comments is False  # type: ignore[attr-defined]
        assert loaded.grader_upload_grades is True  # type: ignore[attr-defined]
        assert loaded.grader_upload_verbose is True  # type: ignore[attr-defined]
    finally:
        CourseConfigBlock.delete(block_name)
