# Setting Up Prefect

CCC stores course blocks in **Prefect**, creates webhook-oriented deployments
through **`ccc system deploy create`**, and executes those deployments with
**workers** attached to a work pool.

## Try It Now

For a course block named `ccc-course-cs101`, this is the shortest local setup:

```bash
$ poe prefect
```

In a second terminal:

```bash
$ uv run prefect work-pool create --type process course-work-pool-cs101
$ ccc system deploy create ccc-course-cs101
$ uv run prefect worker start --pool course-work-pool-cs101
```

Expected deployment output includes:

```text
Creating deployment for course block: ccc-course-cs101
Deployment 'ccc-cs101-deployment' created/updated successfully
```

## Step 1: Start the Prefect API

For local development, run:

```bash
$ poe prefect
```

This starts the Prefect UI and API at `http://localhost:4200`.

If you use a remote Prefect environment, set `PREFECT_API_URL` and
`PREFECT_API_KEY` accordingly before running CCC commands.

## Step 2: Create the Work Pool

The course block stores a `work_pool_name`. Create that pool before starting a
worker.

```bash
$ uv run prefect work-pool create --type process course-work-pool-cs101
```

You only need to do this once per pool name.

## Step 3: Create the Deployment

CCC owns the deployment shape for webhook-triggered corrections. Do not build
it manually with `prefect deployment build`; use the CLI wrapper instead.

```bash
$ ccc system deploy create ccc-course-cs101
```

The default deployment name for that block is:

```text
webhook-correction-flow/ccc-cs101-deployment
```

If you set a custom deployment name in the course block, CCC will use that
instead.

## Step 4: Start a Worker

Start a worker subscribed to the same pool as the course block:

```bash
$ uv run prefect worker start --pool course-work-pool-cs101
```

Expected output begins with:

```text
Starting worker for pool 'course-work-pool-cs101'...
```

The worker host must have:

- Docker access
- Network access to the Prefect API
- Any registry credentials needed to pull the grader image

## Step 5: Verify the Stack

Run the local health check:

```bash
$ ccc system status
```

Expected output contains health lines for:

- `Prefect server`
- `RustFS (S3)` when credentials are configured

Then trigger a small manual run:

```bash
$ ccc course run 98765 --course ccc-course-cs101 --submission-id 54321 --dry-run
```

That verifies the course block loads and the flow can execute without posting
results.

## Troubleshooting

### The deployment command fails

- Confirm `PREFECT_API_URL` points at a reachable Prefect API.
- Confirm the course block exists with `ccc course list`.

### The worker stays idle

- Confirm the worker pool name matches the course block.
- Inspect the deployment in Prefect:

  ```bash
  $ uv run prefect deployment inspect webhook-correction-flow/ccc-cs101-deployment
  ```

### The worker cannot pull the grader image

- Test Docker locally with `docker pull <image>`.
- Add registry credentials to the worker environment if the image is private.

## Next Steps

- [Scheduling Corrections](03-scheduling-corrections.md)
- [Monitoring Results](04-monitoring-results.md)
- [Running Prefect Locally](06-prefect-agent.md)
