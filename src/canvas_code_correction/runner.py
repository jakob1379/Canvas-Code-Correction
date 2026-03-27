# ruff: noqa: D101,D107,B010,TC006,I001,RUF022
"""Compatibility wrapper for flow runner utilities."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, cast

import contextlib
import time
from pathlib import Path

import docker
import requests
from docker.errors import DockerException, ImageNotFound
from docker.types import Mount

import canvas_code_correction.flows.runner as _impl

if TYPE_CHECKING:
    from collections.abc import Callable

ExecutionResult = _impl.ExecutionResult
ResourceLimits = _impl.ResourceLimits
GraderConfig = _impl.GraderConfig
MountPoint = _impl.MountPoint
ContainerRunKwargs = _impl.ContainerRunKwargs
P = ParamSpec("P")
R = TypeVar("R")


def _sync_impl() -> None:
    setattr(_impl, "contextlib", contextlib)
    setattr(_impl, "time", time)
    setattr(_impl, "Path", Path)
    setattr(_impl, "docker", cast(Any, docker))
    setattr(_impl, "requests", cast(Any, requests))
    setattr(_impl, "DockerException", DockerException)
    setattr(_impl, "ImageNotFound", ImageNotFound)
    setattr(_impl, "Mount", Mount)


def _wrap_method[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        _sync_impl()
        return func(*args, **kwargs)

    return wrapper


class GraderExecutor(_impl.GraderExecutor):
    def __init__(self, docker_client: docker.DockerClient | None = None) -> None:
        _sync_impl()
        super().__init__(docker_client)


for _name, _value in _impl.GraderExecutor.__dict__.items():
    if _name.startswith("__"):
        continue
    if callable(_value):
        setattr(GraderExecutor, _name, _wrap_method(_value))


create_default_grader_config = _impl.create_default_grader_config


__all__ = [
    "ExecutionResult",
    "ResourceLimits",
    "GraderConfig",
    "MountPoint",
    "ContainerRunKwargs",
    "GraderExecutor",
    "create_default_grader_config",
]
