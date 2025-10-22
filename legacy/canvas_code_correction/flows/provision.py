"""Flows for provisioning and maintaining course configuration metadata."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from prefect import flow, get_run_logger, task
from prefect.client.orchestration import PrefectClient
from prefect.exceptions import MissingContextError
from prefect.utilities.slugify import slugify

from ..assets import CourseAssetMaterialization, materialize_course_assets
from ..config import CourseAssets, CourseConfig, RunnerSettings
from ..prefect_utils import ensure_work_pool, load_course_config, save_course_config


@task
def slugify_course(course_slug: str) -> str:
    return slugify(course_slug)


@task
async def ensure_work_pool_task(
    slugged: str,
    pool_type: str,
    overwrite: bool,
    description: str | None = None,
    base_job_template: dict[str, Any] | None = None,
) -> str:
    async with PrefectClient() as client:
        await ensure_work_pool(
            client,
            name=f"course-work-pool-{slugged}",
            pool_type=pool_type,
            description=description,
            base_job_template=base_job_template,
            overwrite=overwrite,
        )
    return f"course-work-pool-{slugged}"


@task
async def materialize_assets_task(
    slugged: str,
    course_id: int,
    assets_path: Path,
    bucket_block: str,
    overwrite: bool,
) -> CourseAssetMaterialization:
    async with PrefectClient() as client:
        return await materialize_course_assets(
            client,
            slugged=slugged,
            course_id=course_id,
            local_path=assets_path,
            bucket_block=bucket_block,
            overwrite=overwrite,
        )


@task
async def persist_course_config_task(
    slugged: str,
    config: CourseConfig,
    overwrite: bool,
) -> CourseConfig:
    block_name = f"course-config-{slugged}"
    async with PrefectClient() as client:
        await save_course_config(client, block_name, config, overwrite=overwrite)
    return config


@task
async def update_course_assets_task(
    slugged: str,
    materialization: CourseAssetMaterialization,
) -> CourseConfig:
    block_name = f"course-config-{slugged}"
    async with PrefectClient() as client:
        existing = await load_course_config(client, block_name)
        updated = existing.model_copy(
            update={
                "assets": CourseAssets(
                    asset_key=materialization.asset_key,
                    materialization_id=materialization.materialization_id,
                    manifest=materialization.manifest,
                )
            }
        )
        await save_course_config(client, block_name, updated, overwrite=True)
        return updated


def _sync_run_logger() -> logging.Logger:
    try:
        return get_run_logger()
    except MissingContextError:
        logger = logging.getLogger("canvas_code_correction.flows.provision")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger


@flow
def provision_course_flow(
    course_slug: str,
    course_id: int,
    docker_image: str,
    assets_path: str,
    bucket_block: str,
    pool_type: str = "docker",
    overwrite: bool = False,
    network_disabled: bool = True,
    memory_limit: str = "1g",
    cpu_limit: float = 1.0,
    gpu_enabled: bool = False,
    runner_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    logger = _sync_run_logger()
    slugged_future = slugify_course.submit(course_slug)
    work_pool_future = ensure_work_pool_task.submit(
        slugged_future,
        pool_type=pool_type,
        overwrite=overwrite,
    )

    materialization_future = materialize_assets_task.submit(
        slugged_future,
        course_id,
        Path(assets_path),
        bucket_block,
        overwrite,
    )

    slugged = slugged_future.result()
    work_pool = work_pool_future.result()
    materialization = materialization_future.result()

    runner = RunnerSettings(
        docker_image=docker_image,
        network_disabled=network_disabled,
        memory_limit=memory_limit,
        cpu_limit=cpu_limit,
        gpu_enabled=gpu_enabled,
        env=runner_env or {},
    )
    course_assets = CourseAssets(
        asset_key=materialization.asset_key,
        materialization_id=materialization.materialization_id,
        manifest=materialization.manifest,
    )
    config = CourseConfig(
        course_slug=slugged,
        work_pool=work_pool,
        runner=runner,
        assets=course_assets,
    )

    persist_course_config_task.submit(slugged, config, overwrite).result()
    logger.info(
        "Provisioned course",
        extra={
            "slug": slugged,
            "work_pool": work_pool,
            "config_block": f"course-config-{slugged}",
            "asset_key": course_assets.asset_key,
            "materialization_id": course_assets.materialization_id,
        },
    )
    return {
        "slug": slugged,
        "work_pool": work_pool,
        "config_block": f"course-config-{slugged}",
        "asset_key": course_assets.asset_key,
        "materialization_id": course_assets.materialization_id,
    }


@flow
def refresh_course_assets_flow(
    course_name: str,
    course_id: int,
    assets_path: str,
    bucket_block: str,
) -> dict[str, Any]:
    slugged_future = slugify_course.submit(course_name)
    materialization_future = materialize_assets_task.submit(
        slugged_future,
        course_id,
        Path(assets_path),
        bucket_block,
        overwrite=True,
    )
    updated_config_future = update_course_assets_task.submit(slugged_future, materialization_future)
    slugged = slugged_future.result()
    updated_config = updated_config_future.result()
    return {
        "slug": slugged,
        "config_block": f"course-config-{slugged}",
        "asset_key": updated_config.assets.asset_key,
        "materialization_id": updated_config.assets.materialization_id,
    }
