"""Command-line interface for Canvas Code Correction v2."""

from pathlib import Path

import typer

from .config import Settings
from .flows.correct_submission import correct_submission_flow

try:  # pragma: no cover - imported lazily in tests
    from prefect.blocks.system import JSON
except Exception:  # pragma: no cover - Prefect may not be available during static analysis
    JSON = None

app = typer.Typer(help="Canvas Code Correction orchestration utilities.")

CONFIG_PATH_OPTION = typer.Option(
    None,
    "--config",
    help="Path to a TOML or ENV configuration file overriding defaults.",
    exists=True,
    file_okay=True,
    dir_okay=False,
)

GRADER_ENV_OPTION = typer.Option(
    None,
    "--env",
    "-e",
    help="Environment assignment for the grader in KEY=VALUE form (repeatable).",
)


@app.callback()
def load_settings(
    ctx: typer.Context,
    config_path: Path | None = CONFIG_PATH_OPTION,
) -> None:
    """Load shared configuration before executing commands."""

    if config_path is not None:
        config_path = config_path.expanduser()
        if not config_path.exists():
            raise typer.BadParameter(f"Configuration file not found: {config_path}")
        if not config_path.is_file():
            raise typer.BadParameter(f"Configuration path must be a file: {config_path}")
        settings = Settings.from_file(config_path)
    else:
        settings = Settings.from_env()
    ctx.obj = settings


@app.command()
def run_once(
    ctx: typer.Context,
    assignment_id: int = typer.Argument(..., help="Canvas assignment identifier."),
    submission_id: int = typer.Argument(..., help="Canvas submission identifier."),
) -> None:
    """Execute the correction flow once for a specific submission."""

    if ctx.obj is None:
        raise typer.BadParameter("Settings failed to load")
    settings: Settings = ctx.obj
    correct_submission_flow.with_options(name="correct-submission")(
        assignment_id=assignment_id,
        submission_id=submission_id,
        settings=settings,
    )


@app.command("configure-grader")
def configure_grader_block(
    course: str = typer.Argument(..., help="Course identifier used to name the block."),
    docker_image: str = typer.Option(..., "--docker-image", "-i", help="Grader Docker image"),
    block_name: str | None = typer.Option(
        None,
        "--block-name",
        help="Override the Prefect block name.",
    ),
    network_disabled: bool = typer.Option(
        True,
        "--network-disabled/--network-enabled",
        help="Disable container networking by default.",
    ),
    memory_limit: str = typer.Option("1g", "--memory-limit", help="Docker memory limit (e.g. 1g)."),
    cpu_limit: float = typer.Option(
        1.0, "--cpu-limit", help="CPU shares/limit for the grader container."
    ),
    gpu_enabled: bool = typer.Option(
        False,
        "--gpu-enabled/--gpu-disabled",
        help="Allow grader containers to access GPU devices.",
    ),
    env: list[str] | None = GRADER_ENV_OPTION,
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing Prefect block."),
) -> None:
    """Create or update a Prefect JSON block for course-specific grader settings."""

    if JSON is None:  # pragma: no cover - Prefect import guard
        raise typer.BadParameter("Prefect must be installed to manage grader configuration blocks")

    block_id = block_name or f"grader-config/{course}"

    env_map: dict[str, str] = {}
    for item in env or []:
        if "=" not in item:
            raise typer.BadParameter("Environment variables must be in KEY=VALUE format")
        key, value = item.split("=", 1)
        env_map[key] = value

    payload = {
        "docker_image": docker_image,
        "network_disabled": network_disabled,
        "memory_limit": memory_limit,
        "cpu_limit": cpu_limit,
        "gpu_enabled": gpu_enabled,
        "env": env_map,
    }

    JSON(value=payload).save(block_id, overwrite=overwrite)
    typer.echo(f"Saved grader configuration block '{block_id}'")
