from __future__ import annotations

import io
import itertools
import json
import os
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypedDict

import requests
import typer
import yaml
from canvasapi.exceptions import CanvasException
from prefect.client.orchestration import get_client
from prefect.exceptions import ObjectNotFound
from prefect_aws.s3 import S3Bucket
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr, ValidationError
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from slugify import slugify

from canvas_code_correction.storage import (
    RustfsProvisioningError,
    RustfsStorageConfig,
    build_bucket_name,
    build_credentials,
    create_course_bucket,
    delete_stale_objects,
    seed_ambient_storage_env,
    upload_directory_with_credentials,
    verify_course_runtime_access,
)

if TYPE_CHECKING:
    from canvasapi import Canvas
    from canvasapi.course import Course

    from canvas_code_correction.config import Settings
    from canvas_code_correction.flows.correction import FlowArtifacts
    from rich.console import Console


ASCII_CONTROL_MAX = 32
ASCII_DELETE = 127
BATCH_SUBMISSION_EXCEPTIONS = (RuntimeError, ValueError, TypeError, KeyError, OSError)
COURSE_BLOCK_LOAD_EXCEPTIONS = (RuntimeError, ValueError, TypeError, KeyError, AttributeError)
SUGGESTED_SLUG_EXCEPTIONS = (CanvasException, requests.RequestException, TypeError, AttributeError)
CANVAS_API_URL_DEFAULT = "https://canvas.instructure.com"
CANVAS_URL_SCHEME = "https://"
WORK_PACKAGE_MAPPING_FORMAT = "<assignment id>:<path to work package root>"
WORK_PACKAGE_MAPPING_EXAMPLE = "59160606:/path/to/my-work-package"
WORK_PACKAGE_MANIFEST_FILENAME = "work-package.yaml"
WORK_PACKAGE_ASSET_DIR_CANDIDATES = ("grader", "assets")
DEFAULT_RUSTFS_ENDPOINT = "http://localhost:9000"
DEFAULT_RUSTFS_ACCESS_KEY = "rustfsadmin"
DEFAULT_RUSTFS_SECRET_KEY = "rustfsadmin"  # noqa: S105 # nosec B105
DEFAULT_AWS_REGION = "us-east-1"


class WorkPackageManifest(BaseModel):
    """The part of `work-package.yaml` that CCC reads; other keys pass through."""

    model_config = ConfigDict(extra="allow")

    schema_version: int = 1
    assignment_ids: list[int] = Field(default_factory=list)


@dataclass(frozen=True)
class WorkPackagePlan:
    assignment_id: int
    root: Path
    asset_source_dir: Path
    prefix: str


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
    work_package_plans: tuple[WorkPackagePlan, ...]
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
    work_packages: list[str]
    env_var: list[str]
    interactive: bool


class CourseConfigBlockPayload(TypedDict):
    canvas_api_url: HttpUrl
    canvas_token: SecretStr
    canvas_course_id: int
    asset_bucket_block: str
    asset_path_prefix: str
    assignment_asset_prefixes: dict[int, str]
    storage_auth_mode: str
    grader_image: str
    work_pool_name: str
    grader_env: dict[str, str]


def _run_cli_step[T](console: Console, step: str, action: Callable[[], T]) -> T:
    try:
        return action()
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]{step}: {exc}[/red]")
        raise typer.Exit(1) from exc


def _has_control_chars(value: str) -> bool:
    return any(ord(char) < ASCII_CONTROL_MAX or ord(char) == ASCII_DELETE for char in value)


def _switch_stdin_to_tty_for_prompts(console: Console) -> None:
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


def _resolve_canvas_api_url(canvas_api_url: str | None, console: Console) -> str:
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
    console: Console,
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
    canvas_api_url: str, *, show_common_hints: bool, console: Console
) -> None:
    console.print("[red]Error: Failed to validate Canvas credentials[/red]")
    if not show_common_hints:
        return

    console.print("[yellow]This error often occurs when:[/yellow]")
    console.print(f"  • The Canvas URL is incorrect (missing {CANVAS_URL_SCHEME})")
    console.print("  • The provided Canvas credential is invalid or expired")
    console.print("  • There's a proxy or firewall blocking HTTPS requests")
    console.print(f"[dim]Attempted URL: {canvas_api_url}[/dim]")


def _fetch_canvas_courses(canvas: Canvas, *, console: Console) -> list[Course]:
    try:
        return list(canvas.get_courses())
    except (CanvasException, requests.RequestException) as exc:
        console.print(f"[red]Error fetching courses: {exc}[/red]")
        raise typer.Exit(1) from exc


def _resolve_provided_course(
    canvas: Canvas, course_id: int, *, console: Console
) -> tuple[int, Course]:
    try:
        course = canvas.get_course(course_id)
    except (CanvasException, requests.RequestException, Exception) as exc:
        console.print(f"[red]Course ID {course_id} not found[/red]")
        raise typer.Exit(1) from exc
    else:
        console.print(f"[green]✓ Course ID {course_id} validated[/green]")
        return course_id, course


def _prompt_course_selection(courses: list[Course], *, console: Console) -> list[Course]:
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
    canvas: Canvas, *, console: Console, IntPrompt
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
    canvas: Canvas,
    provided_course_id: int | None,
    *,
    interactive: bool,
    console: Console,
    IntPrompt,
) -> tuple[int, Course]:
    if provided_course_id is not None:
        return _resolve_provided_course(canvas, provided_course_id, console=console)

    if not interactive:
        console.print("[red]Error: --course-id is required in non-interactive mode[/red]")
        raise typer.Exit(1)

    return _resolve_interactive_course_selection(canvas, console=console, IntPrompt=IntPrompt)


def _parse_work_package_mapping(mapping: str, *, console: Console) -> tuple[int, Path] | None:
    """Parse an ``<assignment id>:<path>`` mapping, reporting why it was skipped."""
    assignment_id_str, separator, raw_root = mapping.partition(":")
    root = raw_root.strip()
    if not separator or not root or not assignment_id_str.strip().isdigit():
        console.print(
            f"[yellow]Skipping invalid work-package mapping: {mapping}. "
            f"Use {WORK_PACKAGE_MAPPING_FORMAT}, for example {WORK_PACKAGE_MAPPING_EXAMPLE}[/yellow]"
        )
        return None
    return int(assignment_id_str), Path(root)


def _parse_work_package_mappings(mappings: list[str], *, console: Console) -> dict[int, Path]:
    parsed = (_parse_work_package_mapping(mapping, console=console) for mapping in mappings)
    return dict(mapping for mapping in parsed if mapping is not None)


def _resolve_work_package_root(root: Path, *, console: Console) -> Path:
    resolved = root.expanduser().resolve()
    if not resolved.is_dir():
        console.print(f"[red]Work-package root is not a directory: {resolved}[/red]")
        raise typer.Exit(1)
    return resolved


def _resolve_work_package_asset_source_dir(root: Path, *, console: Console) -> Path:
    for candidate_name in WORK_PACKAGE_ASSET_DIR_CANDIDATES:
        candidate = root / candidate_name
        if candidate.is_dir():
            return candidate

    candidate_list = " or ".join(f"`{name}/`" for name in WORK_PACKAGE_ASSET_DIR_CANDIDATES)
    console.print(f"[red]Work-package root {root} must contain {candidate_list}[/red]")
    raise typer.Exit(1)


def _build_work_package_plans(
    mappings: dict[int, Path], *, console: Console
) -> tuple[WorkPackagePlan, ...]:
    plans: list[WorkPackagePlan] = []
    for assignment_id, raw_root in sorted(mappings.items()):
        root = _resolve_work_package_root(raw_root, console=console)
        plans.append(
            WorkPackagePlan(
                assignment_id=assignment_id,
                root=root,
                asset_source_dir=_resolve_work_package_asset_source_dir(root, console=console),
                prefix=f"assignments/{assignment_id}",
            )
        )
    return tuple(plans)


def _load_work_package_manifest(manifest_path: Path, *, console: Console) -> WorkPackageManifest:
    if not manifest_path.exists():
        return WorkPackageManifest()

    try:
        raw_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        return WorkPackageManifest.model_validate(raw_data or {})
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        console.print(f"[red]Invalid work-package manifest {manifest_path}: {exc}[/red]")
        raise typer.Exit(1) from exc


def _manifest_header(manifest_path: Path) -> str:
    """Return the leading ``---``/comment lines so a rewrite keeps the schema pragma."""
    if not manifest_path.exists():
        return ""
    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    # Re-adding the newline per line also covers a header-only file saved without one,
    # which would otherwise fuse with the dumped body and swallow its first key.
    return "".join(
        f"{line}\n"
        for line in itertools.takewhile(lambda line: line.lstrip().startswith(("---", "#")), lines)
    )


def _sync_work_package_manifests(plans: tuple[WorkPackagePlan, ...], *, console: Console) -> None:
    """Record each mapped assignment ID in its work package's manifest."""
    assignment_ids_by_root: dict[Path, set[int]] = {}
    for plan in plans:
        assignment_ids_by_root.setdefault(plan.root, set()).add(plan.assignment_id)

    for root, assignment_ids in sorted(assignment_ids_by_root.items()):
        manifest_path = root / WORK_PACKAGE_MANIFEST_FILENAME
        manifest = _load_work_package_manifest(manifest_path, console=console)
        merged_ids = sorted(set(manifest.assignment_ids) | assignment_ids)
        if manifest_path.exists() and merged_ids == manifest.assignment_ids:
            continue

        manifest.assignment_ids = merged_ids
        try:
            manifest_path.write_text(
                _manifest_header(manifest_path)
                + yaml.safe_dump(manifest.model_dump(), sort_keys=False),
                encoding="utf-8",
            )
        except OSError as exc:
            console.print(f"[red]Failed to write {manifest_path}: {exc}[/red]")
            raise typer.Exit(1) from exc
        console.print(f"[green]✓ Recorded assignments {merged_ids} in {manifest_path}[/green]")


def _build_storage_config() -> RustfsStorageConfig:
    return RustfsStorageConfig(
        endpoint_url=os.getenv("RUSTFS_ENDPOINT", DEFAULT_RUSTFS_ENDPOINT),
        aws_access_key_id=os.getenv("RUSTFS_ACCESS_KEY", DEFAULT_RUSTFS_ACCESS_KEY),
        aws_secret_access_key=os.getenv("RUSTFS_SECRET_KEY", DEFAULT_RUSTFS_SECRET_KEY),
        region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", DEFAULT_AWS_REGION)),
    )


def _save_course_assets_block(
    block_name: str, bucket_name: str, storage: RustfsStorageConfig, *, console: Console
) -> None:
    block = S3Bucket(bucket_name=bucket_name, credentials=build_credentials(storage))
    try:
        block.save(block_name, overwrite=True)
    except (RuntimeError, TypeError, ValueError) as exc:
        console.print(f"[red]Failed to save assets block {block_name}: {exc}[/red]")
        raise typer.Exit(1) from exc

    console.print(f"[green]✓ Saved assets block: {block_name}[/green]")


def _upload_work_package(
    storage: RustfsStorageConfig, bucket_name: str, plan: WorkPackagePlan, *, console: Console
) -> None:
    """Upload a work package's assets, then prune objects the upload replaced."""
    source = plan.asset_source_dir
    uploaded_count = upload_directory_with_credentials(
        storage, bucket_name=bucket_name, local_path=source, to_path=plan.prefix
    )
    fresh_keys = {
        f"{plan.prefix}/{path.relative_to(source).as_posix()}"
        for path in source.rglob("*")
        if path.is_file()
    }
    pruned_count = delete_stale_objects(storage, bucket_name, plan.prefix, keep=fresh_keys)

    console.print(
        f"[green]✓ Uploaded {uploaded_count} asset(s) for assignment {plan.assignment_id} "
        f"to s3://{bucket_name}/{plan.prefix}[/green]"
    )
    if pruned_count:
        console.print(f"[dim]  removed {pruned_count} stale object(s)[/dim]")


def _provision_course_assets(config: CourseSetupConfig, *, console: Console) -> None:
    storage = _build_storage_config()
    bucket_name = build_bucket_name(config.assets_block)

    try:
        create_course_bucket(storage, bucket_name)
        console.print(f"[green]✓ Using assets bucket: {bucket_name}[/green]")
        _save_course_assets_block(config.assets_block, bucket_name, storage, console=console)
        for plan in config.work_package_plans:
            _upload_work_package(storage, bucket_name, plan, console=console)
        verify_course_runtime_access(storage, bucket_name)
    except RustfsProvisioningError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    console.print(f"[green]✓ Verified RustFS credential access to s3://{bucket_name}[/green]")


def _request_work_package_mappings(
    course: Course, *, console: Console, Confirm, Prompt
) -> dict[int, Path]:
    mappings: dict[int, Path] = {}
    console.print("\n[bold]Fetching assignments from course...[/bold]")
    try:
        assignments = list(course.get_assignments())
    except (CanvasException, requests.RequestException) as exc:
        console.print(f"[yellow]Warning: Could not fetch assignments: {exc}[/yellow]")
        return mappings

    if not assignments:
        console.print("[yellow]No assignments found in this course[/yellow]")
        return mappings

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

    if not Confirm.ask("\nWould you like to map local work packages to assignments?", default=True):
        return mappings

    console.print(
        "\n[yellow]Enter work package mappings (press Enter with no input to finish):[/yellow]"
    )
    console.print(f"Format: [dim]{WORK_PACKAGE_MAPPING_FORMAT}[/dim]")
    console.print(
        "[dim]Use the root directory of the work package, the folder that contains "
        "`grader/` or `assets/` "
        f"(for example `{WORK_PACKAGE_MAPPING_EXAMPLE}`).[/dim]"
    )
    console.print(
        "[dim]Mapped assignment IDs are recorded in the package's "
        f"`{WORK_PACKAGE_MANIFEST_FILENAME}` before the final save.[/dim]"
    )

    while True:
        mapping = Prompt.ask(
            "Work-package mapping (press Enter on empty input to finish)",
            default="",
            show_default=False,
        )
        if not mapping:
            break

        parsed_mapping = _parse_work_package_mapping(mapping, console=console)
        if parsed_mapping is None:
            continue

        assignment_id, root = parsed_mapping
        try:
            course.get_assignment(assignment_id)
        except (CanvasException, requests.RequestException) as exc:
            console.print(f"[yellow]Warning: Could not validate assignment: {exc}[/yellow]")
        else:
            console.print(f"[green]✓ Mapped assignment {assignment_id} → {root}[/green]")
        mappings[assignment_id] = root

    return mappings


def _collect_work_package_mappings(
    course: Course,
    work_packages: list[str] | None,
    *,
    interactive: bool,
    console: Console,
    Confirm,
    Prompt,
) -> dict[int, Path]:
    if work_packages:
        return _parse_work_package_mappings(work_packages, console=console)
    if not interactive:
        return {}
    return _request_work_package_mappings(course, console=console, Confirm=Confirm, Prompt=Prompt)


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


def _build_grader_env(env_var: list[str] | None, *, console: Console) -> dict[str, str]:
    grader_env: dict[str, str] = {}
    if env_var:
        for env_str in env_var:
            if "=" in env_str:
                key, value = env_str.split("=", 1)
                grader_env[key.strip()] = value.strip()
            else:
                console.print(f"[yellow]Skipping invalid env var: {env_str}[/yellow]")
    return grader_env


def _apply_course_runtime_storage_env(settings: Settings, *, console: Console) -> None:
    """Mirror ambient RUSTFS_* credentials into AWS_* for shared-environment courses."""
    if settings.assets.storage_auth_mode != "shared_environment":
        return
    if seed_ambient_storage_env(os.environ):
        console.print("[blue]Mirrored RUSTFS_* credentials into AWS_* for this run[/blue]")


def _resolve_course_run_download_dir(download_dir: Path | None, *, console: Console) -> Path:
    if download_dir is not None:
        return download_dir
    resolved = Path(tempfile.mkdtemp(prefix="ccc-download-"))
    console.print(f"[yellow]Using temporary download directory: {resolved}[/yellow]")
    return resolved


def _print_flow_result(result: FlowArtifacts, *, console: Console) -> None:
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
    console: Console,
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
    console: Console,
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


def _resolve_docker_image(docker_image: str, *, interactive: bool, console: Console, Prompt) -> str:
    if not interactive:
        return docker_image
    return Prompt.ask("Docker image for grading", default=docker_image)


def _build_course_setup_config(
    selected_course_id: int,
    course: Course,
    options: CourseSetupOptions,
    *,
    console: Console,
    Prompt,
    Confirm,
) -> CourseSetupConfig:
    course_slug = _suggest_course_slug(selected_course_id, course)
    mappings = _collect_work_package_mappings(
        course,
        options.work_packages,
        interactive=options.interactive,
        console=console,
        Confirm=Confirm,
        Prompt=Prompt,
    )

    return CourseSetupConfig(
        block_name=f"ccc-course-{course_slug}",
        canvas_api_url=options.canvas_api_url or CANVAS_API_URL_DEFAULT,
        canvas_token=options.canvas_token or "",
        selected_course_id=selected_course_id,
        assets_block=f"ccc-assets-{course_slug}",
        assets_prefix=f"graders/{course_slug}/",
        work_pool=f"course-work-pool-{course_slug}",
        docker_image=_resolve_docker_image(
            options.docker_image,
            interactive=options.interactive,
            console=console,
            Prompt=Prompt,
        ),
        work_package_plans=_build_work_package_plans(mappings, console=console),
        grader_env=_build_grader_env(options.env_var, console=console),
    )


def _print_course_setup_summary(config: CourseSetupConfig, *, console: Console) -> None:
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
    summary_table.add_row("Work Packages", str(len(config.work_package_plans)))
    console.print(summary_table)

    if not config.work_package_plans:
        return

    upload_table = Table(title="Work-package uploads")
    upload_table.add_column("Assignment", style="cyan")
    upload_table.add_column("Source", style="green")
    upload_table.add_column("Asset Prefix", style="yellow")
    for plan in config.work_package_plans:
        upload_table.add_row(str(plan.assignment_id), str(plan.asset_source_dir), plan.prefix)
    console.print(upload_table)


def _build_course_block_payload(config: CourseSetupConfig) -> CourseConfigBlockPayload:
    return {
        "canvas_api_url": HttpUrl(config.canvas_api_url),
        "canvas_token": SecretStr(config.canvas_token),
        "canvas_course_id": config.selected_course_id,
        "asset_bucket_block": config.assets_block,
        "asset_path_prefix": config.assets_prefix,
        "assignment_asset_prefixes": {
            plan.assignment_id: plan.prefix for plan in config.work_package_plans
        },
        "storage_auth_mode": "shared_environment",
        "grader_image": config.docker_image,
        "work_pool_name": config.work_pool,
        "grader_env": config.grader_env,
    }


def _ensure_course_block_absent(block_name: str, *, console: Console, CourseConfigBlock) -> None:
    """Fail before any S3 or manifest mutation if the course block already exists.

    Queries the block document directly rather than going through ``Block.load``:
    only a genuine miss raises ``ObjectNotFound``, so a missing API URL, an auth
    failure, or a schema-drifted block propagates instead of reading as "absent"
    and letting setup mutate S3 and the user's manifests first.
    """
    with get_client(sync_client=True) as client:
        try:
            client.read_block_document_by_name(
                name=block_name,
                block_type_slug=CourseConfigBlock.get_block_type_slug(),
                include_secrets=False,  # an existence check has no business fetching the token
            )
        except ObjectNotFound:
            return

    console.print(f"[red]Course configuration block already exists: {block_name}[/red]")
    console.print(
        f"[dim]Delete it first with: prefect block delete "
        f"{CourseConfigBlock.get_block_type_slug()}/{block_name}[/dim]"
    )
    raise typer.Exit(1)


def _save_course_block(config: CourseSetupConfig, *, console: Console, CourseConfigBlock) -> None:
    try:
        block = CourseConfigBlock(**_build_course_block_payload(config))
        block.save(config.block_name, overwrite=False)
    except (RuntimeError, TypeError, ValueError) as exc:
        console.print(f"[red]Error saving course block: {exc}[/red]")
        raise typer.Exit(1) from exc

    console.print(f"\n[green]✓ Course configuration saved as block: {config.block_name}[/green]")
    console.print(
        f"[blue]You can now use: ccc course run <assignment_id> --course {config.block_name}[/blue]"
    )


def course_run_command(
    assignment_id: int,
    options: CourseRunOptions,
    *,
    console: Console,
    load_settings_from_course_block,
    build_canvas_resources,
    correct_submission_flow,
    CorrectSubmissionPayload,
) -> None:
    settings = _run_cli_step(
        console,
        "Error loading course block",
        lambda: load_settings_from_course_block(options.course_block),
    )
    _apply_course_runtime_storage_env(settings, console=console)
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
    options: CourseSetupOptions,
    *,
    console: Console,
    Canvas,
    CourseConfigBlock,
    Prompt,
    IntPrompt,
    Confirm,
) -> None:
    console.print(Panel.fit("[bold blue]Canvas Code Correction - Course Setup[/bold blue]"))

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
        replace(options, canvas_api_url=canvas_api_url, canvas_token=canvas_credential),
        console=console,
        Prompt=Prompt,
        Confirm=Confirm,
    )
    _print_course_setup_summary(setup_config, console=console)

    if options.interactive and not Confirm.ask("\nSave this configuration?", default=True):
        console.print("[yellow]Configuration cancelled[/yellow]")
        raise typer.Exit(0)

    _run_cli_step(
        console,
        "Error checking for an existing course block",
        lambda: _ensure_course_block_absent(
            setup_config.block_name, console=console, CourseConfigBlock=CourseConfigBlock
        ),
    )
    _sync_work_package_manifests(setup_config.work_package_plans, console=console)
    _provision_course_assets(setup_config, console=console)
    _save_course_block(config=setup_config, console=console, CourseConfigBlock=CourseConfigBlock)


def course_list_command(
    *, console: Console, _run_cli_step=_run_cli_step, find_course_block_names, load_course_block
) -> None:
    blocks = _run_cli_step(console, "Error listing courses", find_course_block_names)
    if not blocks:
        console.print("[yellow]No course configuration blocks found[/yellow]")
        return

    table = Table(title="Configured Courses")
    table.add_column("Block Name", style="cyan", no_wrap=True)
    table.add_column("Canvas Course ID", style="green")
    table.add_column("Docker Image", style="yellow")
    table.add_column("Assets Block", style="blue", no_wrap=True)
    table.add_column("Storage Auth", style="magenta")

    for block_slug in blocks:
        try:
            block = load_course_block(block_slug)
            table.add_row(
                block_slug,
                str(block.canvas_course_id),
                block.grader_image or "Not set",
                block.asset_bucket_block,
                block.storage_auth_mode,
            )
        except COURSE_BLOCK_LOAD_EXCEPTIONS as exc:
            table.add_row(block_slug, f"Error: {exc}", "", "", "")

    console.print(table)
