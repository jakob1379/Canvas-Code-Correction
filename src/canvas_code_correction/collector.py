# ruff: noqa: D101,D107,B010,TC006,I001,RUF022
"""Compatibility wrapper for flow collector utilities."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Callable

import canvas_code_correction.flows.collector as _impl

import json
import logging
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ERRORS_LOG_FILENAME = _impl.ERRORS_LOG_FILENAME
CollectionMetadata = _impl.CollectionMetadata
GradingResult = _impl.GradingResult
CollectionResult = _impl.CollectionResult

logger = logging.getLogger(__name__)
P = ParamSpec("P")
R = TypeVar("R")


def _sync_impl() -> None:
    setattr(_impl, "Path", Path)
    setattr(_impl, "json", cast(Any, json))
    setattr(_impl, "logging", cast(Any, logging))
    setattr(_impl, "re", re)
    setattr(_impl, "zipfile", cast(Any, zipfile))
    setattr(_impl, "UTC", UTC)
    setattr(_impl, "datetime", datetime)
    setattr(_impl, "logger", logger)


def _wrap_method[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        _sync_impl()
        return func(*args, **kwargs)

    return wrapper


class ResultCollector(_impl.ResultCollector):
    def __init__(self, workspace_root: Path) -> None:
        _sync_impl()
        super().__init__(workspace_root)


for _name, _value in _impl.ResultCollector.__dict__.items():
    if _name.startswith("__"):
        continue
    if callable(_value):
        setattr(ResultCollector, _name, _wrap_method(_value))

__all__ = [
    "ERRORS_LOG_FILENAME",
    "CollectionMetadata",
    "GradingResult",
    "CollectionResult",
    "ResultCollector",
]
