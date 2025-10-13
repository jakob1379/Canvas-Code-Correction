# Local Prefect Agent Guide

This guide explains how to run Prefect locally to orchestrate Canvas correction
flows.

1. Start Prefect Orion:
   ```bash
   uv run prefect server start
   ```
2. Launch a local work pool and agent scoped to the `canvas-corrections` queue:
   ```bash
   uv run prefect work-pool create --type process canvas-corrections
   uv run prefect agent start --pool canvas-corrections
   ```
3. Deploy the flow defined in `canvas_code_correction.flows.correct_submission`
   and trigger it via CLI (`uv run ccc run-once ...`) or webhook.

Ensure environment variables for Canvas credentials are exported or provided via
a `.env` file.
