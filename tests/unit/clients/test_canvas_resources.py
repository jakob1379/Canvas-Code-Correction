from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from pydantic import SecretStr

from canvas_code_correction.clients import canvas_resources
from canvas_code_correction.config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    WorkspaceSettings,
)
from canvas_code_correction.prefect_blocks import CourseConfigBlock


def _make_settings() -> Settings:
    return Settings(
        canvas=CanvasSettings(
            api_url="https://canvas.example.com",
            token=SecretStr("secret-token"),
            course_id=42,
        ),
        assets=CourseAssetsSettings(bucket_block="course-assets-block", path_prefix="prefix"),
        grader=GraderSettings(docker_image="example/image:latest"),
        workspace=WorkspaceSettings(root=Path("/tmp/workspaces")),
    )


def test_build_canvas_resources_uses_settings(monkeypatch):
    fake_canvas = Mock()
    fake_course = Mock()
    fake_canvas.get_course.return_value = fake_course

    canvas_ctor = Mock(return_value=fake_canvas)
    monkeypatch.setattr(canvas_resources, "Canvas", canvas_ctor)

    settings = _make_settings()

    resources = canvas_resources.build_canvas_resources(settings)

    canvas_ctor.assert_called_once()
    called_url, called_token = canvas_ctor.call_args.args
    assert called_url.rstrip("/") == "https://canvas.example.com"
    assert called_token == "secret-token"
    fake_canvas.get_course.assert_called_once_with(42)
    assert resources.canvas is fake_canvas
    assert resources.course is fake_course


def test_settings_from_course_block(monkeypatch):
    block = CourseConfigBlock(
        canvas_api_url="https://block.canvas.test",
        canvas_token=SecretStr("block-token"),
        canvas_course_id=99,
        asset_bucket_block="bucket-block",
        asset_path_prefix="courses/99",
        workspace_root="/tmp/workspaces",
        grader_image="block/image:latest",
        work_pool_name="course-pool",
        grader_env={"FOO": "BAR"},
    )

    def fake_load(cls, block_name: str) -> CourseConfigBlock:  # type: ignore[override]
        assert block_name == "my-block"
        return block

    monkeypatch.setattr(CourseConfigBlock, "load", classmethod(fake_load))

    settings = Settings.from_course_block("my-block")

    assert str(settings.canvas.api_url).rstrip("/") == "https://block.canvas.test"
    assert settings.canvas.token.get_secret_value() == "block-token"
    assert settings.canvas.course_id == 99
    assert settings.assets.bucket_block == "bucket-block"
    assert settings.assets.path_prefix == "courses/99"
    assert settings.grader.docker_image == "block/image:latest"
    assert settings.grader.work_pool_name == "course-pool"
    assert settings.grader.env == {"FOO": "BAR"}
    assert settings.workspace.root == Path("/tmp/workspaces")
