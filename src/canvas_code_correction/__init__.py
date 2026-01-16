"""Canvas Code Correction public API surface."""

from __future__ import annotations

from .clients import (
    CanvasResources,
    build_canvas_resources,
    build_canvas_resources_from_course_block,
)
from .collector import (
    CollectionResult,
    GradingResult,
    ResultCollector,
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
from .runner import (
    ExecutionResult,
    GraderConfig,
    GraderExecutor,
    MountPoint,
    ResourceLimits,
    create_default_grader_config,
)
from .uploader import (
    CanvasUploader,
    UploadConfig,
    UploadResult,
    create_uploader_from_resources,
)

# CLI is available as canvas_code_correction.cli.app
# Importing it here would cause circular imports due to flow dependencies

__all__ = [
    "CanvasResources",
    "CanvasSettings",
    "CanvasUploader",
    "CollectionResult",
    "CorrectSubmissionPayload",
    "CourseAssetsSettings",
    "CourseConfigBlock",
    "ExecutionResult",
    "FlowArtifacts",
    "GraderConfig",
    "GraderExecutor",
    "GraderSettings",
    "GradingResult",
    "MountPoint",
    "ResourceLimits",
    "ResultCollector",
    "Settings",
    "UploadConfig",
    "UploadResult",
    "build_canvas_resources",
    "build_canvas_resources_from_course_block",
    "collect_results",
    "correct_submission_flow",
    "create_default_grader_config",
    "create_uploader_from_resources",
    "download_submission_files",
    "execute_grader",
    "fetch_submission_metadata",
    "post_grade",
    "resolve_settings_from_block",
    "upload_feedback",
]
