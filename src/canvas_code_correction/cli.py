from __future__ import annotations

import importlib.metadata
import os
from importlib import import_module
from typing import TYPE_CHECKING, Annotated

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
worker_app = typer.Typer(help="Manage course-scoped workers", rich_markup_mode="rich")


@course_app.command("run")
def course_run(
    assignment_id: int,
    submission_id: Annotated[
        int | None, typer.Option("--submission-id", help="Limit the run to one submission")
    ] = None,
    course: Annotated[
        str, typer.Option("--course", "-c", help="Course block name to load")
    ] = "default-course",
    download_dir: Annotated[
        str | None, typer.Option("--download-dir", help="Directory for downloaded files")
    ] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Skip upload side effects")] = False,
) -> None:
    """Run correction flow for an assignment."""
    cli_course_impl.course_run_command(
        assignment_id,
        cli_course_impl.CourseRunOptions(
            submission_id=submission_id,
            course_block=course,
            download_dir=None if download_dir is None else cli_course_impl.Path(download_dir),
            dry_run=dry_run,
        ),
        console=console,
        load_settings_from_course_block=load_settings_from_course_block,
        build_canvas_resources=build_canvas_resources,
        correct_submission_flow=correct_submission_flow,
        CorrectSubmissionPayload=CorrectSubmissionPayload,
    )


@course_app.command("setup")
def course_setup(
    token_stdin: Annotated[
        bool, typer.Option("--token-stdin", help="Read the Canvas token from stdin")
    ] = False,
    token: Annotated[str | None, typer.Option("--token", help="Canvas API token")] = None,
    api_url: Annotated[str | None, typer.Option("--api-url", "-u", help="Canvas base URL")] = None,
    course_id: Annotated[int, typer.Option("--course-id", "-c", help="Canvas course ID")] = 0,
    docker_image: Annotated[
        str, typer.Option("--docker-image", "-d", help="Docker image used for grading")
    ] = "jakob1379/canvas-grader:latest",
    work_packages: Annotated[
        list[str] | None,
        typer.Option(
            "--map-assignments",
            "--work-package",
            help="Map an assignment ID to a work-package root using assignment_id:path",
        ),
    ] = None,
    env_var: Annotated[
        list[str] | None,
        typer.Option("--env", "-e", help="Extra grader environment variable in KEY=VALUE form"),
    ] = None,
    interactive: Annotated[
        bool, typer.Option("--interactive/--no-interactive", help="Enable or disable prompts")
    ] = True,
) -> None:
    """Interactively set up a course configuration."""
    cli_course_impl.course_setup_command(
        cli_course_impl.CourseSetupOptions(
            token_stdin=token_stdin,
            canvas_api_url=api_url,
            canvas_token=token,
            course_id=course_id,
            docker_image=docker_image,
            work_packages=work_packages or [],
            env_var=env_var or [],
            interactive=interactive,
        ),
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


@worker_app.command("start")
def system_worker_start(
    course: Annotated[
        str,
        typer.Option("--course", "-c", help="Course block name to load"),
    ],
) -> None:
    """Start a course-scoped Prefect worker with injected storage credentials."""
    cli_system_impl.worker_start_command(
        console=console,
        course_block=course,
        load_settings_from_course_block=load_settings_from_course_block,
    )


system_app.add_typer(webhook_app, name="webhook")
system_app.add_typer(deploy_app, name="deploy")
system_app.add_typer(worker_app, name="worker")
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
