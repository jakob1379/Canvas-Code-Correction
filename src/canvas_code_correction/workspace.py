"""Utilities for preparing per-run workspaces for grading."""

from __future__ import annotations

import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from prefect_aws.s3 import S3Bucket

if TYPE_CHECKING:
    from pathlib import Path

    from canvas_code_correction.config import Settings


@dataclass(frozen=True)
class WorkspacePaths:
    """Locations prepared for a grading run."""

    root: Path
    submission_dir: Path
    assets_dir: Path


@dataclass(frozen=True)
class WorkspaceConfig:
    """Configuration for a grading workspace."""

    workspace_root: Path
    bucket_block: str
    path_prefix: str
    assignment_id: int
    submission_id: int
    run_id: str | None = None


def _ensure_safe_directory(path: Path, mode: int = 0o700) -> None:
    """Ensure directory exists with safe permissions.

    Creates missing parent directories with the same safe mode.
    Raises RuntimeError if path is a symlink or world-writable.
    """
    if path.exists():
        st = path.stat()
        if stat.S_ISLNK(st.st_mode):
            msg = f"Directory {path} is a symlink"
            raise RuntimeError(msg)
        if st.st_mode & stat.S_IWOTH:
            msg = f"Directory {path} is world-writable"
            raise RuntimeError(msg)
        # Directory exists and is safe
        return

    # Find the deepest existing ancestor
    parents = []
    current = path
    while not current.exists():
        parents.append(current)
        current = current.parent
        # Safety: avoid infinite loop (should not happen as root exists)
        if current == current.parent:  # reached root
            break

    # Ensure existing ancestor is not a symlink
    if current.exists():
        st = current.stat()
        if stat.S_ISLNK(st.st_mode):
            msg = f"Parent directory {current} is a symlink"
            raise RuntimeError(msg)

    # Create missing directories in reverse order (deepest to shallowest)
    for missing in reversed(parents):
        missing.mkdir(mode=mode)


def prepare_workspace(
    config: WorkspaceConfig,
    submission_files: list[Path],
) -> WorkspacePaths:
    """Create a workspace for a grading run and populate it with required files."""
    run_identifier = config.run_id or uuid4().hex
    workspace_root = (
        config.workspace_root
        / f"assignment-{config.assignment_id}"
        / f"submission-{config.assignment_id}-{config.submission_id}-{run_identifier}"
    )
    _ensure_safe_directory(workspace_root)

    submission_dir = workspace_root / "submission"
    assets_dir = workspace_root / "assets"

    _ensure_safe_directory(submission_dir)
    _ensure_safe_directory(assets_dir)

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
        msg = "S3Bucket block missing download method"
        raise AttributeError(msg)

    return WorkspacePaths(
        root=workspace_root,
        submission_dir=submission_dir,
        assets_dir=assets_dir,
    )


def build_workspace_config(
    settings: Settings,
    *,
    assignment_id: int,
    submission_id: int,
) -> WorkspaceConfig:
    """Construct :class:`WorkspaceConfig` from application settings."""
    return WorkspaceConfig(
        workspace_root=settings.workspace.root,
        bucket_block=settings.assets.bucket_block,
        path_prefix=settings.assets.path_prefix,
        assignment_id=assignment_id,
        submission_id=submission_id,
    )
