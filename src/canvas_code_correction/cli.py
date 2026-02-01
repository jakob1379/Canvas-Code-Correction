"""Command-line interface for Canvas Code Correction.

This CLI is organized into two main command groups:
- **course**: Commands for course administrators (setup, configure, run corrections)
- **system**: Commands for platform administrators (webhook, deployments, monitoring)
"""

from __future__ import annotations

import asyncio
import importlib.metadata
import json
import tempfile
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from canvasapi import Canvas
from pydantic import HttpUrl, SecretStr
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from canvas_code_correction.clients import build_canvas_resources
from canvas_code_correction.config import resolve_settings_from_block
from canvas_code_correction.flows import (
    CorrectSubmissionPayload,
    correct_submission_flow,
)
from canvas_code_correction.prefect_blocks import CourseConfigBlock
from canvas_code_correction.webhooks.deployments import ensure_deployment
from canvas_code_correction.webhooks.server import app as webhook_fastapi_app

# Main CLI app
app = typer.Typer(
    help="Canvas Code Correction CLI",
    rich_markup_mode="rich",
    invoke_without_command=True,
)
console = Console()

# =============================================================================
# COURSE ADMINISTRATOR COMMANDS
# =============================================================================

course_app = typer.Typer(
    help="""[bold blue]📚 Course Administration[/bold blue]

Commands for course administrators to configure courses and grade submissions.

[dim]Typical workflow:[/dim]
  1. [dim]ccc course setup[/dim]     - Interactive course configuration
  2. [dim]ccc course run[/dim]       - Grade submissions
  3. [dim]ccc course list[/dim]      - View configured courses""",
    rich_markup_mode="rich",
)


@course_app.command("run")
def course_run(
    assignment_id: Annotated[int, typer.Argument(help="Canvas assignment ID")],
    submission_id: Annotated[
        int | None,
        typer.Option(help="Specific submission ID (default: all submissions)"),
    ] = None,
    course_block: Annotated[
        str,
        typer.Option("--course", "-c", help="Prefect course configuration block name"),
    ] = "default-course",
    download_dir: Annotated[
        Path | None,
        typer.Option(help="Directory for downloaded submissions (default: temporary directory)"),
    ] = None,
    dry_run: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--dry-run", help="Skip actual grading and upload"),
    ] = False,
) -> None:
    """Run correction flow for an assignment or specific submission.

    [blue]Examples:[/blue]
        # Grade all submissions for an assignment
        $ ccc course run 12345 --course ccc-course-cs101

        # Grade a single submission in dry-run mode
        $ ccc course run 12345 --submission-id 67890 --dry-run
    """
    try:
        settings = resolve_settings_from_block(course_block)
    except Exception as e:
        console.print(f"[red]Error loading course block '{course_block}': {e}[/red]")
        raise typer.Exit(1) from e

    if download_dir is None:
        download_dir = Path(tempfile.mkdtemp(prefix="ccc-download-"))
        console.print(f"[yellow]Using temporary download directory: {download_dir}[/yellow]")

    if submission_id:
        payload = CorrectSubmissionPayload(
            assignment_id=assignment_id,
            submission_id=submission_id,
        )
        console.print(
            f"[blue]Running correction for assignment {assignment_id}, "
            f"submission {submission_id}[/blue]",
        )
    else:
        # Batch mode: process all submissions
        console.print(
            f"[blue]Batch mode: processing all submissions for assignment {assignment_id}[/blue]",
        )
        resources = build_canvas_resources(settings)
        assignment = resources.course.get_assignment(assignment_id)
        submissions = assignment.get_submissions()
        for submission in submissions:
            sub_id = submission.id
            console.print(f"[blue]Processing submission {sub_id}[/blue]")
            payload = CorrectSubmissionPayload(
                assignment_id=assignment_id,
                submission_id=sub_id,
            )
            try:
                result = correct_submission_flow(
                    payload,
                    settings,
                    download_dir=download_dir,
                    dry_run=dry_run,
                )
                console.print(f"[green]Submission {sub_id} processed successfully[/green]")
                # Optional: collect summary
            except Exception as e:  # noqa: BLE001
                console.print(f"[red]Error processing submission {sub_id}: {e}[/red]")
                # Continue with next submission
                continue

        console.print("[green]Batch processing completed![/green]")
        raise typer.Exit(0)

    if dry_run:
        console.print("[yellow]Dry run enabled - no actual grading or upload will occur[/yellow]")

    try:
        result = correct_submission_flow(
            payload,
            settings,
            download_dir=download_dir,
            dry_run=dry_run,
        )
        console.print("[green]Correction flow completed successfully![/green]")
        console.print(
            json.dumps(
                {
                    "submission_metadata_keys": list(result.submission_metadata.keys()),
                    "downloaded_files_count": len(result.downloaded_files),
                    "workspace": str(result.workspace.root) if result.workspace else None,
                    "results_keys": list(result.results.keys()),
                },
                indent=2,
            ),
        )
    except Exception as e:
        console.print(f"[red]Error running correction flow: {e}[/red]")
        raise typer.Exit(1) from e


@course_app.command("configure")
def course_configure(  # noqa: PLR0913
    course_slug: Annotated[str, typer.Argument(help="Unique identifier for the course")],
    canvas_token: Annotated[
        str,
        typer.Option(
            "--token",
            "-t",
            help="Canvas API token",
            prompt=True,
            hide_input=True,
        ),
    ],
    canvas_course_id: Annotated[int, typer.Option("--course-id", "-i", help="Canvas course ID")],
    asset_bucket_block: Annotated[
        str,
        typer.Option(
            "--assets-block",
            "-a",
            help="Prefect S3 bucket block name for assets",
        ),
    ],
    canvas_api_url: Annotated[
        str,
        typer.Option("--api-url", help="Canvas instance URL"),
    ] = "https://canvas.instructure.com",
    asset_path_prefix: Annotated[
        str,
        typer.Option("--s3-prefix", "-p", help="S3 prefix for grader assets"),
    ] = "",
    docker_image: Annotated[
        str | None,
        typer.Option("--docker-image", "-d", help="Docker image for grading"),
    ] = None,
    work_pool_name: Annotated[
        str | None,
        typer.Option("--work-pool", "-w", help="Prefect work pool name"),
    ] = None,
    workspace_root: Annotated[
        Path | None,
        typer.Option("--workspace-root", help="Root directory for workspaces"),
    ] = None,
    env_var: Annotated[
        list[str] | None,
        typer.Option("--env", "-e", help="Environment variables (KEY=VALUE)"),
    ] = None,
) -> None:
    """Create or update a course configuration block.

    [blue]Examples:[/blue]
        # Basic configuration
        $ ccc course configure cs101 \\
            --token $CANVAS_TOKEN \\
            --course-id 12345 \\
            --assets-block course-assets

        # With all options
        $ ccc course configure cs101 \\
            --token $CANVAS_TOKEN \\
            --course-id 12345 \\
            --assets-block course-assets \\
            --docker-image mygrader:latest \\
            --s3-prefix graders/cs101/
    """
    block_name = f"ccc-course-{course_slug}"

    # Parse environment variables
    grader_env = {}
    if env_var:
        for env_str in env_var:
            if "=" in env_str:
                key, value = env_str.split("=", 1)
                grader_env[key.strip()] = value.strip()
            else:
                console.print(f"[yellow]Skipping invalid env var: {env_str}[/yellow]")

    try:
        block = CourseConfigBlock(
            canvas_api_url=HttpUrl(canvas_api_url),
            canvas_token=SecretStr(canvas_token),
            canvas_course_id=canvas_course_id,
            asset_bucket_block=asset_bucket_block,
            asset_path_prefix=asset_path_prefix,
            workspace_root=str(workspace_root) if workspace_root else None,
            grader_image=docker_image,
            work_pool_name=work_pool_name,
            grader_env=grader_env,
        )
        block.save(block_name, overwrite=True)
        console.print(f"[green]Course configuration saved as block: {block_name}[/green]")
    except Exception as e:
        console.print(f"[red]Error saving course block: {e}[/red]")
        raise typer.Exit(1) from e


@course_app.command("setup")
def course_setup(  # noqa: PLR0913, PLR0912, PLR0915
    canvas_token: Annotated[
        str | None,
        typer.Option(
            "--token",
            "-t",
            help="Canvas API token",
            hide_input=True,
        ),
    ] = None,
    canvas_api_url: Annotated[
        str,
        typer.Option("--api-url", help="Canvas instance URL"),
    ] = "https://canvas.instructure.com",
    course_id: Annotated[
        int | None,
        typer.Option("--course-id", "-c", help="Canvas course ID (skip interactive selection)"),
    ] = None,
    assets_block: Annotated[
        str | None,
        typer.Option("--assets-block", "-a", help="Prefect S3 bucket block name"),
    ] = None,
    assets_prefix: Annotated[
        str,
        typer.Option("--assets-prefix", "-p", help="S3 prefix for grader assets"),
    ] = "",
    course_slug: Annotated[
        str | None,
        typer.Option("--slug", "-s", help="Unique identifier for the course block"),
    ] = None,
    docker_image: Annotated[
        str | None,
        typer.Option("--docker-image", "-d", help="Docker image for grading"),
    ] = None,
    work_pool: Annotated[
        str | None,
        typer.Option("--work-pool", "-w", help="Prefect work pool name"),
    ] = None,
    test_mappings: Annotated[
        list[str] | None,
        typer.Option(
            "--test-map",
            help="Test mappings in format 'assignment_id:/path/to/test.py'",
        ),
    ] = None,
    env_var: Annotated[
        list[str] | None,
        typer.Option("--env", "-e", help="Environment variables (KEY=VALUE)"),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option("--interactive/--no-interactive", help="Enable interactive prompts"),
    ] = True,
) -> None:
    """Interactively set up a course configuration with guided prompts.

    This command guides you through setting up a course configuration step by step:
    1. Canvas API token (required first to authenticate)
    2. Canvas instance URL
    3. Course selection (fetched from Canvas)
    4. Assets configuration (S3 bucket)
    5. Assignment mapping (link local tests to Canvas assignments)
    6. Grader configuration (Docker image, work pool, etc.)

    [blue]Examples:[/blue]
        # Interactive mode (default)
        $ ccc course setup

        # Non-interactive with all options
        $ ccc course setup --no-interactive \\
            --token $CANVAS_TOKEN \\
            --course-id 12345 \\
            --assets-block my-bucket \\
            --slug my-course
    """
    console.print(Panel.fit("[bold blue]Canvas Code Correction - Course Setup[/bold blue]"))

    # Step 1: Get API Token (required first)
    if canvas_token is None:
        if interactive:
            canvas_token = Prompt.ask(
                "Enter your Canvas API token",
                password=True,
            )
        else:
            console.print("[red]Error: --token is required in non-interactive mode[/red]")
            raise typer.Exit(1)

    # Validate token by making a test API call
    try:
        canvas = Canvas(canvas_api_url, canvas_token)
        # Try to get current user to validate token
        _ = canvas.get_current_user()
        console.print("[green]✓ Canvas API token validated successfully[/green]")
    except Exception as e:
        console.print(f"[red]Error: Failed to validate Canvas API token: {e}[/red]")
        raise typer.Exit(1) from e

    # Step 2: Course Selection
    if course_id is None:
        if interactive:
            console.print("\n[bold]Fetching available courses from Canvas...[/bold]")
            try:
                courses = list(canvas.get_courses())
                if not courses:
                    console.print("[yellow]No courses found for this user[/yellow]")
                    raise typer.Exit(1)

                # Display courses in a table
                table = Table(title="Available Courses")
                table.add_column("ID", style="cyan", justify="right")
                table.add_column("Name", style="green")
                table.add_column("Course Code", style="blue")

                for course in courses:
                    table.add_row(
                        str(course.id),
                        course.name or "Unnamed",
                        course.course_code or "N/A",
                    )

                console.print(table)

                # Prompt for course selection
                course_id = IntPrompt.ask(
                    "\nEnter the Course ID to configure",
                )

                # Validate the selected course exists
                try:
                    _ = canvas.get_course(course_id)
                except Exception:
                    console.print(f"[red]Error: Course ID {course_id} not found[/red]")
                    raise typer.Exit(1)

            except Exception as e:
                console.print(f"[red]Error fetching courses: {e}[/red]")
                raise typer.Exit(1) from e
        else:
            console.print("[red]Error: --course-id is required in non-interactive mode[/red]")
            raise typer.Exit(1)
    else:
        # Validate provided course ID
        try:
            _ = canvas.get_course(course_id)
            console.print(f"[green]✓ Course ID {course_id} validated[/green]")
        except Exception as e:
            console.print(f"[red]Error: Course ID {course_id} not found: {e}[/red]")
            raise typer.Exit(1) from e

    # Get course details for slug suggestion
    try:
        course = canvas.get_course(course_id)
        suggested_slug = course.course_code or f"course-{course_id}"
        suggested_slug = suggested_slug.lower().replace(" ", "-").replace("_", "-")
    except Exception:
        suggested_slug = f"course-{course_id}"

    # Step 3: Course Slug
    if course_slug is None:
        if interactive:
            course_slug = Prompt.ask(
                "Enter a unique identifier (slug) for this course",
                default=suggested_slug,
            )
        else:
            course_slug = suggested_slug

    # Step 4: Assets Configuration
    if assets_block is None:
        if interactive:
            assets_block = Prompt.ask(
                "Enter the Prefect S3 bucket block name for assets",
                default="default-assets",
            )
        else:
            console.print("[red]Error: --assets-block is required in non-interactive mode[/red]")
            raise typer.Exit(1)

    if interactive and assets_prefix == "":
        default_prefix = f"graders/{course_slug}/"
        assets_prefix = Prompt.ask(
            "Enter the S3 prefix for grader assets",
            default=default_prefix,
        )

    # Step 5: Assignment Mapping
    test_map_env = {}
    if test_mappings is None and interactive:
        console.print("\n[bold]Fetching assignments from course...[/bold]")
        try:
            assignments = list(course.get_assignments())
            if assignments:
                table = Table(title=f"Assignments in {course.name}")
                table.add_column("ID", style="cyan", justify="right")
                table.add_column("Name", style="green")
                table.add_column("Published", style="blue")

                for assignment in assignments:
                    published = "✓" if getattr(assignment, "published", False) else "✗"
                    table.add_row(
                        str(assignment.id),
                        assignment.name or "Unnamed",
                        published,
                    )

                console.print(table)

                if Confirm.ask(
                    "\nWould you like to map local test files to assignments?",
                    default=True,
                ):
                    console.print(
                        "\n[yellow]Enter test mappings (press Enter with no input to finish):[/yellow]"
                    )
                    console.print("Format: [dim]assignment_id:/path/to/test.py[/dim]")

                    while True:
                        mapping = Prompt.ask(
                            "Test mapping",
                            default="",
                        )
                        if not mapping:
                            break

                        if ":" not in mapping:
                            console.print(
                                "[yellow]Invalid format. Use: assignment_id:/path/to/test.py[/yellow]"
                            )
                            continue

                        try:
                            assignment_id_str, test_path = mapping.split(":", 1)
                            assignment_id = int(assignment_id_str)
                            # Validate assignment exists
                            _ = course.get_assignment(assignment_id)
                            env_key = f"CCC_TEST_MAP_{assignment_id}"
                            test_map_env[env_key] = test_path
                            console.print(
                                f"[green]✓ Mapped assignment {assignment_id} → {test_path}[/green]"
                            )
                        except ValueError:
                            console.print(
                                "[yellow]Invalid assignment ID (must be a number)[/yellow]"
                            )
                        except Exception as e:
                            console.print(
                                f"[yellow]Warning: Could not validate assignment: {e}[/yellow]"
                            )
                            # Still add it, user might know better
                            env_key = f"CCC_TEST_MAP_{assignment_id_str}"
                            test_map_env[env_key] = test_path
            else:
                console.print("[yellow]No assignments found in this course[/yellow]")

        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch assignments: {e}[/yellow]")
    elif test_mappings:
        # Parse provided test mappings
        for mapping in test_mappings:
            if ":" not in mapping:
                console.print(f"[yellow]Skipping invalid test mapping: {mapping}[/yellow]")
                continue
            try:
                assignment_id_str, test_path = mapping.split(":", 1)
                assignment_id = int(assignment_id_str)
                env_key = f"CCC_TEST_MAP_{assignment_id}"
                test_map_env[env_key] = test_path
            except ValueError:
                console.print(f"[yellow]Skipping invalid assignment ID in: {mapping}[/yellow]")

    # Step 6: Grader Configuration
    if docker_image is None and interactive:
        docker_image = Prompt.ask(
            "Docker image for grading (optional)",
            default="",
        )
        if docker_image == "":
            docker_image = None

    if work_pool is None and interactive:
        work_pool = Prompt.ask(
            "Prefect work pool name (optional)",
            default="",
        )
        if work_pool == "":
            work_pool = None

    # Parse environment variables
    grader_env = {}
    if env_var:
        for env_str in env_var:
            if "=" in env_str:
                key, value = env_str.split("=", 1)
                grader_env[key.strip()] = value.strip()
            else:
                console.print(f"[yellow]Skipping invalid env var: {env_str}[/yellow]")

    # Merge test mappings into grader_env
    grader_env.update(test_map_env)

    # Step 7: Save Configuration
    block_name = f"ccc-course-{course_slug}"

    console.print("\n[bold]Configuration Summary:[/bold]")
    summary_table = Table(show_header=False)
    summary_table.add_column("Setting", style="cyan")
    summary_table.add_column("Value", style="green")
    summary_table.add_row("Block Name", block_name)
    summary_table.add_row("Canvas API URL", canvas_api_url)
    summary_table.add_row("Canvas Course ID", str(course_id))
    summary_table.add_row("Assets Block", assets_block)
    summary_table.add_row("Assets Prefix", assets_prefix)
    summary_table.add_row("Docker Image", docker_image or "Not set")
    summary_table.add_row("Work Pool", work_pool or "Not set")
    summary_table.add_row("Test Mappings", str(len(test_map_env)))

    console.print(summary_table)

    if interactive:
        if not Confirm.ask("\nSave this configuration?", default=True):
            console.print("[yellow]Configuration cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        block = CourseConfigBlock(
            canvas_api_url=HttpUrl(canvas_api_url),
            canvas_token=SecretStr(canvas_token),
            canvas_course_id=course_id,
            asset_bucket_block=assets_block,
            asset_path_prefix=assets_prefix,
            workspace_root=None,
            grader_image=docker_image,
            work_pool_name=work_pool,
            grader_env=grader_env,
        )
        block.save(block_name, overwrite=True)
        console.print(f"\n[green]✓ Course configuration saved as block: {block_name}[/green]")
        console.print(
            f"[blue]You can now use: ccc course run <assignment_id> --course {block_name}[/blue]"
        )
    except Exception as e:
        console.print(f"[red]Error saving course block: {e}[/red]")
        raise typer.Exit(1) from e


@course_app.command("list")
def course_list() -> None:
    """List all configured course blocks.

    [blue]Example:[/blue]
        $ ccc course list
    """
    try:
        blocks = CourseConfigBlock.find()  # type: ignore[attr-defined]
        if not blocks:
            console.print("[yellow]No course configuration blocks found[/yellow]")
            return

        table = Table(title="Configured Courses")
        table.add_column("Block Name", style="cyan")
        table.add_column("Canvas Course ID", style="green")
        table.add_column("Docker Image", style="yellow")
        table.add_column("Assets Block", style="blue")

        for block_slug in blocks:
            try:
                block = CourseConfigBlock.load(block_slug)
                table.add_row(
                    block_slug,
                    str(block.canvas_course_id),  # type: ignore[attr-defined]
                    block.grader_image or "Not set",  # type: ignore[attr-defined]
                    block.asset_bucket_block,  # type: ignore[attr-defined]
                )
            except Exception as e:  # noqa: BLE001
                table.add_row(block_slug, f"Error: {e}", "", "")

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing courses: {e}[/red]")
        raise typer.Exit(1) from e


# =============================================================================
# PLATFORM ADMINISTRATOR COMMANDS
# =============================================================================

system_app = typer.Typer(
    help="""[bold green]🔧 Platform Administration[/bold green]

Commands for platform administrators to manage infrastructure, webhooks, and deployments.

[dim]Typical operations:[/dim]
  • [dim]ccc system webhook serve[/dim]  - Start webhook server
  • [dim]ccc system deploy create[/dim]  - Create Prefect deployment
  • [dim]ccc system status[/dim]         - Check platform health""",
    rich_markup_mode="rich",
)

# Webhook subcommand
webhook_app = typer.Typer(
    help="Manage webhook server for Canvas submissions",
    rich_markup_mode="rich",
)


@webhook_app.command("serve")
def webhook_serve(
    host: Annotated[str, typer.Option("--host", help="Host to bind")] = "0.0.0.0",  # noqa: S104 # nosec B104 # nosonar
    port: Annotated[int, typer.Option("--port", help="Port to bind")] = 8080,
) -> None:
    """Start webhook server for Canvas submissions.

    [blue]Examples:[/blue]
        # Start on default host/port
        $ ccc system webhook serve

        # Start on custom host/port
        $ ccc system webhook serve --host 127.0.0.1 --port 9090
    """
    console.print(f"[blue]Starting webhook server on {host}:{port}[/blue]")
    uvicorn.run(webhook_fastapi_app, host=host, port=port)


system_app.add_typer(webhook_app, name="webhook")

# Deploy subcommand
deploy_app = typer.Typer(
    help="Manage Prefect deployments",
    rich_markup_mode="rich",
)


@deploy_app.command("create")
def deploy_create(
    course_block: Annotated[
        str,
        typer.Argument(help="Prefect course configuration block name"),
    ],
) -> None:
    """Create or update a Prefect deployment for webhook-triggered corrections.

    [blue]Example:[/blue]
        $ ccc system deploy create ccc-course-cs101
    """
    try:
        settings = resolve_settings_from_block(course_block)
    except Exception as e:
        console.print(f"[red]Error loading course block '{course_block}': {e}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[blue]Creating deployment for course block: {course_block}[/blue]")

    try:
        deployment_name = asyncio.run(ensure_deployment(course_block, settings))
        console.print(f"[green]Deployment '{deployment_name}' created/updated successfully[/green]")
        console.print(
            f"[yellow]Note: Ensure work pool "
            f"'{settings.grader.work_pool_name or 'local-pool'}' exists and has workers[/yellow]",
        )
    except Exception as e:
        console.print(f"[red]Error creating deployment: {e}[/red]")
        raise typer.Exit(1) from e


system_app.add_typer(deploy_app, name="deploy")


@system_app.command("status")
def system_status() -> None:
    """Check platform status and configuration.

    [blue]Example:[/blue]
        $ ccc system status
    """
    console.print("[bold blue]Platform Status[/bold blue]")

    # Check Prefect connection
    try:
        import requests

        prefect_url = "http://localhost:4200/api/health"
        response = requests.get(prefect_url, timeout=5)
        if response.status_code == 200:
            console.print("[green]✓ Prefect server: Running[/green]")
        else:
            console.print(f"[yellow]⚠ Prefect server: HTTP {response.status_code}[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Prefect server: Not reachable ({e})[/red]")

    # Check RustFS/S3
    try:
        import boto3
        from botocore.exceptions import EndpointConnectionError

        s3 = boto3.client(
            "s3",
            endpoint_url="http://localhost:9000",
            aws_access_key_id="rustfsadmin",
            aws_secret_access_key="rustfsadmin",
        )
        s3.list_buckets()
        console.print("[green]✓ RustFS (S3): Running[/green]")
    except EndpointConnectionError:
        console.print("[red]✗ RustFS (S3): Not reachable[/red]")
    except Exception as e:
        console.print(f"[yellow]⚠ RustFS (S3): Error ({e})[/yellow]")

    console.print("\n[dim]Use 'ccc course list' to see configured courses[/dim]")


# =============================================================================
# MAIN APP SETUP
# =============================================================================

app.add_typer(course_app, name="course")
app.add_typer(system_app, name="system")


@app.callback()
def main_callback(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Show version information"),
    ] = False,
) -> None:
    """Canvas Code Correction CLI.

    [bold]Command Groups:[/bold]
    • [blue]ccc course[/blue]  - Course administration (setup, run, list)
    • [green]ccc system[/green] - Platform administration (webhook, deploy, status)

    [bold]Quick Start:[/bold]
    1. Setup a course:    [dim]ccc course setup[/dim]
    2. Grade submissions: [dim]ccc course run <assignment_id> --course <block>[/dim]
    3. Start webhook:     [dim]ccc system webhook serve[/dim]

    For detailed help: [dim]ccc <command> --help[/dim]
    """
    if version:
        try:
            version_str = importlib.metadata.version("canvas-code-correction")
        except importlib.metadata.PackageNotFoundError:
            version_str = "v2.0.0a0"
        console.print(f"Canvas Code Correction {version_str}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
