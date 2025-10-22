"""Execute grader commands within the current worker environment."""

from __future__ import annotations

import logging
import os
import subprocess  # nosec B404 - intentional use for executing graded commands
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import Settings

RESULTS_FILENAME = "results.json"
POINTS_FILENAME = "points.txt"
COMMENTS_FILENAME = "comments.txt"


@dataclass
class ExecutionResult:
    """Represents the outcome of a grader command execution."""

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


class GraderExecutor:
    """Runs grader commands inside the Prefect worker container."""

    def __init__(self, settings: Settings, logger: logging.Logger | None = None) -> None:
        self.settings = settings
        self._logger = logger or logging.getLogger("canvas_code_correction.grader")

    def run(
        self,
        workspace: Path,
        command: list[str] | None = None,
        extra_env: dict[str, str] | None = None,
        workdir: str | None = None,
    ) -> ExecutionResult:
        """Execute the grader command and return its outcome."""

        command = command or ["python", "-m", "canvas_code_correction.runner"]
        workspace = workspace.resolve()
        workspace.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env.update(
            {
                "CCC_WORKSPACE_DIR": workspace.as_posix(),
                "CCC_RESULTS_FILE": (workspace / RESULTS_FILENAME).as_posix(),
                "CCC_POINTS_FILE": (workspace / POINTS_FILENAME).as_posix(),
                "CCC_COMMENTS_FILE": (workspace / COMMENTS_FILENAME).as_posix(),
                **self.settings.runner.env,
            }
        )
        if extra_env:
            env.update({str(key): str(value) for key, value in extra_env.items()})

        execution_dir = self._resolve_workdir(workspace, workdir)

        self._logger.debug(
            "Executing grader command",
            extra={
                "workspace": workspace.as_posix(),
                "command": command,
                "env_keys": sorted(env.keys()),
                "cwd": execution_dir.as_posix(),
            },
        )

        completed = subprocess.run(  # noqa: S603,S607 - grader commands are pre-vetted  # nosec B603
            command,
            cwd=execution_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        status = "success" if completed.returncode == 0 else "failed"

        results_file = self._existing_path(workspace / RESULTS_FILENAME)
        points_file = self._existing_path(workspace / POINTS_FILENAME)
        comments_file = self._existing_path(workspace / COMMENTS_FILENAME)

        metadata: dict[str, Any] = {
            "command": command,
            "cwd": execution_dir.as_posix(),
        }

        if results_file and results_file.exists():
            metadata.setdefault("results_file", results_file.as_posix())

        return ExecutionResult(
            status=status,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            results_file=results_file,
            points_file=points_file,
            comments_file=comments_file,
            metadata=metadata,
        )

    @staticmethod
    def _existing_path(path: Path) -> Path | None:
        return path if path.exists() else None

    @staticmethod
    def _resolve_workdir(workspace: Path, workdir: str | None) -> Path:
        if workdir is None:
            return workspace

        candidate = Path(workdir)
        if not candidate.is_absolute():
            candidate = workspace / candidate
        candidate = candidate.resolve()

        try:
            candidate.relative_to(workspace)
        except ValueError as exc:  # pragma: no cover - defensive
            raise RuntimeError("Configured workdir must reside within the workspace") from exc

        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
