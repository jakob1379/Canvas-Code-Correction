"""Command-line interface for Canvas Code Correction."""

from __future__ import annotations

import importlib.metadata
import json
import tempfile
from pathlib import Path
from typing import Annotated

import typer
from pydantic import HttpUrl, SecretStr
from rich.console import Console
from rich.table import Table

from canvas_code_correction.clients import build_canvas_resources
from canvas_code_correction.config import resolve_settings_from_block
from canvas_code_correction.flows import (
    CorrectSubmissionPayload,
    correct_submission_flow,
)
from canvas_code_correction.prefect_blocks import CourseConfigBlock

app = typer.Typer(help="Canvas Code Correction CLI")
console = Console()


@app.command()
def run_once(
    assignment_id: Annotated[int, typer.Argument(help="Canvas assignment ID")],
    submission_id: Annotated[
        int | None,
        typer.Option(
            None, help="Specific submission ID (default: all submissions)"
        ),
    ] = None,
    course_block: Annotated[
        str,
        typer.Option(
            "--course", "-c", help="Prefect course configuration block name"
        ),
    ] = "default-course",
    download_dir: Annotated[
        Path | None,
        typer.Option(
            None,
            help="Directory for downloaded submissions (default: temporary directory)",
        ),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Skip actual grading and upload")
    ] = False,
) -> None:
    """Run correction flow for an assignment or specific submission."""
    try:
        settings = resolve_settings_from_block(course_block)
    except Exception as e:
        console.print(
            f"[red]Error loading course block '{course_block}': {e}[/red]"
        )
        raise typer.Exit(1) from e

    if download_dir is None:
        download_dir = Path(tempfile.mkdtemp(prefix="ccc-download-"))
        console.print(
            f"[yellow]Using temporary download directory: {download_dir}[/yellow]"
        )

    if submission_id:
        payload = CorrectSubmissionPayload(
            assignment_id=assignment_id,
            submission_id=submission_id,
        )
        console.print(
            f"[blue]Running correction for assignment {assignment_id}, "
            f"submission {submission_id}[/blue]"
        )
    else:
        # Batch mode: process all submissions
        console.print(
            f"[blue]Batch mode: processing all submissions for assignment {assignment_id}[/blue]"
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
                console.print(
                    f"[green]Submission {sub_id} processed successfully[/green]"
                )
                # Optional: collect summary
            except Exception as e:
                console.print(
                    f"[red]Error processing submission {sub_id}: {e}[/red]"
                )
                # Continue with next submission
                continue

        console.print("[green]Batch processing completed![/green]")
        raise typer.Exit(0)

    if dry_run:
        console.print(
            "[yellow]Dry run enabled - no actual grading or upload will occur[/yellow]"
        )

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
                    "submission_metadata_keys": list(
                        result.submission_metadata.keys()
                    ),
                    "downloaded_files_count": len(result.downloaded_files),
                    "workspace": str(result.workspace.root)
                    if result.workspace
                    else None,
                    "results_keys": list(result.results.keys()),
                },
                indent=2,
            )
        )
    except Exception as e:
        console.print(f"[red]Error running correction flow: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def configure_course(
    course_slug: Annotated[
        str, typer.Argument(help="Unique identifier for the course")
    ],
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
    canvas_course_id: Annotated[
        int, typer.Option("--course-id", "-i", help="Canvas course ID")
    ],
    asset_bucket_block: Annotated[
        str,
        typer.Option(
            "--assets-block",
            "-a",
            help="Prefect S3 bucket block name for assets",
        ),
    ],
    canvas_api_url: Annotated[
        str, typer.Option("--api-url", help="Canvas instance URL")
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
    """Create or update a course configuration block."""
    block_name = f"ccc-course-{course_slug}"

    # Parse environment variables
    grader_env = {}
    if env_var:
        for env_str in env_var:
            if "=" in env_str:
                key, value = env_str.split("=", 1)
                grader_env[key.strip()] = value.strip()
            else:
                console.print(
                    f"[yellow]Skipping invalid env var: {env_str}[/yellow]"
                )

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
        console.print(
            f"[green]Course configuration saved as block: {block_name}[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error saving course block: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def list_courses() -> None:
    """List all configured course blocks."""
    try:
        blocks = CourseConfigBlock.find()  # type: ignore
        if not blocks:
            console.print(
                "[yellow]No course configuration blocks found[/yellow]"
            )
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
                    str(block.canvas_course_id),  # type: ignore
                    block.grader_image or "Not set",  # type: ignore
                    block.asset_bucket_block,  # type: ignore
                )
            except Exception as e:
                table.add_row(block_slug, f"Error: {e}", "", "")

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing courses: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def version() -> None:
    """Show version information."""
    try:
        version = importlib.metadata.version("canvas-code-correction")
    except importlib.metadata.PackageNotFoundError:
        version = "v2.0.0a0"
    console.print(f"Canvas Code Correction {version}")


if __name__ == "__main__":
    app()
