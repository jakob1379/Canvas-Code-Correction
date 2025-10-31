"""Utilities for preparing per-run workspaces for grading."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from prefect_aws.s3 import S3Bucket

from canvas_code_correction.config import Settings


@dataclass(frozen=True)
class WorkspacePaths:
    """Locations prepared for a grading run."""

    root: Path
    submission_dir: Path
    assets_dir: Path


@dataclass(frozen=True)
class WorkspaceConfig:
    workspace_root: Path
    bucket_block: str
    path_prefix: str
    assignment_id: int
    submission_id: int
    run_id: str | None = None


def prepare_workspace(config: WorkspaceConfig, submission_files: list[Path]) -> WorkspacePaths:
    """Create a workspace for a grading run and populate it with required files."""

    run_identifier = config.run_id or uuid4().hex
    workspace_root = (
        config.workspace_root
        / f"assignment-{config.assignment_id}"
        / f"submission-{config.assignment_id}-{config.submission_id}-{run_identifier}"
    )

    submission_dir = workspace_root / "submission"
    assets_dir = workspace_root / "assets"

    submission_dir.mkdir(parents=True, exist_ok=False)
    assets_dir.mkdir(parents=True, exist_ok=False)

    for file_path in submission_files:
        if not file_path.exists():
            continue
        destination = submission_dir / file_path.name
        shutil.copy2(file_path, destination)

    bucket = S3Bucket.load(config.bucket_block)
    prefix = config.path_prefix.strip("/") if config.path_prefix else ""

    download_kwargs: dict[str, str] = {}
    if prefix:
        download_kwargs["from_path"] = prefix

    if hasattr(bucket, "download_folder"):
        bucket.download_folder(local_path=str(assets_dir), **download_kwargs)
    elif hasattr(bucket, "get_directory"):
        bucket.get_directory(local_path=str(assets_dir), **download_kwargs)
    else:  # pragma: no cover - defensive fallback
        raise AttributeError("S3Bucket block missing download method")

    return WorkspacePaths(root=workspace_root, submission_dir=submission_dir, assets_dir=assets_dir)


def build_workspace_config(
    settings: Settings, *, assignment_id: int, submission_id: int
) -> WorkspaceConfig:
    """Construct :class:`WorkspaceConfig` from application settings."""

    return WorkspaceConfig(
        workspace_root=settings.workspace.root,
        bucket_block=settings.assets.bucket_block,
        path_prefix=settings.assets.path_prefix,
        assignment_id=assignment_id,
        submission_id=submission_id,
    )
