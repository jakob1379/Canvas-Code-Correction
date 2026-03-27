"""Compatibility wrapper for flow workspace utilities."""

from __future__ import annotations

import canvas_code_correction.flows.workspace as _impl

S3Bucket = _impl.S3Bucket
WorkspaceConfig = _impl.WorkspaceConfig
WorkspacePaths = _impl.WorkspacePaths
prepare_workspace = _impl.prepare_workspace


__all__ = ["S3Bucket", "WorkspaceConfig", "WorkspacePaths", "prepare_workspace"]
