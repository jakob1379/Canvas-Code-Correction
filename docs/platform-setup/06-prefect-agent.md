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
$ uv run prefect worker start --pool canvas-corrections
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

## Step 3: Start the Worker

```bash
$ uv run prefect worker start --pool canvas-corrections
```

Expected output begins with:

```text
Starting worker for pool 'canvas-corrections'...
```

## Step 4: Use a Course Block That Targets the Same Pool

For local runs, create or update a course block with:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --course-id 12345 \
  --slug cs101 \
  --assets-block local-rustfs \
  --assets-prefix graders/cs101/ \
  --docker-image ghcr.io/example/cs101-grader:latest \
  --work-pool canvas-corrections
```

Then create the deployment:

```bash
$ ccc system deploy create ccc-course-cs101
```

## Step 5: Trigger Work

For quick validation, prefer the CCC CLI:

```bash
$ ccc course run 98765 --course ccc-course-cs101 --submission-id 54321 --dry-run
```

To inspect recent flow activity:

```bash
$ uv run prefect flow-run ls --limit 5
```

## Troubleshooting

### The local server is up but CCC cannot reach it

- Confirm `PREFECT_API_URL=http://localhost:4200/api`
- Re-run `ccc system status`

### The worker is running but nothing executes

- Confirm the course block and worker use the same pool name
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
