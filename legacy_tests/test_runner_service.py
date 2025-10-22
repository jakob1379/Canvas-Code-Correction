"""Tests for the Docker runner service."""

from pathlib import Path

from canvas_code_correction.config import Settings
from canvas_code_correction.runner_service import RunnerResult, RunnerService


def _base_settings(tmp_path: Path) -> Settings:
    return Settings.model_validate(
        {
            "canvas": {
                "api_url": "https://canvas.example",
                "token": "token",
                "course_id": 1,
            },
            "working_dir": tmp_path,
            "runner": {
                "commands": {
                    "1": {
                        "command": ["python", "-c", "exit(0)"],
                        "env": {"ASSIGN": "one"},
                    }
                }
            },
        }
    )


def test_runner_service_forwards_to_executor(tmp_path: Path) -> None:
    settings = _base_settings(tmp_path)
    service = RunnerService(settings)
    result = service.run(tmp_path, command=["python", "-c", "exit(0)"])

    assert isinstance(result, RunnerResult)
    assert result.exit_code == 0
    assert result.status == "success"
