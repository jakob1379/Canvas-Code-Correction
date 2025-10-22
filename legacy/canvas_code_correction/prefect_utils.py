"""Prefect helper utilities for configuring course-level resources."""

from __future__ import annotations

from typing import Any

from prefect.client.orchestration import PrefectClient
from prefect.client.schemas.actions import BlockDocumentCreate, WorkPoolCreate
from prefect.client.schemas.objects import BlockDocument

from .config import CourseConfig


async def ensure_work_pool(
    client: PrefectClient,
    name: str,
    pool_type: str = "docker",
    description: str | None = None,
    base_job_template: dict[str, Any] | None = None,
    overwrite: bool = False,
) -> Any:
    """Create or update a worker/work pool and return its metadata."""

    if hasattr(client, "read_work_pools"):
        pools = await client.read_work_pools()
        existing = next((pool for pool in pools if getattr(pool, "name", None) == name), None)
        if existing and not overwrite:
            return existing
        if existing:
            existing_id = getattr(existing, "id", None)
            if existing_id is not None:
                await client.delete_work_pool(existing_id)
        payload = {
            "name": name,
            "type": pool_type,
            "description": description,
            "base_job_template": base_job_template,
        }
        model_payload = {key: value for key, value in payload.items() if value is not None}
        create_model = WorkPoolCreate(**model_payload)
        return await client.create_work_pool(create_model, overwrite=overwrite)

    if hasattr(client, "read_worker_pools"):
        pools = await client.read_worker_pools()
        existing = next((pool for pool in pools if getattr(pool, "name", None) == name), None)
        if existing and not overwrite:
            return existing
        if existing:
            existing_id = getattr(existing, "id", None)
            if existing_id is not None:
                await client.delete_worker_pool(existing_id)
        payload = {
            "name": name,
            "type": pool_type,
            "description": description,
        }
        if base_job_template is not None:
            payload["base_job_template"] = base_job_template
        return await client.create_worker_pool(**payload)

    raise RuntimeError("Prefect client missing work pool management methods")


async def save_course_config(
    client: PrefectClient,
    block_name: str,
    config: CourseConfig,
    overwrite: bool = False,
) -> BlockDocument:
    """Persist course configuration metadata to a Prefect JSON block."""

    block_type = await client.read_block_type_by_slug("system/json")
    block_schema_id = await _resolve_block_schema_id(client, block_type.id)
    existing = await _get_block_by_name(client, block_name)
    payload = config.model_dump(mode="json")
    if existing and overwrite:
        await client.delete_block_document(existing.id)
        existing = None
    if existing:
        return existing
    created = await client.create_block_document(
        BlockDocumentCreate(
            name=block_name,
            block_type_id=block_type.id,
            block_schema_id=block_schema_id,
            data=payload,
        )
    )
    return created


async def load_course_config(client: PrefectClient, block_name: str) -> CourseConfig:
    """Load course configuration from a Prefect JSON block."""

    document = await _require_block_by_name(client, block_name)
    if not isinstance(document.data, dict):
        raise RuntimeError(f"Block '{block_name}' does not contain a mapping")
    return CourseConfig.model_validate(document.data)


async def _get_block_by_name(client: PrefectClient, name: str) -> BlockDocument | None:
    blocks = await client.read_block_documents(name_like=name)
    for block in blocks:
        if block.name == name:
            return block
    return None


async def _require_block_by_name(client: PrefectClient, name: str) -> BlockDocument:
    document = await _get_block_by_name(client, name)
    if document is None:
        raise RuntimeError(f"Prefect block '{name}' not found")
    return document


async def _resolve_block_schema_id(client: PrefectClient, block_type_id: str) -> str:
    read = getattr(client, "read_block_schemas", None)
    if read is None:
        raise RuntimeError("Prefect client missing read_block_schemas method")
    schemas = await read(block_type_id=block_type_id)
    for schema in schemas:
        schema_id = getattr(schema, "id", None)
        if schema_id:
            return schema_id
        if isinstance(schema, dict):
            schema_id = schema.get("id")
            if schema_id:
                return schema_id
    raise RuntimeError(f"No block schema found for block type {block_type_id}")
