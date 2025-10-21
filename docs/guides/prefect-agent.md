# Local Prefect Worker Guide

This guide explains how to run Prefect locally to orchestrate Canvas correction
flows.

1. Start Prefect Orion:
   ```bash
   uv run prefect server start
   ```
2. Launch a local work pool and worker scoped to the `canvas-corrections` queue:
   ```bash
   uv run prefect work-pool create --type process canvas-corrections
   uv run prefect worker start --pool canvas-corrections
   ```
3. Deploy the flow defined in `canvas_code_correction.flows.correct_submission`
   and trigger it via CLI (`uv run ccc run-once ...`) or webhook.

Ensure environment variables for Canvas credentials are exported or provided via
a `.env` file.
