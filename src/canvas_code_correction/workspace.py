# ruff: noqa: D103,RUF022
"""Compatibility wrapper for flow workspace utilities."""

from __future__ import annotations

import shutil
import stat
from pathlib import Path
from uuid import uuid4

from prefect_aws.s3 import S3Bucket

import canvas_code_correction.flows.workspace as _impl

WorkspacePaths = _impl.WorkspacePaths
WorkspaceConfig = _impl.WorkspaceConfig


def _sync_impl() -> None:
    _impl.shutil = shutil
    _impl.stat = stat
    _impl.Path = Path
    _impl.uuid4 = uuid4
    _impl.S3Bucket = S3Bucket


def prepare_workspace(config: WorkspaceConfig, submission_files: list[Path]) -> WorkspacePaths:
    _sync_impl()
    return _impl.prepare_workspace(config, submission_files)


__all__ = ["WorkspacePaths", "WorkspaceConfig", "prepare_workspace"]
