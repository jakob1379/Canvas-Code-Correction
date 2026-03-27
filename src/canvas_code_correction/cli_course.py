from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Callable, TypedDict, cast

import requests
import typer
from canvasapi.exceptions import CanvasException
from pydantic import HttpUrl, SecretStr
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from slugify import slugify

if TYPE_CHECKING:
    from canvasapi.course import Course

    from canvasapi import Canvas

    from canvas_code_correction.config import Settings
    from canvas_code_correction.flows.correction import FlowArtifacts


ASCII_CONTROL_MAX = 32
ASCII_DELETE = 127
BATCH_SUBMISSION_EXCEPTIONS = (RuntimeError, ValueError, TypeError, KeyError, OSError)
COURSE_BLOCK_LOAD_EXCEPTIONS = (RuntimeError, ValueError, TypeError, KeyError, AttributeError)
SUGGESTED_SLUG_EXCEPTIONS = (CanvasException, requests.RequestException, TypeError, AttributeError)
CANVAS_API_URL_DEFAULT = "https://canvas.instructure.com"
CANVAS_URL_SCHEME = "https://"


@dataclass(frozen=True)
class CourseSetupConfig:
    block_name: str
    canvas_api_url: str
    canvas_token: str
    selected_course_id: int
    assets_block: str
    assets_prefix: str
    work_pool: str
    docker_image: str
    test_map_count: int
    grader_env: dict[str, str]


@dataclass(frozen=True)
class CourseRunOptions:
    submission_id: int | None
    course_block: str
    download_dir: Path | None
    dry_run: bool


@dataclass(frozen=True)
class CourseSetupOptions:
    token_stdin: bool
    canvas_api_url: str | None
    canvas_token: str | None
    course_id: int
    docker_image: str
    map_assignments: list[str]
    env_var: list[str]
    interactive: bool
    assets_block: str | None
    slug: str | None
    assets_prefix: str | None
    work_pool: str | None


class CourseConfigBlockPayload(TypedDict):
    canvas_api_url: HttpUrl
    canvas_token: SecretStr
    canvas_course_id: int
    asset_bucket_block: str
    asset_path_prefix: str
    grader_image: str
    work_pool_name: str
    grader_env: dict[str, str]


def _run_cli_step[T](console, step: str, action: Callable[[], T]) -> T:
    try:
        return action()
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]{step}: {exc}[/red]")
        raise typer.Exit(1) from exc


def _has_control_chars(value: str) -> bool:
    return any(ord(char) < ASCII_CONTROL_MAX or ord(char) == ASCII_DELETE for char in value)


def _switch_stdin_to_tty_for_prompts(console) -> None:
    if sys.stdin.isatty():
        return

    try:
        sys.stdin = io.TextIOWrapper(io.FileIO("/dev/tty"), encoding="utf-8")
    except OSError as exc:
        console.print(
            "[red]Error: --token-stdin with interactive setup requires a TTY for prompts[/red]"
        )
        console.print(
            "[yellow]Use --no-interactive with required options, or pass --token for manual entry[/yellow]",
        )
        raise typer.Exit(1) from exc


def _resolve_canvas_api_url(canvas_api_url: str | None, console) -> str:
    normalized_url = (canvas_api_url or CANVAS_API_URL_DEFAULT).strip()
    if not normalized_url:
        console.print("[red]Error: Canvas API URL cannot be empty[/red]")
        raise typer.Exit(1)

    if _has_control_chars(normalized_url):
        console.print("[red]Error: Canvas API URL contains control characters[/red]")
        console.print(
            "[yellow]Tip: Re-type the URL manually or pass --api-url to avoid terminal paste issues[/yellow]"
        )
        raise typer.Exit(1)

    if "/api/v1" in normalized_url:
        normalized_url = normalized_url.split("/api/v1", 1)[0]

    if "://" not in normalized_url:
        normalized_url = f"{CANVAS_URL_SCHEME}{normalized_url}"

    return normalized_url.rstrip("/")


@dataclass(frozen=True)
class CanvasClientValidationError(Exception):
    show_common_hints: bool = False


def _resolve_canvas_token(
    canvas_token: str | None,
    *,
    token_stdin: bool,
    interactive: bool,
    console,
    Prompt,
) -> str:
    if token_stdin:
        if canvas_token is not None:
            console.print("[red]Use either --token or --token-stdin, not both[/red]")
            raise typer.Exit(1)

        token_from_stdin = sys.stdin.read().strip()
        if not token_from_stdin:
            console.print("[red]Error: No Canvas credential received on stdin[/red]")
            raise typer.Exit(1)

        if _has_control_chars(token_from_stdin):
            console.print(
                "[red]Error: Canvas credential from stdin contains control characters[/red]"
            )
            console.print(
                '[yellow]Tip: Use `printf %s "$CANVAS_API_TOKEN"` instead of `echo` to avoid extra characters[/yellow]'
            )
            raise typer.Exit(1)

        return token_from_stdin

    if canvas_token is None:
        if interactive:
            canvas_token = Prompt.ask("Enter your Canvas API token", password=True)
        else:
            console.print("[red]--token or --token-stdin is required in non-interactive mode[/red]")
            raise typer.Exit(1)

    normalized_token = canvas_token.strip()
    if not normalized_token:
        if len(canvas_token) == 0:
            return normalized_token
        console.print("[red]Error: Canvas credential cannot be empty[/red]")
        raise typer.Exit(1)

    if _has_control_chars(normalized_token):
        console.print("[red]Error: Canvas credential contains control characters[/red]")
        console.print(
            "[yellow]Tip: Re-paste the credential or use stdin input with printf to avoid shell artifacts[/yellow]"
        )
        raise typer.Exit(1)

    return normalized_token


def _build_canvas_client(canvas_api_url: str, canvas_credential: str, *, Canvas) -> Canvas:
    try:
        canvas = Canvas(canvas_api_url, canvas_credential)
        _ = canvas.get_current_user()
    except (CanvasException, requests.RequestException) as exc:
        error_msg = str(exc)
        raise CanvasClientValidationError(
            show_common_hints=(
                "port 80" in error_msg.lower() or "bad request" in error_msg.lower()
            ),
        ) from exc
    except Exception as exc:
        raise CanvasClientValidationError from exc
    else:
        return canvas


def _print_canvas_validation_failure(
    canvas_api_url: str, *, show_common_hints: bool, console
) -> None:
    console.print("[red]Error: Failed to validate Canvas credentials[/red]")
    if not show_common_hints:
        return

    console.print("[yellow]This error often occurs when:[/yellow]")
    console.print(f"  • The Canvas URL is incorrect (missing {CANVAS_URL_SCHEME})")
    console.print("  • The provided Canvas credential is invalid or expired")
    console.print("  • There's a proxy or firewall blocking HTTPS requests")
    console.print(f"[dim]Attempted URL: {canvas_api_url}[/dim]")


def _fetch_canvas_courses(canvas: Canvas, *, console) -> list[Course]:
    try:
        return list(canvas.get_courses())
    except (CanvasException, requests.RequestException) as exc:
        console.print(f"[red]Error fetching courses: {exc}[/red]")
        raise typer.Exit(1) from exc


def _resolve_provided_course(canvas: Canvas, course_id: int, *, console) -> tuple[int, Course]:
    try:
        course = canvas.get_course(course_id)
    except (CanvasException, requests.RequestException, Exception) as exc:
        console.print(f"[red]Course ID {course_id} not found[/red]")
        raise typer.Exit(1) from exc
    else:
        console.print(f"[green]✓ Course ID {course_id} validated[/green]")
        return course_id, course


def _prompt_course_selection(courses: list[Course], *, console) -> list[Course]:
    console.print("\n[bold]Fetching available courses from Canvas...[/bold]")
    if not courses:
        console.print("[yellow]No courses found for this user[/yellow]")
        raise typer.Exit(1)

    console.print("\n[bold]Available Courses:[/bold]")
    for idx, course in enumerate(courses, 1):
        name = course.name or "Unnamed"
        course_code = course.course_code or "N/A"
        console.print(f"  [cyan]{idx}.[/cyan] [green]{name}[/green] [dim]({course_code})[/dim]")

    console.print()
    return courses


def _resolve_interactive_course_selection(
    canvas: Canvas, *, console, IntPrompt
) -> tuple[int, Course]:
    courses = _prompt_course_selection(
        _fetch_canvas_courses(canvas, console=console), console=console
    )
    total_courses = len(courses)
    while True:
        selection = IntPrompt.ask(f"Select a course [1-{total_courses}]")
        if not 1 <= selection <= total_courses:
            console.print(
                "[yellow]Selection "
                f"{selection} is not between 1 and {total_courses}. Please try again.[/yellow]",
            )
            continue
        course = courses[selection - 1]
        console.print(
            f"[green]✓ Selected: {course.name or 'Unnamed'} (Canvas ID: {course.id})[/green]"
        )
        return course.id, course


def _resolve_course_selection(
    canvas: Canvas, provided_course_id: int | None, *, interactive: bool, console, IntPrompt
) -> tuple[int, Course]:
    if provided_course_id is not None:
        return _resolve_provided_course(canvas, provided_course_id, console=console)

    if not interactive:
        console.print("[red]Error: --course-id is required in non-interactive mode[/red]")
        raise typer.Exit(1)

    return _resolve_interactive_course_selection(canvas, console=console, IntPrompt=IntPrompt)


def _parse_test_mappings(mappings: list[str], *, console) -> dict[str, str]:
    test_map_env: dict[str, str] = {}
    for mapping in mappings:
        if ":" not in mapping:
            console.print(f"[yellow]Skipping invalid test mapping: {mapping}[/yellow]")
            continue
        try:
            assignment_id_str, test_path = mapping.split(":", 1)
            assignment_id = int(assignment_id_str)
            test_map_env[f"CCC_TEST_MAP_{assignment_id}"] = test_path
        except ValueError:
            console.print(f"[yellow]Skipping invalid assignment ID in: {mapping}[/yellow]")
    return test_map_env


def _request_test_mappings(course: Course, *, console, Confirm, Prompt) -> dict[str, str]:
    test_map_env: dict[str, str] = {}
    console.print("\n[bold]Fetching assignments from course...[/bold]")
    try:
        assignments = list(course.get_assignments())
    except (CanvasException, requests.RequestException) as exc:
        console.print(f"[yellow]Warning: Could not fetch assignments: {exc}[/yellow]")
        return test_map_env

    if not assignments:
        console.print("[yellow]No assignments found in this course[/yellow]")
        return test_map_env

    table = Table(title=f"Assignments in {course.name}")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Published", style="blue")

    for assignment in assignments:
        table.add_row(
            str(assignment.id),
            assignment.name or "Unnamed",
            "✓" if getattr(assignment, "published", False) else "✗",
        )

    console.print(table)

    if not Confirm.ask("\nWould you like to map local test files to assignments?", default=True):
        return test_map_env

    console.print("\n[yellow]Enter test mappings (press Enter with no input to finish):[/yellow]")
    console.print("Format: [dim]assignment_id:/path/to/test.py[/dim]")

    while True:
        mapping = Prompt.ask("Test mapping", default="")
        if not mapping:
            break

        if ":" not in mapping:
            console.print("[yellow]Invalid format. Use: assignment_id:/path/to/test.py[/yellow]")
            continue

        assignment_id_str, test_path = mapping.split(":", 1)
        try:
            assignment_id = int(assignment_id_str)
        except ValueError:
            console.print("[yellow]Invalid assignment ID (must be a number)[/yellow]")
            continue

        try:
            course.get_assignment(assignment_id)
        except CanvasException as exc:
            console.print(f"[yellow]Warning: Could not validate assignment: {exc}[/yellow]")
            test_map_env[f"CCC_TEST_MAP_{assignment_id_str}"] = test_path
            continue

        test_map_env[f"CCC_TEST_MAP_{assignment_id}"] = test_path
        console.print(f"[green]✓ Mapped assignment {assignment_id} → {test_path}[/green]")

    return test_map_env


def _collect_test_mappings(
    course: Course, test_mappings: list[str] | None, *, interactive: bool, console, Confirm, Prompt
) -> dict[str, str]:
    if test_mappings:
        return _parse_test_mappings(test_mappings, console=console)
    if not interactive:
        return {}
    return _request_test_mappings(course, console=console, Confirm=Confirm, Prompt=Prompt)


def _parse_course_run_options(args: list[str], *, console) -> CourseRunOptions:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--submission-id", type=int, default=None)
    parser.add_argument("--course", "-c", default="default-course")
    parser.add_argument("--download-dir", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")

    parsed, unknown_args = parser.parse_known_args(args)
    if unknown_args:
        console.print(f"[red]Unknown option(s): {', '.join(unknown_args)}[/red]")
        raise typer.Exit(2)

    return CourseRunOptions(
        submission_id=parsed.submission_id,
        course_block=parsed.course,
        download_dir=parsed.download_dir,
        dry_run=parsed.dry_run,
    )


def _parse_course_setup_options(args: list[str], *, console) -> CourseSetupOptions:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--token-stdin", action="store_true")
    parser.add_argument("--token", default=None)
    parser.add_argument("--api-url", "-u", default=None)
    parser.add_argument("--course-id", "-c", type=int, default=0)
    parser.add_argument("--docker-image", "-d", default="jakob1379/canvas-grader:latest")
    parser.add_argument(
        "--map-assignments", "--test-map", dest="map_assignments", action="append", default=None
    )
    parser.add_argument("--env", "-e", action="append", default=None)
    parser.add_argument("--interactive", dest="interactive", action="store_true")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false")
    parser.set_defaults(interactive=True)
    parser.add_argument("--assets-block", default=None)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--assets-prefix", default=None)
    parser.add_argument("--work-pool", default=None)

    parsed, unknown_args = parser.parse_known_args(args)
    if unknown_args:
        console.print(f"[red]Unknown option(s): {', '.join(unknown_args)}[/red]")
        raise typer.Exit(2)

    return CourseSetupOptions(
        token_stdin=parsed.token_stdin,
        canvas_api_url=parsed.api_url,
        canvas_token=parsed.token,
        course_id=parsed.course_id,
        docker_image=parsed.docker_image,
        map_assignments=parsed.map_assignments or [],
        env_var=parsed.env or [],
        interactive=parsed.interactive,
        assets_block=parsed.assets_block or None,
        slug=parsed.slug or None,
        assets_prefix=parsed.assets_prefix or None,
        work_pool=parsed.work_pool or None,
    )


def _prompt_optional_value(
    value: str | None,
    prompt_text: str,
    *,
    interactive: bool,
    default: str | None = None,
    Prompt,
) -> str | None:
    if value is not None or not interactive:
        return value
    response = Prompt.ask(prompt_text, default=default or "")
    if not response:
        return default
    return response


def _build_grader_env(
    env_var: list[str] | None, test_map_env: dict[str, str], *, console
) -> dict[str, str]:
    grader_env: dict[str, str] = {}
    if env_var:
        for env_str in env_var:
            if "=" in env_str:
                key, value = env_str.split("=", 1)
                grader_env[key.strip()] = value.strip()
            else:
                console.print(f"[yellow]Skipping invalid env var: {env_str}[/yellow]")
    grader_env.update(test_map_env)
    return grader_env


def _resolve_course_run_download_dir(download_dir: Path | None, *, console) -> Path:
    if download_dir is not None:
        return download_dir
    resolved = Path(tempfile.mkdtemp(prefix="ccc-download-"))
    console.print(f"[yellow]Using temporary download directory: {resolved}[/yellow]")
    return resolved


def _print_flow_result(result: FlowArtifacts, *, console) -> None:
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


def _run_single_submission(
    payload,
    settings: Settings,
    *,
    download_dir: Path,
    dry_run: bool,
    console,
    correct_submission_flow,
) -> FlowArtifacts:
    if dry_run:
        console.print("[yellow]Dry run enabled - no actual grading or upload will occur[/yellow]")
    return _run_cli_step(
        console,
        "Error running correction flow",
        lambda: correct_submission_flow(
            payload, settings, download_dir=download_dir, dry_run=dry_run
        ),
    )


def _run_assignment_batch(
    assignment_id: int,
    settings: Settings,
    *,
    download_dir: Path,
    dry_run: bool,
    console,
    build_canvas_resources,
    correct_submission_flow,
    CorrectSubmissionPayload,
) -> None:
    console.print(
        f"[blue]Batch mode: processing all submissions for assignment {assignment_id}[/blue]"
    )
    resources = build_canvas_resources(settings)
    assignment = resources.course.get_assignment(assignment_id)
    submissions = assignment.get_submissions()
    failed_submission_ids: list[int] = []
    for submission in submissions:
        sub_id = submission.id
        console.print(f"[blue]Processing submission {sub_id}[/blue]")
        payload = CorrectSubmissionPayload(assignment_id=assignment_id, submission_id=sub_id)
        try:
            correct_submission_flow(
                payload, settings, resources=resources, download_dir=download_dir, dry_run=dry_run
            )
            console.print(f"[green]Submission {sub_id} processed successfully[/green]")
        except BATCH_SUBMISSION_EXCEPTIONS as exc:
            console.print(f"[red]Error processing submission {sub_id}: {exc}[/red]")
            failed_submission_ids.append(sub_id)
            continue

    if failed_submission_ids:
        console.print(
            "[red]Batch processing completed with failures: "
            f"{', '.join(str(sub_id) for sub_id in failed_submission_ids)}[/red]",
        )
        raise typer.Exit(1)

    console.print("[green]Batch processing completed![/green]")


def _suggest_course_slug(selected_course_id: int, course: Course) -> str:
    try:
        course_code = course.course_code or f"course-{selected_course_id}"
        return f"{selected_course_id}-{slugify(str(course_code))}"
    except SUGGESTED_SLUG_EXCEPTIONS:
        return f"{selected_course_id}-course"


def _resolve_docker_image(docker_image: str, *, interactive: bool, console, Prompt) -> str:
    if not interactive:
        return docker_image
    return Prompt.ask("Docker image for grading", default=docker_image)


def _build_course_setup_config(
    selected_course_id: int,
    course: Course,
    options: CourseSetupOptions,
    *,
    console,
    Prompt,
    Confirm,
) -> CourseSetupConfig:
    suggested_slug = _suggest_course_slug(selected_course_id, course)
    slug_input = _prompt_optional_value(
        options.slug,
        "Course slug",
        interactive=options.interactive,
        default=suggested_slug,
        Prompt=Prompt,
    )
    course_slug = slugify(slug_input or suggested_slug)
    block_name = f"ccc-course-{course_slug}"

    default_assets_block = f"ccc-assets-{course_slug}"
    if options.assets_block:
        assets_block = options.assets_block
    else:
        if not options.interactive:
            console.print("[red]--assets-block is required in non-interactive mode[/red]")
            raise typer.Exit(1)
        prompted_assets_block = _prompt_optional_value(
            None,
            "Assets block (Prefect block storing S3 credentials)",
            interactive=True,
            default=default_assets_block,
            Prompt=Prompt,
        )
        assets_block = prompted_assets_block or default_assets_block

    assets_prefix_input = _prompt_optional_value(
        options.assets_prefix,
        "Assets prefix (S3 path prefix)",
        interactive=options.interactive,
        default=f"graders/{course_slug}/",
        Prompt=Prompt,
    )
    assets_prefix = assets_prefix_input or f"graders/{course_slug}/"

    work_pool_input = _prompt_optional_value(
        options.work_pool,
        "Work pool name",
        interactive=options.interactive,
        default=f"course-work-pool-{course_slug}",
        Prompt=Prompt,
    )
    work_pool = work_pool_input or f"course-work-pool-{course_slug}"

    resolved_docker_image = _resolve_docker_image(
        options.docker_image,
        interactive=options.interactive,
        console=console,
        Prompt=Prompt,
    )
    test_map_env = _collect_test_mappings(
        course,
        options.map_assignments,
        interactive=options.interactive,
        console=console,
        Confirm=Confirm,
        Prompt=Prompt,
    )
    grader_env = _build_grader_env(options.env_var, test_map_env, console=console)

    return CourseSetupConfig(
        block_name=block_name,
        canvas_api_url=options.canvas_api_url or CANVAS_API_URL_DEFAULT,
        canvas_token=options.canvas_token or "",
        selected_course_id=selected_course_id,
        assets_block=assets_block,
        assets_prefix=assets_prefix,
        work_pool=work_pool,
        docker_image=resolved_docker_image,
        test_map_count=len(test_map_env),
        grader_env=grader_env,
    )


def _print_course_setup_summary(config: CourseSetupConfig, *, console) -> None:
    console.print("\n[bold]Configuration Summary:[/bold]")
    summary_table = Table(show_header=False)
    summary_table.add_column("Setting", style="cyan")
    summary_table.add_column("Value", style="green")
    summary_table.add_row("Block Name", config.block_name)
    summary_table.add_row("Canvas API URL", config.canvas_api_url)
    summary_table.add_row("Canvas Course ID", str(config.selected_course_id))
    summary_table.add_row("Assets Block", config.assets_block)
    summary_table.add_row("Assets Prefix", config.assets_prefix)
    summary_table.add_row("Work Pool", config.work_pool)
    summary_table.add_row("Docker Image", config.docker_image)
    summary_table.add_row("Test Mappings", str(config.test_map_count))
    console.print(summary_table)


def _build_course_block_payload(config: CourseSetupConfig) -> CourseConfigBlockPayload:
    return {
        "canvas_api_url": HttpUrl(config.canvas_api_url),
        "canvas_token": SecretStr(config.canvas_token),
        "canvas_course_id": config.selected_course_id,
        "asset_bucket_block": config.assets_block,
        "asset_path_prefix": config.assets_prefix,
        "grader_image": config.docker_image,
        "work_pool_name": config.work_pool,
        "grader_env": config.grader_env,
    }


def _save_course_block(config: CourseSetupConfig, *, console, CourseConfigBlock) -> None:
    try:
        block = CourseConfigBlock(
            **cast("CourseConfigBlockPayload", _build_course_block_payload(config))
        )
        block.save(config.block_name, overwrite=True)
    except (RuntimeError, ValueError, TypeError) as exc:
        console.print(f"[red]Error saving course block: {exc}[/red]")
        raise typer.Exit(1) from exc

    console.print(f"\n[green]✓ Course configuration saved as block: {config.block_name}[/green]")
    console.print(
        f"[blue]You can now use: ccc course run <assignment_id> --course {config.block_name}[/blue]"
    )


def course_run_command(
    ctx: typer.Context,
    assignment_id: int,
    *,
    console,
    load_settings_from_course_block,
    build_canvas_resources,
    correct_submission_flow,
    CorrectSubmissionPayload,
    _run_cli_step=_run_cli_step,
) -> None:
    options = _parse_course_run_options(ctx.args, console=console)
    settings = _run_cli_step(
        console,
        "Error loading course block",
        lambda: load_settings_from_course_block(options.course_block),
    )
    resolved_download_dir = _resolve_course_run_download_dir(options.download_dir, console=console)

    if options.submission_id is not None:
        payload = CorrectSubmissionPayload(
            assignment_id=assignment_id, submission_id=options.submission_id
        )
        console.print(
            f"[blue]Running correction for assignment {assignment_id}, submission {options.submission_id}[/blue]"
        )
    else:
        _run_assignment_batch(
            assignment_id,
            settings,
            download_dir=resolved_download_dir,
            dry_run=options.dry_run,
            console=console,
            build_canvas_resources=build_canvas_resources,
            correct_submission_flow=correct_submission_flow,
            CorrectSubmissionPayload=CorrectSubmissionPayload,
        )
        raise typer.Exit(0)

    result = _run_single_submission(
        payload,
        settings,
        download_dir=resolved_download_dir,
        dry_run=options.dry_run,
        console=console,
        correct_submission_flow=correct_submission_flow,
    )
    _print_flow_result(result, console=console)


def course_setup_command(
    ctx: typer.Context,
    *,
    console,
    Canvas,
    CourseConfigBlock,
    Prompt,
    IntPrompt,
    Confirm,
    _switch_stdin_to_tty_for_prompts=_switch_stdin_to_tty_for_prompts,
) -> None:
    console.print(Panel.fit("[bold blue]Canvas Code Correction - Course Setup[/bold blue]"))
    options = _parse_course_setup_options(ctx.args, console=console)

    canvas_credential = _resolve_canvas_token(
        options.canvas_token,
        token_stdin=options.token_stdin,
        interactive=options.interactive,
        console=console,
        Prompt=Prompt,
    )
    if options.token_stdin and options.interactive:
        _switch_stdin_to_tty_for_prompts(console)
    canvas_api_url_input = (
        _prompt_optional_value(
            options.canvas_api_url,
            "Canvas host (domain or https:// URL)",
            interactive=options.interactive,
            default=CANVAS_API_URL_DEFAULT,
            Prompt=Prompt,
        )
        or CANVAS_API_URL_DEFAULT
    )
    canvas_api_url = _resolve_canvas_api_url(canvas_api_url_input, console)

    try:
        canvas = _build_canvas_client(canvas_api_url, canvas_credential, Canvas=Canvas)
    except CanvasClientValidationError as exc:
        _print_canvas_validation_failure(
            canvas_api_url, show_common_hints=exc.show_common_hints, console=console
        )
        raise typer.Exit(1) from exc

    console.print("[green]✓ Canvas access validated successfully[/green]")
    selected_course_id, course = _resolve_course_selection(
        canvas,
        options.course_id or None,
        interactive=options.interactive,
        console=console,
        IntPrompt=IntPrompt,
    )
    setup_config = _build_course_setup_config(
        selected_course_id,
        course,
        CourseSetupOptions(
            token_stdin=options.token_stdin,
            canvas_api_url=canvas_api_url,
            canvas_token=canvas_credential,
            course_id=options.course_id,
            docker_image=options.docker_image,
            map_assignments=options.map_assignments,
            env_var=options.env_var,
            interactive=options.interactive,
            assets_block=options.assets_block,
            slug=options.slug,
            assets_prefix=options.assets_prefix,
            work_pool=options.work_pool,
        ),
        console=console,
        Prompt=Prompt,
        Confirm=Confirm,
    )
    _print_course_setup_summary(setup_config, console=console)

    if options.interactive and not Confirm.ask("\nSave this configuration?", default=True):
        console.print("[yellow]Configuration cancelled[/yellow]")
        raise typer.Exit(0)

    _save_course_block(config=setup_config, console=console, CourseConfigBlock=CourseConfigBlock)


def course_list_command(
    *, console, _run_cli_step=_run_cli_step, find_course_block_names, load_course_block
) -> None:
    blocks = _run_cli_step(console, "Error listing courses", find_course_block_names)
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
            block = load_course_block(block_slug)
            table.add_row(
                block_slug,
                str(block.canvas_course_id),
                block.grader_image or "Not set",
                block.asset_bucket_block,
            )
        except COURSE_BLOCK_LOAD_EXCEPTIONS as exc:
            table.add_row(block_slug, f"Error: {exc}", "", "")

    console.print(table)
