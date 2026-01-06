"""Docker-based grader executor with resource limits and security hardening."""

from __future__ import annotations

import contextlib
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import docker
from docker.models.containers import Container
from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """Result of a grader execution."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_seconds: float
    container_id: str | None = None


class ResourceLimits(BaseModel):
    """Resource constraints for grader containers."""

    cpu_shares: int | None = None
    memory_mb: int | None = None
    memory_swap_mb: int | None = None
    network_disabled: bool = True
    read_only_rootfs: bool = True
    timeout_seconds: int = 300


class GraderConfig(BaseModel):
    """Configuration for a grading run."""

    docker_image: str
    command: list[str] = Field(default_factory=lambda: ["sh", "main.sh"])
    working_directory: Path = Path("/workspace/submission")
    environment: dict[str, str] = Field(default_factory=dict)
    user: str | None = None  # UID:GID format or username
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)


@dataclass(frozen=True)
class MountPoint:
    """Describes a filesystem mount for the container."""

    source: Path
    target: Path
    read_only: bool = True


class GraderExecutor:
    """Executes grader commands inside Docker containers with security constraints."""

    def __init__(self, docker_client: docker.DockerClient | None = None):
        self.client = docker_client or docker.from_env()

    def execute(
        self,
        config: GraderConfig,
        mounts: list[MountPoint],
    ) -> ExecutionResult:
        """Run the grader command inside a container with the specified mounts."""
        start_time = time.monotonic()

        # Prepare mount configuration for Docker
        docker_mounts = []
        for mount in mounts:
            docker_mounts.append(
                docker.types.Mount(
                    target=str(mount.target),
                    source=str(mount.source),
                    type="bind",
                    read_only=mount.read_only,
                )
            )

        # Prepare resource constraints
        resources: dict[str, Any] = {}
        if config.resource_limits.cpu_shares is not None:
            resources["cpu_shares"] = config.resource_limits.cpu_shares
        if config.resource_limits.memory_mb is not None:
            resources["memory"] = config.resource_limits.memory_mb * 1024 * 1024
        if config.resource_limits.memory_swap_mb is not None:
            resources["memswap"] = config.resource_limits.memory_swap_mb * 1024 * 1024

        container: Container | None = None
        try:
            # Pull image if not available locally
            try:
                self.client.images.get(config.docker_image)
            except docker.errors.ImageNotFound:
                print(f"Pulling image {config.docker_image}...")
                self.client.images.pull(config.docker_image)

            # Create and run container
            container = self.client.containers.run(
                image=config.docker_image,
                command=config.command,
                working_dir=str(config.working_directory),
                environment=config.environment,
                user=config.user,
                mounts=docker_mounts,
                network_disabled=config.resource_limits.network_disabled,
                read_only=config.resource_limits.read_only_rootfs,
                resources=resources,
                detach=True,
                stdout=True,
                stderr=True,
            )

            # Wait for container with timeout
            try:
                result = container.wait(timeout=config.resource_limits.timeout_seconds)
                exit_code = result["StatusCode"]
                timed_out = False
            except subprocess.TimeoutExpired:
                container.stop(timeout=10)
                exit_code = 124  # Standard timeout exit code
                timed_out = True

            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            duration = time.monotonic() - start_time

            return ExecutionResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                timed_out=timed_out,
                duration_seconds=duration,
                container_id=container.id,
            )

        except docker.errors.DockerException as e:
            duration = time.monotonic() - start_time
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Docker error: {e}",
                timed_out=False,
                duration_seconds=duration,
                container_id=container.id if container else None,
            )
        finally:
            # Clean up container
            if container:
                with contextlib.suppress(docker.errors.DockerException):
                    container.remove(force=True)

    def execute_in_workspace(
        self,
        config: GraderConfig,
        submission_dir: Path,
        assets_dir: Path,
    ) -> ExecutionResult:
        """Convenience method to execute grader in a prepared workspace."""
        mounts = [
            MountPoint(
                source=submission_dir, 
                target=Path("/workspace/submission"), 
                read_only=False
            ),
            MountPoint(
                source=assets_dir, 
                target=Path("/workspace/assets"), 
                read_only=True
            ),
        ]
        return self.execute(config, mounts)


def create_default_grader_config(
    docker_image: str,
    command: list[str] | None = None,
    timeout_seconds: int = 300,
    memory_mb: int | None = 512,
) -> GraderConfig:
    """Create a standard grader configuration with safe defaults."""
    if command is None:
        command = ["sh", "main.sh"]

    return GraderConfig(
        docker_image=docker_image,
        command=command,
        resource_limits=ResourceLimits(
            timeout_seconds=timeout_seconds,
            memory_mb=memory_mb,
            network_disabled=True,
            read_only_rootfs=True,
        ),
    )
