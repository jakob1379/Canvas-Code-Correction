"""Canvas Code Correction public API surface."""

from __future__ import annotations

from .clients import (
    CanvasResources,
    build_canvas_resources,
    build_canvas_resources_from_course_block,
)
from .config import (
    CanvasSettings,
    CourseAssetsSettings,
    GraderSettings,
    Settings,
    resolve_settings_from_block,
)
from .flows import (
    CorrectSubmissionPayload,
    FlowArtifacts,
    collect_results,
    correct_submission_flow,
    download_submission_files,
    execute_grader,
    fetch_submission_metadata,
    post_grade,
    upload_feedback,
)
from .prefect_blocks import CourseConfigBlock

__all__ = [
    "CanvasResources",
    "build_canvas_resources",
    "build_canvas_resources_from_course_block",
    "CanvasSettings",
    "CourseAssetsSettings",
    "GraderSettings",
    "Settings",
    "resolve_settings_from_block",
    "CourseConfigBlock",
    "CorrectSubmissionPayload",
    "FlowArtifacts",
    "collect_results",
    "correct_submission_flow",
    "download_submission_files",
    "execute_grader",
    "fetch_submission_metadata",
    "post_grade",
    "upload_feedback",
]
