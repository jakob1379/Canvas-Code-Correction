"""Configuration helpers for Canvas Code Correction."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl, SecretStr

from canvas_code_correction.prefect_blocks.canvas import CourseConfigBlock


class CanvasSettings(BaseModel):
    api_url: HttpUrl
    token: SecretStr
    course_id: int


class CourseAssetsSettings(BaseModel):
    bucket_block: str
    path_prefix: str = ""


class GraderSettings(BaseModel):
    docker_image: str | None = None
    work_pool_name: str | None = None
    env: dict[str, str] = Field(default_factory=dict)


class WorkspaceSettings(BaseModel):
    root: Path = Field(default_factory=lambda: Path("/tmp/ccc/workspaces"))


class Settings(BaseModel):
    canvas: CanvasSettings
    assets: CourseAssetsSettings
    grader: GraderSettings
    workspace: WorkspaceSettings

    @classmethod
    def from_course_block(cls, block_name: str) -> Settings:
        block = CourseConfigBlock.load(block_name)
        workspace_root = (
            Path(block.workspace_root).expanduser()
            if block.workspace_root
            else Path("/tmp/ccc/workspaces")
        )
        return cls(
            canvas=CanvasSettings(
                api_url=block.canvas_api_url,
                token=block.canvas_token,
                course_id=block.canvas_course_id,
            ),
            assets=CourseAssetsSettings(
                bucket_block=block.asset_bucket_block,
                path_prefix=block.asset_path_prefix,
            ),
            grader=GraderSettings(
                docker_image=block.grader_image,
                work_pool_name=block.work_pool_name,
                env=dict(block.grader_env),
            ),
            workspace=WorkspaceSettings(root=workspace_root),
        )


def resolve_settings_from_block(block_name: str) -> Settings:
    """Load :class:`Settings` from a Prefect course configuration block."""

    return Settings.from_course_block(block_name)
