"""Configuration models for Canvas Code Correction v2."""

from __future__ import annotations

import os
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, ClassVar

from dotenv import dotenv_values, load_dotenv
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

    ENV_URL_KEYS: ClassVar[tuple[str, ...]] = ("CANVAS_API_URL",)
    ENV_TOKEN_KEYS: ClassVar[tuple[str, ...]] = ("CANVAS_API_TOKEN",)
    ENV_COURSE_KEYS: ClassVar[tuple[str, ...]] = ("CANVAS_COURSE_ID",)

    @classmethod
    def from_file(cls, path: Path | None) -> Settings:
        if path is None:
            return cls.from_env()

        suffix = path.suffix.lower()
        if suffix in {".toml", ".tml"}:
            data = tomllib.loads(path.read_text())
            return cls.model_validate(data)

        if suffix in {".env", ""}:
            env_data = dotenv_values(path)
            if not env_data:
                raise RuntimeError(f"No configuration values found in {path}")
            return cls._from_mapping(env_data)

        raise RuntimeError(f"Unsupported configuration format for {path}")

    @classmethod
    def from_env(cls) -> Settings:
        # Load local .env without overriding explicit environment values unless disabled
        if os.getenv("CCC_SKIP_DOTENV") not in {"1", "true", "TRUE", "True"}:
            load_dotenv(override=False)
        return cls._from_mapping(os.environ)

    @classmethod
    def _from_mapping(cls, mapping: Mapping[str, Any]) -> Settings:
        canvas_section = {
            "api_url": cls._coalesce(
                mapping,
                cls.ENV_URL_KEYS,
                "https://canvas.instructure.com",
            ),
            "token": cls._coalesce(mapping, cls.ENV_TOKEN_KEYS, "changeme"),
            "course_id": cls._coalesce_int(mapping, cls.ENV_COURSE_KEYS, 0),
        }

        raw: Mapping[str, Any] = {"canvas": canvas_section}
        try:
            return cls.model_validate(raw)
        except ValidationError as exc:  # pragma: no cover - defensive
            raise RuntimeError("Invalid environment configuration") from exc

    @staticmethod
    def _coalesce(mapping: Mapping[str, Any], keys: Iterable[str], default: str | None) -> str:
        for key in keys:
            value = mapping.get(key)
            if value:
                return str(value)
        if default is not None:
            return default
        raise RuntimeError(f"Missing configuration value for keys: {', '.join(keys)}")

    @staticmethod
    def _coalesce_int(mapping: Mapping[str, Any], keys: Iterable[str], default: int) -> int:
        for key in keys:
            value = mapping.get(key)
            if value is not None and value != "":
                return int(value)
        return default
