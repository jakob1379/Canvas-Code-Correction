# Running Prefect Locally for Development

This page is the **developer-focused** companion to
[Setting Up Prefect](02-setting-up-prefect.md). Use it when you want a fast
local loop for CCC changes, not just an operator setup.

## Try It Now

Start the local stack in two terminals.

Terminal 1:

```bash
$ poe prefect
```

Terminal 2:

```bash
$ uv run prefect work-pool create --type process canvas-corrections
$ ccc system worker start --course ccc-course-12345-cs101
```

If you want RustFS too, add:

```bash
$ poe s3
$ poe rustfs-setup
```

## Why Run Prefect Locally

Use a local Prefect server when you want to:

- iterate on flow code quickly
- inspect flow runs without a remote dependency
- reproduce worker and deployment behavior on one machine

## Step 1: Start the Server

```bash
$ poe prefect
```

The UI and API are available at `http://localhost:4200`.

## Step 2: Create a Local Work Pool

```bash
$ uv run prefect work-pool create --type process canvas-corrections
```

You can use any pool name, but your worker and deployment must match it.
With CCC's shared-environment storage mode, the recommended pattern is still
one generated work pool per course.

## Step 3: Start the Worker

```bash
$ ccc system worker start --course ccc-course-12345-cs101
```

Expected output begins with:

```text
Starting Prefect worker for pool: course-work-pool-12345-cs101
```

For a `shared_environment` course that has `RUSTFS_*` credentials in the
environment, this line appears first:

```text
Mirrored RUSTFS_* credentials into AWS_* for the worker
```

The mirroring line only appears when `RUSTFS_ACCESS_KEY` and
`RUSTFS_SECRET_KEY` are set in the worker's environment. If they are not, CCC
leaves the AWS credential chain alone so an IAM role or `~/.aws` profile keeps
working.

## Step 4: Use a Course Block That Targets the Same Pool

For local runs, create or update a course block with:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --course-id 12345 \
  --docker-image ghcr.io/example/cs101-grader:latest
```

Then create the deployment:

```bash
$ ccc system deploy create ccc-course-12345-cs101
```

## Step 5: Trigger Work

For quick validation, prefer the CCC CLI:

```bash
$ ccc course run 98765 --course ccc-course-12345-cs101 --submission-id 54321 --dry-run
```

To inspect recent flow activity:

```bash
$ uv run prefect flow-run ls --limit 5
```

## Troubleshooting

### The local server is up but CCC cannot reach it

- Confirm `PREFECT_API_URL=http://localhost:4200/api`
- Re-run `ccc system status`

### The Docker worker cannot reach the Prefect API

- Start the server with `prefect server start --host 0.0.0.0` when the API runs in a container.
- Inside Docker Compose, point workers at `http://prefect-server:4200/api`, not `localhost`.

### The worker is running but nothing executes

- Confirm the course block and worker use the same pool name
- Confirm you started the worker through `ccc system worker start --course ...`
- Inspect the deployment:

  ```bash
  $ uv run prefect deployment inspect webhook-correction-flow/ccc-cs101-deployment
  ```

### RustFS is not available

- Start it with `poe s3`
- Register the local block with `poe rustfs-setup`

## Next Steps

- [Monitoring Results](04-monitoring-results.md)
- [CLI Reference](../reference/02-cli.md)
- [Architecture Overview](../reference/01-architecture.md)
