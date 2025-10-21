# Deploying Grader Tests to Cartography Canvas Correction (CCC)

This guide walks through publishing instructor grader tests to CCC so Prefect
workers can execute them for a course. It assumes you are using the Prefect v2
rewrite from this repository.

## Prerequisites

- Access to Prefect Cloud or a self-hosted Orion instance.
- Docker installed locally for building grader images.
- Access to the course-specific grader repository with instructor tests.
- Canvas API token and course ID stored in `.env` or Prefect blocks.
- uv installed (used to run project commands).

!!! tip Export `PREFECT_API_URL`, `PREFECT_API_KEY`, and Canvas credentials

    before running CLI commands, or update your Prefect profile to include them.

## 1. Build and Publish the Grader Image

1. Update `containers/grader/Dockerfile` or your course-specific Dockerfile with
   the necessary dependencies and entrypoint.
2. Build and optionally push the image:

   ```bash
   docker build -t ghcr.io/<org>/<course>-grader:latest containers/grader
   docker push ghcr.io/<org>/<course>-grader:latest
   ```

## 2. Configure Prefect Blocks

Use the CLI to create or update the grader configuration block. This stores the
image reference, runtime limits, and optional environment variables.

```bash
uv run ccc configure-grader <course-slug> \
  --docker-image ghcr.io/<org>/<course>-grader:latest \
  --memory-limit 2g \
  --cpu-limit 2.0 \
  --env PYTHONUNBUFFERED=1
```

The command saves a Prefect JSON block named `grader-config/<course-slug>` by
default. You can inspect or edit the block from the Prefect UI as needed.

## 3. Register / Update the Prefect Deployment

Create a Prefect deployment so CCC flows can be triggered manually, via
schedule, or via webhooks.

```bash
uv run prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n <course-slug>-corrections \
  -q <course-work-pool> \
  -a
```

- `-q` specifies the work pool (course-specific) that matching workers will
  poll.
- `-a` applies the deployment immediately.

Alternatively, create deployments through the Prefect UI if preferred.

## 4. Start a Prefect Worker

Launch a worker connected to the course work pool so queued flow runs can
execute the grader code inside the Docker container.

```bash
uv run prefect worker start --pool <course-work-pool>
```

Workers can run locally, on a dedicated VM, or inside container orchestration
depending on your infrastructure. Ensure Docker access is available wherever the
worker runs.

## 5. Trigger Test Runs

With the deployment active and a worker online, you can:

- Trigger a run manually in the Prefect UI.
- Use the CLI:

  ```bash
  uv run prefect deployment run <course-slug>-corrections
  ```

- Execute a one-off run targeting a specific submission:

  ```bash
  uv run ccc run-once <assignment-id> <submission-id>
  ```

- Configure the Canvas webhook to call the Prefect webhook URL for automatic
  runs.

## 6. Verify and Iterate

1. Inspect logs in Prefect to ensure the grader command runs successfully.
2. Review artefacts in the submission workspace (results, points, comments).
3. Adjust grader tests or container configuration as required.
4. Rebuild/push the image and re-run `configure-grader` when changes are made to
   the grader environment.

## Troubleshooting

- **Worker cannot pull image:** ensure the worker environment has credentials
  for private registries and that the image tag is correct.
- **Canvas API failures:** verify tokens and course IDs are present in your
  settings (`.env` or Prefect block).
- **Timeouts / resource issues:** adjust `--memory-limit`, `--cpu-limit`, or
  `--gpu-enabled` flags when running `configure-grader`.
- **No runs start:** confirm the work pool name in the deployment matches the
  running worker and that the worker log shows it is connected.

Following these steps keeps grader tests aligned with CCC’s Prefect-based
orchestration while allowing instructors to iterate rapidly on course-specific
grading logic.
