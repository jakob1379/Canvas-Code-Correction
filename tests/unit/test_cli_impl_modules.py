"""Direct unit tests for CLI implementation modules."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
import typer
from rich.console import Console

from canvas_code_correction import cli_system
from canvas_code_correction.cli_course import course_list_command
from canvas_code_correction.cli_system import deploy_create_command, worker_start_command
from canvas_code_correction.webhooks.deployments import DeploymentEnsureResult


def test_course_list_command_prints_empty_state_direct() -> None:
    console = Mock()

    course_list_command(
        console=console,
        find_course_block_names=list,
        load_course_block=Mock(),
    )

    console.print.assert_called_once_with("[yellow]No course configuration blocks found[/yellow]")


def test_course_list_command_renders_load_errors_direct() -> None:
    console = Console(record=True)

    course_list_command(
        console=console,
        find_course_block_names=lambda: ["broken-course"],
        load_course_block=Mock(side_effect=RuntimeError("missing block data")),
    )

    rendered = console.export_text()
    assert "broken-course" in rendered
    assert "Error:" in rendered
    assert "missing" in rendered
    assert "block" in rendered
    assert "data" in rendered


def test_deploy_create_command_handles_failed_result_direct(mock_settings) -> None:
    console = Mock()
    ensure_deployment = Mock(
        return_value=DeploymentEnsureResult(
            deployment_name="ccc-test-course-deployment",
            work_pool_name="test-pool",
            ensured=False,
            error="Prefect unavailable",
            error_type="RuntimeError",
        ),
    )
    asyncio_module = Mock(run=lambda coro: coro)

    with pytest.raises(typer.Exit) as exc_info:
        deploy_create_command(
            console=console,
            course_block="test-course",
            load_settings_from_course_block=lambda _: mock_settings,
            ensure_deployment=ensure_deployment,
            asyncio_module=asyncio_module,
        )

    assert exc_info.value.exit_code == 1
    ensure_deployment.assert_called_once_with(mock_settings, "test-course")
    console.print.assert_any_call(
        "[red]Error creating deployment: RuntimeError: Prefect unavailable[/red]",
    )


def test_worker_start_command_mirrors_shared_environment_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Mock()
    settings = Mock()
    settings.assets.storage_auth_mode = "shared_environment"
    settings.grader.work_pool_name = "course-work-pool-test"

    environ = {"RUSTFS_ACCESS_KEY": "shared-key", "RUSTFS_SECRET_KEY": "shared-secret"}
    execve = Mock()
    monkeypatch.setattr(cli_system.os, "environ", environ)
    monkeypatch.setattr(cli_system.os, "execve", execve)
    monkeypatch.setattr(cli_system.shutil, "which", lambda _: "/usr/bin/prefect")

    worker_start_command(
        console=console,
        course_block="ccc-course-test",
        load_settings_from_course_block=lambda _: settings,
    )

    assert environ["AWS_ACCESS_KEY_ID"] == "shared-key"
    assert environ["AWS_SECRET_ACCESS_KEY"] == "shared-secret"
    execve.assert_called_once_with(
        "/usr/bin/prefect",
        ["/usr/bin/prefect", "worker", "start", "--pool", "course-work-pool-test"],
        environ,
    )


def test_worker_start_command_leaves_embedded_credential_courses_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Mock()
    settings = Mock()
    settings.assets.storage_auth_mode = "embedded_block_credentials"
    settings.grader.work_pool_name = "course-work-pool-test"

    environ = {"RUSTFS_ACCESS_KEY": "shared-key", "RUSTFS_SECRET_KEY": "shared-secret"}
    execve = Mock()
    monkeypatch.setattr(cli_system.os, "environ", environ)
    monkeypatch.setattr(cli_system.os, "execve", execve)
    monkeypatch.setattr(cli_system.shutil, "which", lambda _: "/usr/bin/prefect")

    worker_start_command(
        console=console,
        course_block="ccc-course-test",
        load_settings_from_course_block=lambda _: settings,
    )

    assert "AWS_ACCESS_KEY_ID" not in environ
    execve.assert_called_once()


def test_worker_start_command_requires_a_work_pool() -> None:
    console = Mock()
    settings = Mock()
    settings.grader.work_pool_name = None

    with pytest.raises(typer.Exit) as exc_info:
        worker_start_command(
            console=console,
            course_block="ccc-course-test",
            load_settings_from_course_block=lambda _: settings,
        )

    assert exc_info.value.exit_code == 1


def test_worker_start_command_reports_missing_prefect_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Mock()
    settings = Mock()
    settings.assets.storage_auth_mode = "embedded_block_credentials"
    settings.grader.work_pool_name = "course-work-pool-test"
    monkeypatch.setattr(cli_system.shutil, "which", lambda _: None)

    with pytest.raises(typer.Exit) as exc_info:
        worker_start_command(
            console=console,
            course_block="ccc-course-test",
            load_settings_from_course_block=lambda _: settings,
        )

    assert exc_info.value.exit_code == 1
