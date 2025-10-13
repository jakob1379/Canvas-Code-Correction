# Canvas Code Correction v2

Canvas Code Correction v2 rebuilds the original bash-driven pipeline as a fully Pythonic
orchestration layer powered by Prefect and containerized runners. This documentation tracks the
rewrite and the evolving design decisions.

## Goals

- Remove ad-hoc shell orchestration in favour of typed Python flows.
- Trigger corrections on demand (webhooks, scheduled batches, manual runs).
- Execute grading in ephemeral Docker containers with non-root users and resource quotas.
- Maintain a clear separation between Canvas interactions, storage, and execution.
- Ship with batteries included: MkDocs docs, pytest-based tests, and uv-managed dependencies.

## Getting Started

```bash
# Install dependencies (uv handles virtualenv and locking)
uv sync

# Run tests
uv run pytest

# Serve documentation locally
uv run mkdocs serve
```

The CLI is exposed through `uv run ccc`. Use `ccc run-once <assignment-id> <submission-id>` for a
local dry-run of the Prefect flow.
