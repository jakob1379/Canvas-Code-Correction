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
