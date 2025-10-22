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
   and trigger it via CLI (e.g., `uv run ccc run-once <assignment-id>`) or
   webhook.

Ensure Prefect blocks already store Canvas credentials, runner configuration,
and the S3 assets block referenced by `configure-course`; locally you only need
`PREFECT_API_KEY` when invoking deployments.
