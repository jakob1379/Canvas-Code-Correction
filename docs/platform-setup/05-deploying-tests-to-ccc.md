# Deploying Grader Tests to Canvas Code Correction (CCC)

> **Audience**: CCC platform operators  
> **Prerequisites**: Grader Docker image built, grader tests ready

This guide walks through publishing instructor grader tests to CCC so Prefect
workers can execute them for a course. It assumes you are using the Prefect v2
rewrite from this repository.

## Prerequisites

- Access to Prefect Cloud or a self-hosted Orion instance.
- Docker installed locally for building grader images.
- Access to the course-specific grader repository with instructor tests.
- Canvas API token and course ID stored in `.env` or Prefect blocks.
- uv installed (used to run project commands).

!!! tip "Export `PREFECT_API_URL`, `PREFECT_API_KEY`, and Canvas credentials"

    before running CLI commands, or update your Prefect profile to include them.

## Local Development Setup

For local development and testing, CCC includes a local S3-compatible server using RustFS. To start it:

```bash
uv run poe s3
```

This starts a RustFS server on `http://localhost:9000` with credentials `rustfsadmin`/`rustfsadmin`. The server stores data in the `./workspace` directory.

To configure the local S3 server for integration tests:

```bash
uv run poe rustfs-setup
```

This script:
1. Verifies RustFS is running
2. Creates a `test-assets` bucket
3. Uploads a test asset file
4. Registers a Prefect S3 block named `local-rustfs`

After setup, you can use `--assets-block local-rustfs` when configuring courses for local testing.

### Configuration via environment variables

The RustFS setup can be customized using environment variables:

- `RUSTFS_ENDPOINT`: S3 endpoint URL (default: `http://localhost:9000`)
- `RUSTFS_ACCESS_KEY`: Access key (default: `rustfsadmin`)
- `RUSTFS_SECRET_KEY`: Secret key (default: `rustfsadmin`)
- `RUSTFS_BUCKET_NAME`: Bucket name (default: `test-assets`)
- `RUSTFS_PREFIX`: Path prefix for assets (default: `dev`)

Example for production setup:
```bash
export RUSTFS_ENDPOINT="https://rustfs.example.com"
export RUSTFS_ACCESS_KEY="your-access-key"
export RUSTFS_SECRET_KEY="your-secret-key"
export RUSTFS_BUCKET_NAME="course-assets"
export RUSTFS_PREFIX="graders/cs101"
uv run poe rustfs-setup
```

## 1. Build and Publish the Grader Image

1. Update `containers/grader/Dockerfile` or your course-specific Dockerfile with
   the necessary dependencies and entrypoint.
2. Build and optionally push the image:

```bash
docker build -t jakob1379/canvas-grader:latest containers/grader
docker push jakob1379/canvas-grader:latest
```

## 2. Configure Prefect Blocks

Use the CLI to configure the course. This provisions a Prefect work pool,
records runner settings, and associates the grader S3 assets block that points
at the bucket/prefix containing immutable grader tests.

```bash
uv run ccc configure-course <course-slug> \
  --docker-image jakob1379/canvas-grader:latest \
  --memory-limit 2g \
  --cpu-limit 2.0 \
  --env PYTHONUNBUFFERED=1 \
  --assets-block course-assets-<course-slug> \
  --s3-bucket <course-assets-bucket> \
  --s3-prefix graders/<course-slug>/
```

This command saves a Prefect JSON block named `course-config-<course-slug>` (by
default) and creates or reuses a work pool `course-work-pool-<course-slug>`.

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
uv run ccc run-once <assignment-id>
```

- Configure the Canvas webhook to call the Prefect webhook URL for automatic
  runs.

## 6. Verify and Iterate

1. Inspect logs in Prefect to ensure the grader command runs successfully.
2. Review artefacts in the submission workspace (results, points, comments).
3. Adjust grader tests or container configuration as required.
4. Rebuild/push the image when the runtime environment changes. To update grader
   tests, upload new files to the S3 bucket/prefix referenced by the Prefect
   block; the next flow run will pick up the new assets automatically.

## Troubleshooting

- **Worker cannot pull image:** ensure the worker environment has credentials
  for private registries and that the image tag is correct.
- **Canvas API failures:** verify tokens and course IDs are present in your
  settings (`.env` or Prefect block).
- **Timeouts / resource issues:** adjust `--memory-limit`, `--cpu-limit`, or
  `--gpu-enabled` flags when running `configure-course`.
- **No runs start:** confirm the work pool name in the deployment matches the
  running worker and that the worker log shows it is connected.

Following these steps keeps grader tests aligned with CCC’s Prefect-based
orchestration while allowing instructors to iterate rapidly on course-specific
grading logic.
