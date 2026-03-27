"""Unit tests for the GraderExecutor."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from docker.errors import ImageNotFound

from canvas_code_correction.runner import (
    GraderConfig,
    GraderExecutor,
    MountPoint,
    ResourceLimits,
    create_default_grader_config,
)


@pytest.mark.local
def test_create_default_grader_config() -> None:
    """Test creation of default grader configuration."""
    config = create_default_grader_config(
        docker_image="test/image:latest",
        command=["sh", "custom.sh"],
        timeout_seconds=600,
        memory_mb=1024,
    )

    assert config.docker_image == "test/image:latest"
    assert config.command == ["sh", "custom.sh"]
    assert config.resource_limits.timeout_seconds == 600
    assert config.resource_limits.memory_mb == 1024
    assert config.resource_limits.network_disabled is True
    assert config.resource_limits.read_only_rootfs is True


@pytest.mark.local
def test_grader_config_defaults() -> None:
    """Test GraderConfig default values."""
    config = GraderConfig(docker_image="test/image:latest")
    assert config.command == ["sh", "/workspace/assets/main.sh"]
    assert config.working_directory == Path("/workspace/submission")
    assert config.environment == {}
    assert config.user is None


@pytest.mark.local
def test_resource_limits_defaults() -> None:
    """Test ResourceLimits default values."""
    limits = ResourceLimits()
    assert limits.timeout_seconds == 300
    assert limits.network_disabled is True
    assert limits.read_only_rootfs is True
    assert limits.cpu_shares is None
    assert limits.memory_mb is None


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_grader_executor_initialization(mock_docker) -> None:
    """Test GraderExecutor initialization."""
    mock_client = Mock()
    mock_docker.from_env.return_value = mock_client

    executor = GraderExecutor()
    assert executor.client is mock_client

    # Test with provided client
    custom_client = Mock()
    executor2 = GraderExecutor(custom_client)
    assert executor2.client is custom_client


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_execute_with_mocks(mock_docker) -> None:
    """Test execute method with mocked Docker client."""
    # Setup mocks
    mock_client = Mock()
    mock_container = Mock()
    mock_image = Mock()

    mock_docker.from_env.return_value = mock_client
    mock_client.images.get.return_value = mock_image
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]
    mock_container.id = "test-container-id"

    # Create executor and config
    executor = GraderExecutor()
    config = GraderConfig(
        docker_image="test/image:latest",
        command=["sh", "test.sh"],
        resource_limits=ResourceLimits(timeout_seconds=30),
    )

    mounts = [
        MountPoint(source=Path("/tmp/src"), target=Path("/workspace/src"), read_only=True),
        MountPoint(source=Path("/tmp/data"), target=Path("/workspace/data"), read_only=False),
    ]

    # Execute
    result = executor.execute(config, mounts)

    # Verify Docker calls
    mock_client.images.get.assert_called_once_with("test/image:latest")
    mock_client.containers.run.assert_called_once()
    call_kwargs = mock_client.containers.run.call_args.kwargs

    assert call_kwargs["image"] == "test/image:latest"
    assert call_kwargs["command"] == ["sh", "test.sh"]
    assert call_kwargs["working_dir"] == "/workspace/submission"
    assert call_kwargs["network_disabled"] is True
    assert call_kwargs["detach"] is True

    # Verify resource constraints
    assert call_kwargs["read_only"] is True
    # Verify memory limits not set when None
    assert "mem_limit" not in call_kwargs
    assert "memswap_limit" not in call_kwargs
    assert "cpu_shares" not in call_kwargs

    # Verify container cleanup
    mock_container.remove.assert_called_once_with(force=True)

    # Verify result
    assert result.exit_code == 0
    assert result.stdout == "stdout output"
    assert result.stderr == "stderr output"
    assert result.timed_out is False
    assert result.container_id == "test-container-id"


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_execute_timeout(mock_docker) -> None:
    """Test execute method with timeout."""
    import subprocess

    # Create a real exception class for DockerException
    class MockDockerException(Exception):
        pass

    # Setup mock hierarchy
    mock_errors = Mock()
    mock_errors.DockerException = MockDockerException
    mock_errors.ImageNotFound = MockDockerException
    mock_docker.errors = mock_errors

    mock_client = Mock()
    mock_container = Mock()

    mock_docker.from_env.return_value = mock_client
    mock_client.images.get.return_value = Mock()
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=30)
    mock_container.id = "timeout-container"
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]

    executor = GraderExecutor()
    config = GraderConfig(
        docker_image="test/image:latest",
        resource_limits=ResourceLimits(timeout_seconds=30),
    )

    result = executor.execute(config, [])

    # Verify container was stopped
    mock_container.stop.assert_called_once_with(timeout=2)

    # Verify timeout result
    assert result.timed_out is True
    assert result.exit_code == 124  # Standard timeout exit code
    assert result.stdout == "stdout output"
    assert result.stderr == "stderr output"


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_execute_docker_error(mock_docker) -> None:
    """Test execute method handling Docker errors."""

    # Create a real exception class for DockerException
    class MockDockerException(Exception):
        pass

    # Setup mock hierarchy
    mock_errors = Mock()
    mock_errors.DockerException = MockDockerException
    mock_errors.ImageNotFound = MockDockerException
    mock_docker.errors = mock_errors

    mock_client = Mock()
    mock_docker.from_env.return_value = mock_client

    # Simulate: image not found, then pull fails with DockerException
    mock_client.images.get.side_effect = mock_errors.ImageNotFound("Image not found")
    mock_client.images.pull.side_effect = MockDockerException("Pull failed")

    executor = GraderExecutor()
    config = GraderConfig(docker_image="test/image:latest")

    # Patch the imported exceptions in the runner module
    with patch("canvas_code_correction.flows.runner.ImageNotFound", MockDockerException):
        with patch("canvas_code_correction.flows.runner.DockerException", MockDockerException):
            result = executor.execute(config, [])

    assert result.exit_code == 1
    assert "Docker error" in result.stderr
    assert "Pull failed" in result.stderr
    assert result.timed_out is False


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
@patch("canvas_code_correction.flows.runner.Mount")
def test_execute_in_workspace(mock_mount, mock_docker) -> None:
    """Test execute_in_workspace convenience method."""

    # Create a real exception class for DockerException
    class MockDockerException(Exception):
        pass

    # Setup mock hierarchy
    mock_errors = Mock()
    mock_errors.DockerException = MockDockerException
    mock_errors.ImageNotFound = MockDockerException
    mock_docker.errors = mock_errors
    mock_docker.types.Mount = mock_mount

    mock_client = Mock()
    mock_container = Mock()

    mock_docker.from_env.return_value = mock_client
    mock_client.images.get.return_value = Mock()
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]
    mock_container.id = "test-container"

    executor = GraderExecutor()
    config = GraderConfig(docker_image="test/image:latest")
    submission_dir = Path("/tmp/submission")
    assets_dir = Path("/tmp/assets")

    # Create the directories so they exist for mounting
    submission_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Patch the imported exceptions in the runner module
    with patch("canvas_code_correction.flows.runner.ImageNotFound", MockDockerException):
        with patch("canvas_code_correction.flows.runner.DockerException", MockDockerException):
            result = executor.execute_in_workspace(config, submission_dir, assets_dir)

    # Verify execute was called (implicitly by execute_in_workspace)
    # Check that docker.types.Mount was called correctly
    mount_calls = mock_mount.call_args_list
    assert len(mount_calls) == 2

    # Check submission mount (read/write) - called with keyword arguments
    first_call = mount_calls[0]
    first_kwargs = first_call[1]
    assert first_kwargs["source"] == str(submission_dir)
    assert first_kwargs["target"] == "/workspace/submission"
    assert first_kwargs["type"] == "bind"
    assert first_kwargs["read_only"] is False

    # Check assets mount (read-only)
    second_call = mount_calls[1]
    second_kwargs = second_call[1]
    assert second_kwargs["source"] == str(assets_dir)
    assert second_kwargs["target"] == "/workspace/assets"
    assert second_kwargs["type"] == "bind"
    assert second_kwargs["read_only"] is True

    # Check that containers.run was called with correct mounts
    mock_client.containers.run.assert_called_once()
    call_kwargs = mock_client.containers.run.call_args.kwargs
    mounts = call_kwargs.get("mounts", [])
    assert len(mounts) == 2

    assert result.exit_code == 0

    # Clean up test directories
    import shutil

    if submission_dir.exists():
        shutil.rmtree(submission_dir)
    if assets_dir.exists():
        shutil.rmtree(assets_dir)


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_execute_with_resource_limits(mock_docker) -> None:
    """Test execute method with all resource limits set."""
    # Setup mocks
    mock_client = Mock()
    mock_container = Mock()
    mock_image = Mock()

    mock_docker.from_env.return_value = mock_client
    mock_client.images.get.return_value = mock_image
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]
    mock_container.id = "test-container-id"

    # Create executor and config with resource limits
    executor = GraderExecutor()
    config = GraderConfig(
        docker_image="test/image:latest",
        command=["sh", "test.sh"],
        resource_limits=ResourceLimits(
            cpu_shares=512,
            memory_mb=1024,
            memory_swap_mb=2048,
            timeout_seconds=30,
        ),
    )

    mounts = []
    result = executor.execute(config, mounts)

    # Verify Docker calls
    mock_client.images.get.assert_called_once_with("test/image:latest")
    mock_client.containers.run.assert_called_once()
    call_kwargs = mock_client.containers.run.call_args.kwargs

    # Verify resource limits were passed correctly
    assert call_kwargs["cpu_shares"] == 512
    assert call_kwargs["mem_limit"] == 1024 * 1024 * 1024  # MB to bytes
    assert call_kwargs["memswap_limit"] == 2048 * 1024 * 1024
    assert call_kwargs["read_only"] is True
    assert call_kwargs["network_disabled"] is True

    # Verify container cleanup
    mock_container.remove.assert_called_once_with(force=True)

    # Verify result
    assert result.exit_code == 0
    assert result.stdout == "stdout output"
    assert result.stderr == "stderr output"
    assert result.timed_out is False
    assert result.container_id == "test-container-id"


@pytest.mark.local
def test_create_default_grader_config_no_command() -> None:
    """Test create_default_grader_config with command=None."""
    config = create_default_grader_config(
        docker_image="test/image:latest",
        command=None,
        timeout_seconds=600,
        memory_mb=256,
    )
    assert config.docker_image == "test/image:latest"
    assert config.command == ["sh", "/workspace/assets/main.sh"]  # default
    assert config.resource_limits.timeout_seconds == 600
    assert config.resource_limits.memory_mb == 256
    assert config.resource_limits.network_disabled is True
    assert config.resource_limits.read_only_rootfs is True


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_execute_image_pull_success(mock_docker) -> None:
    """Test execute when image is pulled successfully."""
    # Setup mocks
    mock_client = Mock()
    mock_container = Mock()
    mock_image = Mock()

    mock_docker.from_env.return_value = mock_client
    # First (and only) call raises ImageNotFound
    mock_client.images.get.side_effect = ImageNotFound("Image not found")
    mock_client.images.pull.return_value = mock_image
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]
    mock_container.id = "test-container-id"

    executor = GraderExecutor()
    config = GraderConfig(docker_image="test/image:latest")
    result = executor.execute(config, [])

    # Verify image pull was attempted
    mock_client.images.get.assert_called_with("test/image:latest")
    mock_client.images.pull.assert_called_once_with("test/image:latest")
    # Should have called get once (check before pull)
    assert mock_client.images.get.call_count == 1

    # Verify container ran
    mock_client.containers.run.assert_called_once()
    assert result.exit_code == 0


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_execute_requests_timeout(mock_docker) -> None:
    """Test execute with requests.exceptions.Timeout."""
    import requests

    # Setup mocks
    mock_client = Mock()
    mock_container = Mock()
    mock_image = Mock()

    mock_docker.from_env.return_value = mock_client
    mock_client.images.get.return_value = mock_image
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.side_effect = requests.exceptions.Timeout
    mock_container.id = "timeout-container"
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]

    executor = GraderExecutor()
    config = GraderConfig(
        docker_image="test/image:latest",
        resource_limits=ResourceLimits(timeout_seconds=30),
    )
    result = executor.execute(config, [])

    # Verify container was stopped
    mock_container.stop.assert_called_once_with(timeout=2)

    # Verify timeout result
    assert result.timed_out is True
    assert result.exit_code == 124
    assert result.stdout == "stdout output"
    assert result.stderr == "stderr output"


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_execute_connection_error(mock_docker) -> None:
    """Test execute with requests.exceptions.ConnectionError."""
    import requests

    # Setup mocks
    mock_client = Mock()
    mock_container = Mock()
    mock_image = Mock()

    mock_docker.from_env.return_value = mock_client
    mock_client.images.get.return_value = mock_image
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.side_effect = requests.exceptions.ConnectionError
    mock_container.id = "connection-error-container"
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]

    executor = GraderExecutor()
    config = GraderConfig(
        docker_image="test/image:latest",
        resource_limits=ResourceLimits(timeout_seconds=30),
    )
    result = executor.execute(config, [])

    # Verify container was stopped
    mock_container.stop.assert_called_once_with(timeout=2)

    # Verify timeout result (ConnectionError treated as timeout)
    assert result.timed_out is True
    assert result.exit_code == 124
    assert result.stdout == "stdout output"
    assert result.stderr == "stderr output"


@patch("canvas_code_correction.flows.runner.docker")
@pytest.mark.local
def test_execute_with_zero_memory_limits(mock_docker) -> None:
    """Test execute with zero memory limits (edge case)."""
    # Setup mocks
    mock_client = Mock()
    mock_container = Mock()
    mock_image = Mock()

    mock_docker.from_env.return_value = mock_client
    mock_client.images.get.return_value = mock_image
    mock_client.containers.run.return_value = mock_container
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [
        b"stdout output",
        b"stderr output",
    ]
    mock_container.id = "test-container-id"

    # Create executor and config with zero memory limits
    executor = GraderExecutor()
    config = GraderConfig(
        docker_image="test/image:latest",
        command=["sh", "test.sh"],
        resource_limits=ResourceLimits(
            cpu_shares=0,  # zero is valid (default weight)
            memory_mb=0,  # zero memory limit
            memory_swap_mb=0,  # zero swap limit
            timeout_seconds=30,
        ),
    )

    mounts = []
    result = executor.execute(config, mounts)

    # Verify Docker calls
    mock_client.images.get.assert_called_once_with("test/image:latest")
    mock_client.containers.run.assert_called_once()
    call_kwargs = mock_client.containers.run.call_args.kwargs

    # Verify resource limits were passed correctly (zero converted to bytes)
    assert call_kwargs["cpu_shares"] == 0
    assert call_kwargs["mem_limit"] == 0  # 0 * 1024 * 1024 = 0
    assert call_kwargs["memswap_limit"] == 0
    assert call_kwargs["read_only"] is True
    assert call_kwargs["network_disabled"] is True

    # Verify container cleanup
    mock_container.remove.assert_called_once_with(force=True)

    # Verify result
    assert result.exit_code == 0
    assert result.stdout == "stdout output"
    assert result.stderr == "stderr output"
    assert result.timed_out is False
    assert result.container_id == "test-container-id"
