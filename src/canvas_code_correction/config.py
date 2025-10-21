"""Configuration models for Canvas Code Correction v2."""

import os
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, ClassVar

from dotenv import dotenv_values, load_dotenv
from pydantic import BaseModel, Field, ValidationError


class RunnerCommand(BaseModel):
    command: list[str]
    env: dict[str, str] = Field(default_factory=dict)
    workdir: str | None = None


class CanvasSettings(BaseModel):
    api_url: str = Field(..., alias="api_url")
    token: str
    course_id: int = Field(..., alias="course_id")


class RunnerSettings(BaseModel):
    docker_image: str = "ghcr.io/jakob1379/canvas-code-correction-grader:latest"
    network_disabled: bool = True
    memory_limit: str = "1g"
    cpu_limit: float = 1.0
    gpu_enabled: bool = False
    env: dict[str, str] = Field(default_factory=dict)
    config_block: str | None = None
    commands: dict[str, RunnerCommand] = Field(default_factory=dict, frozen=True)

    def command_for_assignment(self, assignment_id: int) -> RunnerCommand | None:
        return self.commands.get(str(assignment_id))


class Settings(BaseModel):
    canvas: CanvasSettings
    runner: RunnerSettings = Field(default_factory=RunnerSettings)
    working_dir: Path = Field(default_factory=lambda: Path.cwd() / "var" / "runs")

    ENV_URL_KEYS: ClassVar[tuple[str, ...]] = ("CANVAS_API_URL",)
    ENV_TOKEN_KEYS: ClassVar[tuple[str, ...]] = ("CANVAS_API_TOKEN",)
    ENV_COURSE_KEYS: ClassVar[tuple[str, ...]] = ("CANVAS_COURSE_ID",)
    ENV_WORKING_DIR_KEYS: ClassVar[tuple[str, ...]] = ("CCC_WORKING_DIR",)
    ENV_RUNNER_IMAGE_KEYS: ClassVar[tuple[str, ...]] = (
        "CCC_RUNNER_IMAGE",
        "CCC_GRADER_IMAGE",
    )
    ENV_RUNNER_BLOCK_KEYS: ClassVar[tuple[str, ...]] = (
        "CCC_RUNNER_BLOCK",
        "CCC_GRADER_BLOCK",
    )
    ENV_RUNNER_NETWORK_KEYS: ClassVar[tuple[str, ...]] = (
        "CCC_RUNNER_NETWORK_DISABLED",
        "CCC_GRADER_NETWORK_DISABLED",
    )
    ENV_RUNNER_MEMORY_KEYS: ClassVar[tuple[str, ...]] = (
        "CCC_RUNNER_MEMORY_LIMIT",
        "CCC_GRADER_MEMORY_LIMIT",
    )
    ENV_RUNNER_CPU_KEYS: ClassVar[tuple[str, ...]] = (
        "CCC_RUNNER_CPU_LIMIT",
        "CCC_GRADER_CPU_LIMIT",
    )
    ENV_RUNNER_GPU_KEYS: ClassVar[tuple[str, ...]] = (
        "CCC_RUNNER_GPU_ENABLED",
        "CCC_GRADER_GPU_ENABLED",
    )

    @classmethod
    def from_file(cls, path: Path | None) -> "Settings":
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
    def from_env(cls) -> "Settings":
        # Load local .env without overriding explicit environment values unless disabled
        if os.getenv("CCC_SKIP_DOTENV") not in {"1", "true", "TRUE", "True"}:
            load_dotenv(override=False)
        return cls._from_mapping(os.environ)

    @classmethod
    def _from_mapping(cls, mapping: Mapping[str, Any]) -> "Settings":
        runner_defaults = RunnerSettings()

        block_name = cls._lookup(mapping, cls.ENV_RUNNER_BLOCK_KEYS)
        runner_section: dict[str, Any] = {}
        if block_name:
            runner_section = dict(cls._load_runner_block(block_name))
            runner_section.setdefault("config_block", block_name)

        image_override = cls._lookup(mapping, cls.ENV_RUNNER_IMAGE_KEYS)
        if image_override is not None:
            runner_section["docker_image"] = image_override
        else:
            runner_section.setdefault("docker_image", runner_defaults.docker_image)

        network_override = cls._lookup(mapping, cls.ENV_RUNNER_NETWORK_KEYS)
        if network_override is not None:
            runner_section["network_disabled"] = cls._parse_bool(network_override)
        else:
            runner_section.setdefault("network_disabled", runner_defaults.network_disabled)

        memory_override = cls._lookup(mapping, cls.ENV_RUNNER_MEMORY_KEYS)
        if memory_override is not None:
            runner_section["memory_limit"] = memory_override
        else:
            runner_section.setdefault("memory_limit", runner_defaults.memory_limit)

        cpu_override = cls._lookup(mapping, cls.ENV_RUNNER_CPU_KEYS)
        if cpu_override is not None:
            runner_section["cpu_limit"] = cls._parse_float(cpu_override)
        else:
            runner_section.setdefault("cpu_limit", runner_defaults.cpu_limit)

        gpu_override = cls._lookup(mapping, cls.ENV_RUNNER_GPU_KEYS)
        if gpu_override is not None:
            runner_section["gpu_enabled"] = cls._parse_bool(gpu_override)
        else:
            runner_section.setdefault("gpu_enabled", runner_defaults.gpu_enabled)

        runner_section.setdefault("env", runner_defaults.env.copy())

        canvas_section = {
            "api_url": cls._coalesce(
                mapping,
                cls.ENV_URL_KEYS,
                "https://canvas.instructure.com",
            ),
            "token": cls._coalesce(mapping, cls.ENV_TOKEN_KEYS, "changeme"),
            "course_id": cls._coalesce_int(mapping, cls.ENV_COURSE_KEYS, 0),
        }

        raw: dict[str, Any] = {"canvas": canvas_section, "runner": runner_section}

        working_dir_override = cls._lookup(mapping, cls.ENV_WORKING_DIR_KEYS)
        if working_dir_override is not None:
            raw["working_dir"] = Path(working_dir_override).expanduser()

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

    @staticmethod
    def _lookup(mapping: Mapping[str, Any], keys: Iterable[str]) -> str | None:
        for key in keys:
            value = mapping.get(key)
            if value is not None and value != "":
                return str(value)
        return None

    @staticmethod
    def _parse_bool(value: str) -> bool:
        lowered = value.lower()
        if lowered in {"1", "true", "t", "yes", "y"}:
            return True
        if lowered in {"0", "false", "f", "no", "n"}:
            return False
        raise RuntimeError(f"Invalid boolean value: {value!r}")

    @staticmethod
    def _parse_float(value: str) -> float:
        try:
            return float(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Invalid float value: {value!r}") from exc

    @staticmethod
    def _load_runner_block(block_name: str) -> Mapping[str, Any]:
        try:
            from prefect.blocks.system import JSON
        except ImportError as exc:  # pragma: no cover - defensive
            raise RuntimeError("Prefect is required to load runner configuration blocks") from exc

        block = JSON.load(block_name)
        value = getattr(block, "value", None)
        if not isinstance(value, Mapping):
            raise RuntimeError(
                f"Prefect block '{block_name}' does not contain a mapping-compatible value"
            )
        return dict(value)
