# Grader Image Guide

The grader container executes student submissions in an isolated environment.
Build the image using the provided Dockerfile:

```bash
docker build \
  -t ghcr.io/your-org/canvas-grader:latest \
  -f containers/grader/Dockerfiledocker .
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

Register the grader configuration so the orchestrator uses the image:

```bash
uv run ccc configure-grader <course-slug> --docker-image <registry>/grader:latest
```

!!! tip "Override runtime command"

    Pass `--env` flags to supply additional environment variables if you
    need to modify the container command or pass configuration knobs to your
    grading script.

## Validating the Setup

Trigger a dry run for a single submission to validate the setup:

    ```bash
    uv run ccc run-once <assignment-id> <submission-id>
    ```

`run-once` downloads the submission, mounts it at `/workspace/submission`, runs
the container, and collects the outputs. Review the returned points and comments
to iterate on your grading logic.
