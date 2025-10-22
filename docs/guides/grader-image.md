# Grader Image Guide

The grader container executes student submissions in an isolated environment.
Build the image using the provided Dockerfile:

```bash
docker build \
  -t jakob1379/canvas-grader:latest \
  -f containers/grader/Dockerfile .
```

Key hardening steps:

- Runs as a non-root user (`app`, UID/GID configurable via build args).
- Installs dependencies with `uv sync --frozen --group tests` to mirror project
  tooling.
- Uses an `ENTRYPOINT` that executes your grading harness within the container
  (for example a script shipped alongside the image or mounted at runtime).

When running under Prefect, pass volume mounts for submission workspaces and set
environment variables (`CCC_RESULTS_FILE`, `CCC_POINTS_FILE`, etc.) to align
with your grading contract.

## Packaging Course-Specific Graders

Course configuration should not require modifying the CCC source tree. Instead,
ship grader code and test assets with your Docker image (or mount them read-only
at runtime) while keeping CCC itself immutable.

Two common approaches:

1. **General-purpose base image.** Start from a lightweight Ubuntu (or
   equivalent) image, install the language runtimes and dependencies required by
   your grader, and copy your test harness into the image under `/opt/grader` or
   a similar path.
2. **Course-specialized image.** Fork the base image and bake in course-specific
   tooling or third-party binaries. When sensitive test assets should not be
   bundled into the image, mount them read/executable-only via Prefect worker
   volume configuration so the grader can read but not mutate the files.

In both cases the container should expose the grader entry script via
`ENTRYPOINT` (or `CMD`) so Prefect can invoke it directly. The script is
responsible for reading submission files from `/workspace/submission` and
writing results (`results.json`, `points.txt`, `comments.txt`) back to the
workspace.

## Building and Publishing

Once your Dockerfile packages the grader harness and any required test assets,
build and optionally push the image:

```bash
docker build -t <registry>/grader:latest containers/grader
docker push <registry>/grader:latest  # optional but recommended
```

## Configure CCC to Use the Image

Provision the course through the Prefect flow/deployment instead of the former
CLI. The provisioning flow will:

1. Create (or overwrite) the course work pool.
2. Upload the grader asset folder to S3 via the configured Prefect S3 block.
3. Persist a `course-config-<course_name>` JSON block referencing the Docker
   image and latest asset materialization.

Example Python snippet using the provisioning flow directly:

```python
from pathlib import Path

from canvas_code_correction.flows.provision import provision_course_flow

provision_course_flow(
    course_name="my-course",
    course_id=42,
    docker_image="jakob1379/canvas-grader:latest",
    assets_path=str(Path("grader-assets")),
    bucket_block="course-assets-my-course",
)
```

Alternatively, build and apply the provided deployment script under
`canvas_code_correction/deployments/provision.py` so operators can trigger
provisioning from Prefect Cloud/UI.

## Validating the Setup

Once provisioning completes and the correction deployment is active, trigger a
test run via Prefect (UI, CLI, or API). The correction flow downloads the course
assets materialization into the grader container and executes the command
defined in the course configuration.
