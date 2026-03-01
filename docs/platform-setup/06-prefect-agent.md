# Running Prefect Locally for Development

!!! note "Audience"
    CCC developers and testers **Prerequisites**: Python 3.13+,
    Docker installed and running, CCC installed (`uv install -e .`)

**Prefect Orion** is the local server that orchestrates correction workflows
when you are developing or testing CCC. This guide shows you how to start Orion,
create a local work pool, and launch a worker that picks up flow runs, **all in
3 minutes**.

!!! note "Try It Now (90 seconds)"

    If you have a course configured with slug `cs101`, run these commands to start
    a local Prefect server and a worker:

    ```bash
    $ prefect server start
    ```

    Expected output (server starts on http://127.0.0.1:4200):

    ```
     ___ ___ ___ ___ ___ ___ _____
    | _ \ _ \ __| __| __/ __|_   _|
    |  _/   / _|| _|| _| (__  | |
    |_| |_|_\___|_| |_| \___| |_|

    Starting Prefect server...
    Server started on http://127.0.0.1:4200
    ```

    In a **second terminal**, create a work pool and start a worker for the
    `canvas-corrections` queue:

    ```bash
    $ prefect work-pool create --type process canvas-corrections
    $ prefect worker start --pool canvas-corrections
    ```

    Expected worker output:

    ```
    Starting worker for pool 'canvas-corrections'...
    Worker 'eager-panda' started!
    Waiting for flow runs...
    ```

    Your local Prefect environment is now ready. Keep both terminals open.

---

## Why Run Prefect Locally?

When you are developing grader images, writing tests, or debugging correction
logic, you need a **fast feedback loop**. A local Prefect server
(`prefect server start`) gives you:

- **No network latency** – all communication stays on your machine.
- **Full control** – you can restart, reset, or inspect the server state.
- **Isolation** – your experiments do not affect production corrections.

This setup is **not for production**; use Prefect Cloud or a self‑hosted Prefect
server for real courses. For production deployment, see
[Setting up Prefect](02-setting-up-prefect.md).

## Prerequisites

Before you start, ensure you have:

1. **Python 3.13+** and `uv` installed (the project uses `uv run`).
2. **Docker** installed and running (the worker launches grader containers).
3. **CCC installed** in editable mode:
   ```bash
   $ uv install -e .
   ```
4. **A configured course** (if you want to run actual corrections). Complete
   [Configuring a Course](01-configuring-course.md) first.

## Step 1: Start the Prefect Orion Server

Open a terminal in the project root and run:

```bash
$ prefect server start
```

### What you will see

The command prints the Prefect ASCII logo and starts the server on
`http://127.0.0.1:4200`. The output looks like this:

```
 ___ ___ ___ ___ ___ ___ _____
| _ \ _ \ __| __| __/ __|_   _|
|  _/   / _|| _|| _| (__  | |
|_| |_|_\___|_| |_| \___| |_|

Starting Prefect server...
Server started on http://127.0.0.1:4200
```

!!! note
    The server runs in the foreground. Keep this terminal open. You can
    stop it with `Ctrl+C`.

### Verify the server

Open your browser to `http://127.0.0.1:4200`. You should see the Prefect UI with
an empty dashboard. No login is required for the local server.

## Step 2: Create a Local Work Pool

A **work pool** is a named queue that workers subscribe to. For local
development, create a pool of type `process` (the worker will run flows in
subprocesses).

In a **second terminal** (same project directory), run:

```bash
$ prefect work-pool create --type process canvas-corrections
```

**Expected output:**

```
Created work pool 'canvas-corrections' (type: process)
```

The pool is now visible in the Prefect UI under **Work Pools**.

!!! note "Why canvas-corrections?" This is a simple local queue name for
testing. CCC can use any queue name as long as your deployment and worker use
the same pool. deployment targets the same pool.

## Step 3: Start a Worker

**Workers** are processes that pick up flow runs from a work pool and execute
them. Start a worker for the pool you just created:

```bash
$ prefect worker start --pool canvas-corrections
```

**Expected output:**

```
Starting worker for pool 'canvas-corrections'...
Worker 'eager-panda' started!
Waiting for flow runs...
```

The worker will stay alive and wait for flow runs. It needs:

- **Access to Docker** (to launch grader containers).
- **The same environment variables** (Canvas token, etc.) that you configured in
  the course block.
- **Network connectivity** to the local Orion server (already satisfied).

Keep this terminal open as well. You can run multiple workers for the same pool
to distribute load.

## Step 4: Trigger a Test Correction

With the server running and a worker waiting, trigger a correction flow to
verify everything works.

### Option A: Use the CCC CLI (recommended)

If you have a course configured, run a one‑off correction for a specific
assignment:

```bash
$ ccc course run <assignment-id>
```

Replace `<assignment-id>` with the numeric Canvas assignment ID. The command
creates a flow run that your local worker will pick up immediately.

### Option B: Use the Prefect CLI

First, create a deployment that targets your local pool (replace `cs101` with
your course slug):

```bash
$ prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n cs101-corrections \
  -q canvas-corrections \
  -a
```

Then run the deployment:

```bash
$ prefect deployment run cs101-corrections
```

### Option C: Use the Prefect UI

1. Open `http://127.0.0.1:4200`.
2. Navigate to **Deployments** and find your deployment.
3. Click the **Run** button.

### Expected outcome

Watch the worker terminal. You should see logs like:

```
Picked up flow run 'golden-sloth' from pool 'canvas-corrections'
Executing flow 'correct-submission-flow'...
Downloading submission from Canvas...
Pulling grader image 'yourusername/canvas-grader:latest'...
Running grader container...
```

If the flow completes successfully, you will see a final log line with the score
submitted to Canvas.

## Step 5: Configure Prefect Blocks Locally

For local runs, you must ensure the **Prefect blocks** that store Canvas
credentials, runner configuration, and S3 assets already exist. The
`ccc course setup` command creates these blocks for you.

If you have not configured a course yet, follow
[Configuring a Course](01-configuring-course.md). The blocks are stored in the
local Orion server's SQLite database, so they persist across server restarts.

!!! note "Important" When you run `ccc course run` locally, you do **not** need
to set `PREFECT_API_KEY` (the local server does not require authentication).
However, you still need the blocks that hold your Canvas token and S3 bucket
details.

## Troubleshooting

### The worker cannot connect to the server

- Ensure the Orion server is still running (first terminal).
- Check that the worker uses the same API URL (default
  `http://127.0.0.1:4200/api`). The local worker auto‑discovers it; if you
  changed the port, set `PREFECT_API_URL`.

### The worker fails to pull the Docker image

- Verify Docker is running (`docker ps`).
- Ensure the grader image exists locally or is accessible from Docker Hub.

### The flow run stays `Scheduled` forever

- Confirm the worker is subscribed to the correct pool (`canvas-corrections`).
- Look for errors in the worker logs (the second terminal).

### Blocks are missing

- Run `ccc course setup` to create the necessary blocks.
- List existing blocks with `prefect block list`.

## Next Steps

Your local Prefect environment is ready for development. Next, you can:

- **Write and test grader images** – see
  [Creating a Grader Image](../tutorial/03-creating-grader-image.md).
- **Upload test assets to S3** – see
  [Deploying Tests to CCC](05-deploying-tests-to-ccc.md).
- **Schedule corrections** (on a local schedule) – follow
  [Scheduling Corrections](03-scheduling-corrections.md).
- **Monitor runs and logs** in the Prefect UI – see
  [Monitoring Results](04-monitoring-results.md).

!!! tip
    When you are done testing, stop the Orion server (`Ctrl+C` in the first terminal) and the worker
    (`Ctrl+C` in the second terminal). The local SQLite database (`~/.prefect/orion.db`) retains
    blocks and run history for the next session.
