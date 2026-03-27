# ruff: noqa: D101,D103,D107,B010,TC006,I001,RUF022
"""Compatibility wrapper for flow uploader utilities."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, cast

import hashlib
import logging
import tempfile
from pathlib import Path

import requests

import canvas_code_correction.flows.uploader as _impl

if TYPE_CHECKING:
    from collections.abc import Callable
    from canvasapi.submission import Submission

    from canvas_code_correction.clients.canvas_resources import CanvasResources

AttachmentWithUrl = _impl.AttachmentWithUrl
SubmissionCommentInfo = _impl.SubmissionCommentInfo
UploadBatchResult = _impl.UploadBatchResult
UploadResult = _impl.UploadResult
UploadConfig = _impl.UploadConfig
UPLOAD_EXCEPTION_TYPES = _impl.UPLOAD_EXCEPTION_TYPES
logger = logging.getLogger(__name__)
P = ParamSpec("P")
R = TypeVar("R")


def _sync_impl() -> None:
    setattr(_impl, "hashlib", hashlib)
    setattr(_impl, "logging", cast(Any, logging))
    setattr(_impl, "tempfile", tempfile)
    setattr(_impl, "Path", Path)
    setattr(_impl, "requests", cast(Any, requests))
    setattr(_impl, "logger", logger)
    setattr(_impl, "UPLOAD_EXCEPTION_TYPES", UPLOAD_EXCEPTION_TYPES)


def _wrap_method[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        _sync_impl()
        return func(*args, **kwargs)

    return wrapper


class CanvasUploader(_impl.CanvasUploader):
    def __init__(self, submission: Submission) -> None:
        _sync_impl()
        super().__init__(submission)


for _name, _value in _impl.CanvasUploader.__dict__.items():
    if _name.startswith("__"):
        continue
    if isinstance(_value, staticmethod):
        setattr(CanvasUploader, _name, staticmethod(_value.__func__))
        continue
    if callable(_value):
        setattr(CanvasUploader, _name, _wrap_method(_value))


def create_uploader_from_resources(
    resources: CanvasResources,
    assignment_id: int,
    submission_id: int,
) -> CanvasUploader:
    _sync_impl()
    return cast(
        CanvasUploader,
        _impl.create_uploader_from_resources(
            resources,
            assignment_id,
            submission_id,
        ),
    )


__all__ = [
    "AttachmentWithUrl",
    "SubmissionCommentInfo",
    "UploadBatchResult",
    "UploadResult",
    "UploadConfig",
    "UPLOAD_EXCEPTION_TYPES",
    "CanvasUploader",
    "create_uploader_from_resources",
]
