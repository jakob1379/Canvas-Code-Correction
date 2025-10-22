# Canvas Code Correction v2

Canvas Code Correction v2 rebuilds the original bash-driven pipeline as a fully
Pythonic orchestration layer powered by Prefect and containerized runners. This
documentation tracks the rewrite and the evolving design decisions.

## Goals

- Remove ad-hoc shell orchestration in favour of typed Python flows.
- Trigger corrections on demand (webhooks, scheduled batches, manual runs).
- Execute grading in ephemeral Docker containers with non-root users and
  resource quotas.
- Maintain a clear separation between Canvas interactions, storage, and
  execution.
- Ship with batteries included: MkDocs docs, pytest-based tests, and uv-managed
  dependencies.

## Getting Started

```bash
# Install dependencies (uv handles virtualenv and locking)
uv sync

# Run tests
uv run pytest

# Serve documentation locally
uv run mkdocs serve
```

The CLI is exposed through `uv run ccc`. Use `ccc run-once <assignment-id>` for
an assignment-wide dry-run of the Prefect flow, or pass `--submission` to focus
on specific submissions.

For course-specific environments, provision an S3 bucket that stores immutable
grader assets (tests, fixtures, helper scripts) and register a Prefect S3 Bucket
block that points at the bucket/prefix. The block name must be passed to
`configure-course` and is reused by the flows at runtime.

```bash
# Example: create/update course configuration to use S3-backed grader assets
uv run ccc configure-course <course-slug> \
  --docker-image jakob1379/canvas-grader:latest \
  --assets-block course-assets-<course-slug> \
  --s3-bucket <course-assets-bucket> \
  --s3-prefix graders/<course-slug>/ \
  --env EXTRA_REQUIREMENT=1
```

Each course supplies its own Docker image, Prefect work pool, and Prefect S3
block without touching the shared orchestration code; flows resolve the
configuration from the stored Prefect blocks at runtime. Ensure the block has
permission to read the bucket (and optional prefix) before invoking flows.
