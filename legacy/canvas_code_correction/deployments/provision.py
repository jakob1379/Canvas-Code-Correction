"""Deployment script for the course provisioning flow."""

from __future__ import annotations

from pathlib import Path

from prefect.deployments import Deployment

from ..flows.provision import provision_course_flow


def build_deployment(
    *,
    name: str,
    course_slug: str,
    course_id: int,
    docker_image: str,
    assets_path: Path,
    bucket_block: str,
    work_pool_name: str | None = None,
) -> Deployment:
    parameters = {
        "course_slug": course_slug,
        "course_id": course_id,
        "docker_image": docker_image,
        "assets_path": str(assets_path),
        "bucket_block": bucket_block,
        "pool_type": "docker",
    }
    deployment = Deployment.build_from_flow(
        flow=provision_course_flow,
        name=name,
        parameters=parameters,
        work_pool_name=work_pool_name,
    )
    return deployment


def main() -> None:  # pragma: no cover - script entrypoint
    deployment = build_deployment(
        name="provision-course-sample",
        course_slug="sample-course",
        course_id=0,
        docker_image="ghcr.io/example/grader:latest",
        assets_path=Path("/path/to/assets"),
        bucket_block="course-assets-bucket",
    )
    deployment.apply()


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()
