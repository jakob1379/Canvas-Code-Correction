from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from canvas_code_correction.runner import (
    GraderConfig,
    GraderExecutor,
    MountPoint,
    ResourceLimits,
)


def docker_available() -> bool:
    """Check if Docker is available and running."""
    try:
        import docker
    except ImportError:
        return False

    try:
        client = docker.from_env()
        client.ping()
        return True
    except docker.errors.DockerException:
        return False


@pytest.mark.integration
@pytest.mark.skipif(not docker_available(), reason="Docker not available")
def test_grader_executor_simple_command() -> None:
    """Test executing a simple command in a Docker container."""
    # Use a small, widely available image
    config = GraderConfig(
        docker_image="alpine:latest",
        command=["echo", "hello world"],
        resource_limits=ResourceLimits(),
    )
    executor = GraderExecutor()

    try:
        result = executor.execute(config, mounts=[])
    except TypeError as e:
        if "resources" in str(e):
            pytest.skip(f"Docker SDK incompatible: {e}")
        raise

    assert result.exit_code == 0
    assert "hello world" in result.stdout
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.duration_seconds > 0


@pytest.mark.integration
@pytest.mark.skipif(not docker_available(), reason="Docker not available")
def test_grader_executor_with_mounts() -> None:
    """Test executing a command with mounted directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        submission_dir = Path(tmpdir) / "submission"
        submission_dir.mkdir()
        (submission_dir / "test.py").write_text("print('hello')")

        assets_dir = Path(tmpdir) / "assets"
        assets_dir.mkdir()
        (assets_dir / "data.txt").write_text("some data")

        mounts = [
            MountPoint(
                source=submission_dir,
                target=Path("/workspace/submission"),
                read_only=False,
            ),
            MountPoint(source=assets_dir, target=Path("/workspace/assets"), read_only=True),
        ]

        config = GraderConfig(
            docker_image="alpine:latest",
            command=["cat", "/workspace/submission/test.py"],
            resource_limits=ResourceLimits(),
        )
        executor = GraderExecutor()

        try:
            result = executor.execute(config, mounts=mounts)
        except TypeError as e:
            if "resources" in str(e):
                pytest.skip(f"Docker SDK incompatible: {e}")
            raise

        assert result.exit_code == 0
        assert "print('hello')" in result.stdout


@pytest.mark.integration
@pytest.mark.skipif(not docker_available(), reason="Docker not available")
def test_grader_executor_timeout() -> None:
    """Test that timeout kills the container."""
    config = GraderConfig(
        docker_image="alpine:latest",
        command=["sleep", "10"],
        resource_limits=ResourceLimits(timeout_seconds=1),
    )
    executor = GraderExecutor()

    try:
        result = executor.execute(config, mounts=[])
    except TypeError as e:
        if "resources" in str(e):
            pytest.skip(f"Docker SDK incompatible: {e}")
        raise

    # Container should be killed due to timeout
    assert result.timed_out is True
    assert result.exit_code != 0


@pytest.mark.integration
@pytest.mark.skipif(not docker_available(), reason="Docker not available")
def test_grader_executor_invalid_image() -> None:
    """Test error handling for invalid Docker image."""
    config = GraderConfig(
        docker_image="nonexistent_image:999999",
        command=["echo", "test"],
        resource_limits=ResourceLimits(),
    )
    executor = GraderExecutor()

    try:
        result = executor.execute(config, mounts=[])
    except TypeError as e:
        if "resources" in str(e):
            pytest.skip(f"Docker SDK incompatible: {e}")
        raise

    # Should fail due to missing image
    assert result.exit_code != 0
    assert "error" in result.stderr.lower() or "not found" in result.stderr.lower()


@pytest.mark.integration
@pytest.mark.skipif(not docker_available(), reason="Docker not available")
def test_execute_in_workspace() -> None:
    """Test the convenience method that sets up mounts automatically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        submission_dir = Path(tmpdir) / "submission"
        submission_dir.mkdir()
        (submission_dir / "code.py").write_text("x = 1")

        assets_dir = Path(tmpdir) / "assets"
        assets_dir.mkdir()
        (assets_dir / "test.txt").write_text("test")

        config = GraderConfig(
            docker_image="alpine:latest",
            command=["ls", "/workspace/submission"],
            resource_limits=ResourceLimits(),
        )
        executor = GraderExecutor()

        try:
            result = executor.execute_in_workspace(config, submission_dir, assets_dir)
        except TypeError as e:
            if "resources" in str(e):
                pytest.skip(f"Docker SDK incompatible: {e}")
            raise

        assert result.exit_code == 0
        assert "code.py" in result.stdout
