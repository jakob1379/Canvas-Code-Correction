from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

import boto3
import requests
import typer
from botocore.exceptions import BotoCoreError, EndpointConnectionError


DEFAULT_PREFECT_HEALTH_URL = "http://localhost:4200/api/health"
DEFAULT_RUSTFS_ENDPOINT = "http://localhost:9000"


@dataclass(frozen=True)
class SystemStatusConfig:
    requests_module: Any
    boto3_module: Any
    os_module: Any
    http_status: Any
    prefect_health_url: str = DEFAULT_PREFECT_HEALTH_URL
    rustfs_endpoint_default: str = DEFAULT_RUSTFS_ENDPOINT


def _run_cli_step(console, step: str, action):
    try:
        return action()
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]{step}: {exc}[/red]")
        raise typer.Exit(1) from exc


def webhook_serve_command(
    *, console, host: str, port: int, uvicorn_run, webhook_fastapi_app
) -> None:
    console.print(f"[blue]Starting webhook server on {host}:{port}[/blue]")
    uvicorn_run(webhook_fastapi_app, host=host, port=port)


def deploy_create_command(
    *,
    console,
    course_block: str,
    load_settings_from_course_block,
    ensure_deployment,
    asyncio_module=asyncio,
) -> None:
    settings = _run_cli_step(
        console, "Error loading course block", lambda: load_settings_from_course_block(course_block)
    )
    console.print(f"[blue]Creating deployment for course block: {course_block}[/blue]")
    deployment_result = _run_cli_step(
        console,
        "Error creating deployment",
        lambda: asyncio_module.run(ensure_deployment(settings, course_block)),
    )
    if not deployment_result.ensured:
        console.print(
            "[red]Error creating deployment: "
            f"{deployment_result.error_type or 'Error'}: "
            f"{deployment_result.error or 'unknown error'}[/red]",
        )
        raise typer.Exit(1)
    console.print(
        f"[green]Deployment '{deployment_result.deployment_name}' created/updated successfully[/green]"
    )
    console.print(
        f"[yellow]Note: Ensure work pool '{settings.grader.work_pool_name or 'local-pool'}' exists and has workers[/yellow]"
    )


def system_status_command(
    *,
    console,
    config: SystemStatusConfig,
) -> None:
    console.print("[bold blue]Platform Status[/bold blue]")

    try:
        response = config.requests_module.get(config.prefect_health_url, timeout=5)
    except config.requests_module.RequestException as exc:
        console.print(f"[red]✗ Prefect server: Not reachable ({exc})[/red]")
    else:
        if response.status_code == config.http_status.OK:
            console.print("[green]✓ Prefect server: Running[/green]")
        else:
            console.print(f"[yellow]⚠ Prefect server: HTTP {response.status_code}[/yellow]")

    rustfs_endpoint = config.os_module.environ.get(
        "RUSTFS_ENDPOINT",
        config.rustfs_endpoint_default,
    )
    rustfs_access_key = config.os_module.environ.get("RUSTFS_ACCESS_KEY")
    rustfs_secret_key = config.os_module.environ.get("RUSTFS_SECRET_KEY")

    if not rustfs_access_key or not rustfs_secret_key:
        console.print(
            "[yellow]⚠ RustFS (S3): Credentials missing (set RUSTFS_ACCESS_KEY/RUSTFS_SECRET_KEY)[/yellow]"
        )
    else:
        try:
            s3 = config.boto3_module.client(
                "s3",
                endpoint_url=rustfs_endpoint,
                aws_access_key_id=rustfs_access_key,
                aws_secret_access_key=rustfs_secret_key,
            )
            s3.list_buckets()
        except EndpointConnectionError:
            console.print("[red]✗ RustFS (S3): Not reachable[/red]")
        except BotoCoreError as exc:
            console.print(f"[yellow]⚠ RustFS (S3): Error ({exc})[/yellow]")
        else:
            console.print("[green]✓ RustFS (S3): Running[/green]")

    console.print("\n[dim]Use 'ccc course list' to see saved courses[/dim]")
