"""Configuration models for Canvas Code Correction v2."""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class CanvasSettings(BaseModel):
    api_url: str = Field(..., alias="api_url")
    token: str
    course_id: int = Field(..., alias="course_id")


class RunnerSettings(BaseModel):
    docker_image: str = "ghcr.io/jakob1379/canvas-code-correction-grader:latest"
    network_disabled: bool = True
    memory_limit: str = "1g"
    cpu_limit: float = 1.0


class Settings(BaseModel):
    canvas: CanvasSettings
    runner: RunnerSettings = Field(default_factory=RunnerSettings)
    working_dir: Path = Field(default_factory=lambda: Path.cwd() / "var" / "runs")

    @classmethod
    def from_file(cls, path: Path | None) -> Settings:
        if path is None:
            return cls.from_env()
        data = tomllib.loads(path.read_bytes())
        return cls.model_validate(data)

    @classmethod
    def from_env(cls) -> Settings:
        raw: Mapping[str, Any] = {
            "canvas": {
                "api_url": os.getenv("CANVAS_API_URL", "https://canvas.example"),
                "token": os.getenv("CANVAS_API_TOKEN", "changeme"),
                "course_id": int(os.getenv("CANVAS_COURSE_ID", "0")),
            }
        }
        try:
            return cls.model_validate(raw)
        except ValidationError as exc:  # pragma: no cover - defensive
            raise RuntimeError("Invalid environment configuration") from exc
