"""Compatibility wrapper for flow uploader utilities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import canvas_code_correction.flows.uploader as _impl

if TYPE_CHECKING:
    from canvas_code_correction.clients.canvas_resources import CanvasResources

AttachmentWithUrl = _impl.AttachmentWithUrl
SubmissionCommentInfo = _impl.SubmissionCommentInfo
UploadBatchResult = _impl.UploadBatchResult
UploadResult = _impl.UploadResult
UploadConfig = _impl.UploadConfig
UPLOAD_EXCEPTION_TYPES = _impl.UPLOAD_EXCEPTION_TYPES
logger = logging.getLogger(__name__)

CanvasUploader = _impl.CanvasUploader


def create_uploader_from_resources(
    resources: CanvasResources,
    assignment_id: int,
    submission_id: int,
) -> CanvasUploader:
    """Create an uploader from Canvas resources."""
    return _impl.create_uploader_from_resources(
        resources,
        assignment_id,
        submission_id,
    )


__all__ = [
    "UPLOAD_EXCEPTION_TYPES",
    "AttachmentWithUrl",
    "CanvasUploader",
    "SubmissionCommentInfo",
    "UploadBatchResult",
    "UploadConfig",
    "UploadResult",
    "create_uploader_from_resources",
]
