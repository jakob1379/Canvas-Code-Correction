"""Command-line interface for Canvas Code Correction v2."""

from pathlib import Path

import typer

from .config import Settings
from .flows.correct_submission import correct_submission_flow

app = typer.Typer(help="Canvas Code Correction orchestration utilities.")


@app.callback()
def load_settings(
    ctx: typer.Context,
    config_path: Path | None = typer.Option(
        None,
        "--config",
        help="Path to a TOML or ENV configuration file overriding defaults.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
) -> None:
    """Load shared configuration before executing commands."""

    settings = Settings.from_file(config_path) if config_path is not None else Settings.from_env()
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
