# Grader Image Guide

The grader container executes student submissions in an isolated environment.
Build the image using the provided Dockerfile:

```bash
cd containers/grader
docker build -t ghcr.io/your-org/canvas-grader:latest .
```

Key hardening steps:

- Runs as a non-root user (`app`, UID/GID configurable via build args).
- Installs dependencies with `uv sync --frozen --group tests` to mirror project
  tooling.
- Uses `ENTRYPOINT` pointing to `canvas_code_correction.runner` which will be
  replaced with the course-specific grading logic.

When running under Prefect, pass volume mounts for submission workspaces and set
environment variables (`CCC_RESULTS_FILE`, `CCC_POINTS_FILE`, etc.) to align
with your grading contract.

## Running the Grader via `ccc`

1.  Customise `canvas_code_correction/runner.py` (or another module invoked by
    the entrypoint) with your course-specific grading logic.
2.  Build and optionally publish the image:

    ```bash
    docker build -t <registry>/grader:latest containers/grader
    docker push <registry>/grader:latest  # optional but recommended
    ```

3.  Register the grader configuration so the orchestrator uses the image:

    ```bash
    uv run ccc configure-grader <course-slug> --docker-image <registry>/grader:latest
    ```

    !!! tip "Override runtime command"

        Pass `--env` flags to supply additional environment variables if you
        need to modify the container command or pass configuration knobs to your
        grading script.

4.  Trigger a dry run for a single submission to validate the setup:

    ```bash
    uv run ccc run-once <assignment-id> <submission-id>
    ```

`run-once` downloads the submission, mounts it at `/workspace/submission`, runs
the container, and collects the outputs. Review the returned points and comments
to iterate on your grading logic.
