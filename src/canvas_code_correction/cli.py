from __future__ import annotations

import importlib.metadata
import os
from importlib import import_module
from typing import TYPE_CHECKING

import canvas_code_correction.cli_course as cli_course_impl
import canvas_code_correction.cli_system as cli_system_impl
import typer
import uvicorn
from canvasapi import Canvas
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from canvas_code_correction.bootstrap import (
    find_course_block_names,
    load_course_block,
    load_settings_from_course_block,
)
from canvas_code_correction.clients.canvas_resources import build_canvas_resources
from canvas_code_correction.flows.correction import (
    CorrectSubmissionPayload,
    correct_submission_flow,
)
from canvas_code_correction.prefect_blocks import CourseConfigBlock

if TYPE_CHECKING:
    from canvas_code_correction.config import Settings
    from canvas_code_correction.webhooks.deployments import DeploymentEnsureResult

app = typer.Typer(
    help="Canvas Code Correction CLI", rich_markup_mode="rich", invoke_without_command=True
)
console = Console()


async def ensure_deployment(
    settings: Settings,
    course_block: str,
) -> DeploymentEnsureResult:
    deployments = import_module("canvas_code_correction.webhooks.deployments")
    _ensure_deployment = deployments.ensure_deployment

    return await _ensure_deployment(settings, course_block)


def _load_webhook_fastapi_app():
    webhook_server = import_module("canvas_code_correction.webhooks.server")
    return webhook_server.app


course_app = typer.Typer(
    help="""[bold blue]📚 Course Administration[/bold blue]

Commands for course administrators to set up courses and grade submissions.

[dim]Typical workflow:[/dim]
  1. [dim]ccc course setup[/dim]     - Interactive course configuration
  2. [dim]ccc course run[/dim]       - Grade submissions
  3. [dim]ccc course list[/dim]      - View saved courses""",
    rich_markup_mode="rich",
)

system_app = typer.Typer(
    help="""[bold green]🔧 Platform Administration[/bold green]

Commands for platform administrators to manage infrastructure, webhooks, and deployments.

[dim]Typical operations:[/dim]
  • [dim]ccc system webhook serve[/dim]  - Start webhook server
  • [dim]ccc system deploy create[/dim]  - Create Prefect deployment
  • [dim]ccc system status[/dim]         - Check platform health""",
    rich_markup_mode="rich",
)

webhook_app = typer.Typer(
    help="Manage webhook server for Canvas submissions", rich_markup_mode="rich"
)
deploy_app = typer.Typer(help="Manage Prefect deployments", rich_markup_mode="rich")


@course_app.command(
    "run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def course_run(ctx: typer.Context, assignment_id: int) -> None:
    """Run correction flow for an assignment."""
    cli_course_impl.course_run_command(
        ctx,
        assignment_id,
        console=console,
        load_settings_from_course_block=load_settings_from_course_block,
        build_canvas_resources=build_canvas_resources,
        correct_submission_flow=correct_submission_flow,
        CorrectSubmissionPayload=CorrectSubmissionPayload,
    )


@course_app.command(
    "setup", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def course_setup(ctx: typer.Context) -> None:
    """Interactively set up a course configuration."""
    cli_course_impl.course_setup_command(
        ctx,
        console=console,
        Canvas=Canvas,
        CourseConfigBlock=CourseConfigBlock,
        Prompt=Prompt,
        IntPrompt=IntPrompt,
        Confirm=Confirm,
    )


@course_app.command("list")
def course_list() -> None:
    """List all saved course blocks."""
    cli_course_impl.course_list_command(
        console=console,
        find_course_block_names=find_course_block_names,
        load_course_block=load_course_block,
    )


@webhook_app.command("serve")
def webhook_serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Start webhook server for Canvas submissions."""
    cli_system_impl.webhook_serve_command(
        console=console,
        host=host,
        port=port,
        uvicorn_run=uvicorn.run,
        webhook_fastapi_app=_load_webhook_fastapi_app(),
    )


@deploy_app.command("create")
def deploy_create(course_block: str) -> None:
    """Create or update a Prefect deployment."""
    cli_system_impl.deploy_create_command(
        console=console,
        course_block=course_block,
        load_settings_from_course_block=load_settings_from_course_block,
        ensure_deployment=ensure_deployment,
    )


@system_app.command("status")
def system_status() -> None:
    """Check platform status and configuration."""
    cli_system_impl.system_status_command(
        console=console,
        config=cli_system_impl.SystemStatusConfig(
            requests_module=cli_system_impl.requests,
            boto3_module=cli_system_impl.boto3,
            os_module=os,
            http_status=cli_system_impl.HTTPStatus,
        ),
    )


@system_app.command("list")
def system_list() -> None:
    """List saved course blocks.

    Deprecated compatibility alias for `ccc course list`.
    """
    console.print("[yellow]`ccc system list` is deprecated; use `ccc course list`.[/yellow]")
    cli_course_impl.course_list_command(
        console=console,
        find_course_block_names=find_course_block_names,
        load_course_block=load_course_block,
    )


system_app.add_typer(webhook_app, name="webhook")
system_app.add_typer(deploy_app, name="deploy")
app.add_typer(course_app, name="course")
app.add_typer(system_app, name="system")


@app.callback()
def main_callback(
    *,
    version: bool = typer.Option(False, "--version", "-v", help="Show version information"),
) -> None:
    if version:
        try:
            version_str = importlib.metadata.version("canvas-code-correction")
        except importlib.metadata.PackageNotFoundError:
            version_str = "v2.0.0a0"
        console.print(f"Canvas Code Correction {version_str}")
        raise typer.Exit


if __name__ == "__main__":
    app()
