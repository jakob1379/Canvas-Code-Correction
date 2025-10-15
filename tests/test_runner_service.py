"""Tests for the Docker runner service."""

from pathlib import Path
from typing import Any

from canvas_code_correction.config import Settings
from canvas_code_correction.runner_service import RunnerResult, RunnerService


class _DummyContainer:
    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        self.id = "abc123"
        self._removed = False

    def wait(self) -> dict[str, Any]:
        (self._workspace / "results.json").write_text('{"status": "ok"}', encoding="utf-8")
        (self._workspace / "points.txt").write_text("7\n", encoding="utf-8")
        (self._workspace / "comments.txt").write_text("Nice work\n", encoding="utf-8")
        return {"StatusCode": 0}

    def logs(self, stdout: bool = True, stderr: bool = False) -> bytes:
        if stdout and not stderr:
            return b"stdout"
        if stderr and not stdout:
            return b"stderr"
        return b""

    def remove(self, force: bool = False) -> None:
        self._removed = True


class _DummyClient:
    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        self.containers = self
        self.closed = False
        self.last_kwargs: dict[str, Any] = {}

    def run(self, **kwargs: Any) -> _DummyContainer:  # type: ignore[override]
        self.last_kwargs = kwargs
        return _DummyContainer(self._workspace)

    def close(self) -> None:
        self.closed = True


def _base_settings(tmp_path: Path) -> Settings:
    return Settings.model_validate(
        {
            "canvas": {
                "api_url": "https://canvas.example",
                "token": "token",
                "course_id": 1,
            },
            "working_dir": tmp_path,
        }
    )


def test_runner_service_executes_container(tmp_path: Path, monkeypatch) -> None:
    settings = _base_settings(tmp_path)
    dummy_client = _DummyClient(tmp_path)
    monkeypatch.setattr(
        "canvas_code_correction.runner_service.docker.from_env", lambda: dummy_client
    )

    service = RunnerService(settings)
    result = service.run(tmp_path)

    assert isinstance(result, RunnerResult)
    assert result.status == "success"
    assert result.exit_code == 0
    assert result.stdout == "stdout"
    assert result.stderr == "stderr"
    assert result.results_file and result.results_file.exists()
    assert result.points_file and result.points_file.exists()
    assert result.comments_file and result.comments_file.exists()
    assert result.metadata["image"] == settings.runner.docker_image
    assert result.metadata["gpu_enabled"] is False
    assert dummy_client.last_kwargs["environment"]["CCC_RESULTS_FILE"].endswith("results.json")
    assert "device_requests" not in dummy_client.last_kwargs


def test_runner_service_handles_failed_exit(tmp_path: Path, monkeypatch):
    settings = _base_settings(tmp_path)

    class _FailContainer(_DummyContainer):
        def wait(self) -> dict[str, Any]:
            return {"StatusCode": 2}

    class _FailClient(_DummyClient):
        def run(self, **kwargs: Any) -> _FailContainer:  # type: ignore[override]
            return _FailContainer(self._workspace)

    monkeypatch.setattr(
        "canvas_code_correction.runner_service.docker.from_env", lambda: _FailClient(tmp_path)
    )

    service = RunnerService(settings)
    result = service.run(tmp_path)

    assert result.status == "failed"
    assert result.exit_code == 2


def test_runner_service_gpu_request(tmp_path: Path, monkeypatch) -> None:
    settings = _base_settings(tmp_path)
    settings.runner.gpu_enabled = True
    dummy_client = _DummyClient(tmp_path)
    monkeypatch.setattr(
        "canvas_code_correction.runner_service.docker.from_env", lambda: dummy_client
    )

    service = RunnerService(settings)
    result = service.run(tmp_path)

    requests = dummy_client.last_kwargs.get("device_requests")
    assert requests is not None
    assert requests[0].count == -1
    assert requests[0].capabilities == [["gpu"]]
    assert result.metadata["gpu_enabled"] is True
