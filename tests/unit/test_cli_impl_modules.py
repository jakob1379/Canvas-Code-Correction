"""Direct unit tests for CLI implementation modules."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
import typer
from rich.console import Console

from canvas_code_correction.cli_course import course_list_command
from canvas_code_correction.cli_system import deploy_create_command
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
    assert "Error: missing block data" in rendered


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
