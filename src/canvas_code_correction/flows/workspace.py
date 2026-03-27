"""Utilities for preparing per-run workspaces for grading."""

import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from prefect_aws.s3 import S3Bucket


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
        _validate_directory(path)
        return

    base = _existing_ancestor(path)
    _validate_directory(base)

    for parent in reversed(_missing_parent_directories(path, base)):
        parent.mkdir(mode=mode)


def _existing_ancestor(path: Path) -> Path:
    current = path
    while not current.exists():
        current_parent = current.parent
        if current_parent == current:
            msg = f"Could not resolve existing ancestor for {path}"
            raise RuntimeError(msg)
        current = current_parent
    return current


def _missing_parent_directories(path: Path, existing_ancestor: Path) -> list[Path]:
    missing: list[Path] = []
    current = path
    while current != existing_ancestor:
        missing.append(current)
        current = current.parent
    return missing


def _validate_directory(path: Path) -> None:
    if path.is_symlink():
        msg = f"Directory {path} is a symlink"
        raise RuntimeError(msg)

    if path.stat().st_mode & stat.S_IWOTH:
        msg = f"Directory {path} is world-writable"
        raise RuntimeError(msg)


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

    download_folder = getattr(bucket, "download_folder", None)
    if callable(download_folder):
        download_folder(local_path=str(assets_dir), **download_kwargs)

    else:
        get_directory = getattr(bucket, "get_directory", None)
        if callable(get_directory):
            get_directory(local_path=str(assets_dir), **download_kwargs)
        else:  # pragma: no cover - defensive fallback
            msg = "S3Bucket block missing download method"
            raise TypeError(msg)

    return WorkspacePaths(
        root=workspace_root,
        submission_dir=submission_dir,
        assets_dir=assets_dir,
    )
