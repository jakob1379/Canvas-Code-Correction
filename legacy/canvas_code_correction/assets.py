"""Utilities for managing Prefect assets representing course grader resources."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prefect import get_run_logger
from prefect.client.orchestration import PrefectClient
from prefect.utilities.asyncutils import run_sync_in_worker_thread

try:  # pragma: no cover - optional dependency guard
    from prefect_aws.s3 import S3Bucket
except Exception:  # pragma: no cover - optional dependency guard
    S3Bucket = None  # type: ignore[assignment]


@dataclass
class CourseAssetMaterialization:
    asset_key: str
    materialization_id: str
    manifest: dict[str, Any]


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def _build_manifest(slugged: str, course_id: int, root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for file_path in _iter_files(root):
        relative = file_path.relative_to(root).as_posix()
        parts = relative.split("/", 1)
        assignment_id = parts[0] if len(parts) == 2 else "default"
        checksum = hashlib.sha256(file_path.read_bytes()).hexdigest()
        files.append(
            {
                "assignment_id": assignment_id,
                "path": relative,
                "checksum": checksum,
                "size": file_path.stat().st_size,
            }
        )
    base_prefix = f"{slugged}-{course_id}"
    manifest = {
        "base_prefix": base_prefix,
        "files": files,
    }
    return manifest


async def materialize_course_assets(
    client: PrefectClient,
    *,
    slugged: str,
    course_id: int,
    local_path: Path,
    bucket_block: str,
    overwrite: bool,
) -> CourseAssetMaterialization:
    logger = get_run_logger()
    root = local_path.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Assets path must be a directory: {root}")

    manifest = await run_sync_in_worker_thread(_build_manifest, slugged, course_id, root)
    if S3Bucket is None:  # pragma: no cover - defensive
        raise RuntimeError("prefect-aws must be installed to materialize assets")

    bucket = await S3Bucket.load(bucket_block)
    base_prefix = manifest["base_prefix"]
    if overwrite:
        for obj in bucket._get_bucket_resource().objects.filter(
            Prefix=base_prefix
        ):  # pragma: no cover
            obj.delete()
    for file_entry in manifest["files"]:
        local_file = root / file_entry["path"]
        key = f"{base_prefix}/{file_entry['path']}"
        bucket.write_path(key, local_file.read_bytes())

    asset_key = f"canvas-code-correction/assets/{slugged}"
    materialization_id = hashlib.sha256(str(manifest).encode()).hexdigest()
    logger.info(
        "Materialized course assets",
        extra={
            "asset_key": asset_key,
            "materialization_id": materialization_id,
            "file_count": len(manifest["files"]),
        },
    )
    return CourseAssetMaterialization(
        asset_key=asset_key,
        materialization_id=materialization_id,
        manifest=manifest,
    )


async def resolve_course_assets(
    client: PrefectClient,
    *,
    materialization: CourseAssetMaterialization,
    destination: Path,
) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    return destination
