from __future__ import annotations

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


@pytest.mark.integration
def test_build_canvas_resources_live() -> None:
    token = os.getenv("CANVAS_API_TOKEN")
    course_id = os.getenv("CANVAS_COURSE_ID")
    if not token or not course_id:
        pytest.skip("Canvas credentials not configured")

    api_url = os.getenv("CANVAS_API_URL", "https://canvas.instructure.com")

    settings = Settings(
        canvas=CanvasSettings(
            api_url=api_url,
            token=SecretStr(token),
            course_id=int(course_id),
        ),
        assets=CourseAssetsSettings(
            bucket_block=os.getenv("CCC_ASSET_BUCKET_BLOCK", "course-assets-block"),
            path_prefix=os.getenv("CCC_ASSET_PREFIX", "dev"),
        ),
        grader=GraderSettings(),
        workspace=WorkspaceSettings(
            root=Path(os.getenv("CCC_WORKSPACE_ROOT", "/tmp/ccc/workspaces"))
        ),
    )

    resources = canvas_resources.build_canvas_resources(settings)

    assert resources.course.id == int(course_id)
    assert resources.canvas is not None
