"""Execution utilities for running grader containers via Docker."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException
from docker.types import DeviceRequest

from .config import Settings

DEFAULT_COMMAND = ["python", "-m", "canvas_code_correction.runner"]
CONTAINER_WORKDIR = "/workspace"
RESULTS_FILENAME = "results.json"
POINTS_FILENAME = "points.txt"
COMMENTS_FILENAME = "comments.txt"


@dataclass
class RunnerResult:
    """Represents the outcome of a grader container execution."""

    status: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    results_file: Path | None = None
    points_file: Path | None = None
    comments_file: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        def _opt_path(path: Path | None) -> str | None:
            return path.as_posix() if path is not None else None

        payload: dict[str, Any] = {
            "status": self.status,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "results_file": _opt_path(self.results_file),
            "points_file": _opt_path(self.points_file),
            "comments_file": _opt_path(self.comments_file),
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


class RunnerService:
    """Encapsulates Docker execution of the grader image."""

    def __init__(self, settings: Settings, logger: logging.Logger | None = None) -> None:
        self.settings = settings
        self._logger = logger or logging.getLogger("canvas_code_correction.runner")

    def run(self, workspace: Path, command: list[str] | None = None) -> RunnerResult:
        """Execute the grader container and return its outcome."""

        command = command or DEFAULT_COMMAND
        workspace = workspace.resolve()

        env = {
            "CCC_WORKSPACE_DIR": CONTAINER_WORKDIR,
            "CCC_RESULTS_FILE": f"{CONTAINER_WORKDIR}/{RESULTS_FILENAME}",
            "CCC_POINTS_FILE": f"{CONTAINER_WORKDIR}/{POINTS_FILENAME}",
            "CCC_COMMENTS_FILE": f"{CONTAINER_WORKDIR}/{COMMENTS_FILENAME}",
            **self.settings.runner.env,
        }

        volumes = {
            str(workspace): {
                "bind": CONTAINER_WORKDIR,
                "mode": "rw",
            }
        }

        client = docker.from_env()
        container = None
        try:
            device_requests = self._device_requests(self.settings.runner.gpu_enabled)
            run_kwargs: dict[str, Any] = {
                "image": self.settings.runner.docker_image,
                "command": command,
                "environment": env,
                "working_dir": CONTAINER_WORKDIR,
                "volumes": volumes,
                "detach": True,
                "network_disabled": self.settings.runner.network_disabled,
                "mem_limit": self.settings.runner.memory_limit,
                "nano_cpus": self._nano_cpus(self.settings.runner.cpu_limit),
            }
            if device_requests:
                run_kwargs["device_requests"] = device_requests
            container = client.containers.run(
                **run_kwargs,
            )
            wait_result = container.wait()
            exit_code = int(wait_result.get("StatusCode", 1))
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="ignore")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="ignore")

            status = "success" if exit_code == 0 else "failed"
            metadata: dict[str, Any] = {
                "container_id": container.id,
                "image": self.settings.runner.docker_image,
                "command": command,
                "gpu_enabled": self.settings.runner.gpu_enabled,
            }

            results_file = self._existing_path(workspace / RESULTS_FILENAME)
            points_file = self._existing_path(workspace / POINTS_FILENAME)
            comments_file = self._existing_path(workspace / COMMENTS_FILENAME)

            if results_file and results_file.exists():
                try:
                    metadata["results"] = json.loads(results_file.read_text())
                except json.JSONDecodeError:
                    metadata["results"] = None

            return RunnerResult(
                status=status,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                results_file=results_file,
                points_file=points_file,
                comments_file=comments_file,
                metadata=metadata,
            )
        except DockerException as exc:  # pragma: no cover - defensive
            self._logger.exception("Failed to execute grader container: %s", exc)
            raise RuntimeError("Grader container execution failed") from exc
        finally:
            if container is not None:
                try:
                    container.remove(force=False)
                except DockerException:
                    self._logger.debug("Container cleanup failed", exc_info=True)
            client.close()

    @staticmethod
    def _nano_cpus(cpu_limit: float | None) -> int | None:
        if cpu_limit is None or cpu_limit <= 0:
            return None
        return int(cpu_limit * 1_000_000_000)

    @staticmethod
    def _existing_path(path: Path) -> Path | None:
        return path if path.exists() else None

    @staticmethod
    def _device_requests(gpu_enabled: bool) -> list[DeviceRequest] | None:
        if not gpu_enabled:
            return None
        return [DeviceRequest(count=-1, capabilities=[["gpu"]])]
