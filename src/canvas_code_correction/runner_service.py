"""Legacy RunnerService adapter forwarding to GraderExecutor."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .grader_executor import ExecutionResult, GraderExecutor


class RunnerService:
    """Compatibility shim delegating to :class:`GraderExecutor`."""

    def __init__(self, settings: Settings, logger: logging.Logger | None = None) -> None:
        self._executor = GraderExecutor(settings, logger=logger)

    def run(self, workspace: Path, command: list[str] | None = None) -> RunnerResult:
        execution = self._executor.run(workspace, command=command)
        return RunnerResult.from_execution_result(execution)


@dataclass(slots=True)
class RunnerResult:
    """Compatibility wrapper preserving legacy RunnerService API."""

    status: str
    exit_code: int
    stdout: str
    stderr: str
    results_file: Path | None
    points_file: Path | None
    comments_file: Path | None
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "results_file": self._opt_path(self.results_file),
            "points_file": self._opt_path(self.points_file),
            "comments_file": self._opt_path(self.comments_file),
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    @classmethod
    def from_execution_result(cls, result: ExecutionResult) -> RunnerResult:
        return cls(
            status=result.status,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            results_file=result.results_file,
            points_file=result.points_file,
            comments_file=result.comments_file,
            metadata=result.metadata,
        )

    @staticmethod
    def _opt_path(path: Path | None) -> str | None:
        return path.as_posix() if path is not None else None
