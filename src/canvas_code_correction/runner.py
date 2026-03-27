"""Compatibility wrapper for flow runner utilities."""

from __future__ import annotations

import canvas_code_correction.flows.runner as _impl

ExecutionResult = _impl.ExecutionResult
ResourceLimits = _impl.ResourceLimits
GraderConfig = _impl.GraderConfig
MountPoint = _impl.MountPoint
ContainerRunKwargs = _impl.ContainerRunKwargs

GraderExecutor = _impl.GraderExecutor
DockerException = _impl.DockerException
ImageNotFound = _impl.ImageNotFound
Mount = _impl.Mount


create_default_grader_config = _impl.create_default_grader_config


__all__ = [
    "ContainerRunKwargs",
    "ExecutionResult",
    "GraderConfig",
    "GraderExecutor",
    "MountPoint",
    "ResourceLimits",
    "create_default_grader_config",
]
