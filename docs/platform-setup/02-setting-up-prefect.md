# Setting up Prefect

!!! note "Audience" CCC platform operators **Prerequisites**: Course configured
via `ccc configure-course` (see
[Configuring a Course](01-configuring-course.md))

**Prefect** orchestrates the correction workflows in CCC. After you configure a
course, you need to create a **Prefect deployment** (the definition of how to
run your flow) and start a **worker** (the process that executes flow runs).
This guide walks you through both steps in **3 minutes**.

!!! note "Try It Now (90 seconds)"

    If you already have a course configured with slug `cs101`, run these two
    commands to create a deployment and start a worker:

    ```bash
    $ prefect deployment build \
      canvas_code_correction.flows.correct_submission:correct_submission_flow \
      -n cs101-corrections \
      -q course-work-pool-cs101 \
      -a
    ```

    Expected output:

    ```
    Successfully created deployment 'cs101-corrections'!
    Deployment applied to work pool 'course-work-pool-cs101'.
    ```

    Then start the worker:

    ```bash
    $ prefect worker start --pool course-work-pool-cs101
    ```

    You’ll see the worker connect to Prefect and wait for flow runs. Keep this
    terminal open.

---

## Prerequisites

- A course configured with `ccc configure-course` (if you haven’t, complete
  [Configuring a Course](01-configuring-course.md) first)
- The same Python environment where you installed CCC (`uv run` works)
- Docker installed and running (the worker will launch grader containers)

## Step 1: Create a Prefect deployment

A **deployment** makes your correction flow triggerable via schedule, API, or
UI. Use the Prefect CLI with your course’s **work pool name** (default
`course-work-pool-<slug>`).

### Command template

```bash
$ prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n <deployment-name> \
  -q <work-pool-name> \
  -a
```

Replace `<deployment-name>` with a unique identifier (e.g., `cs101-corrections`)
and `<work-pool-name>` with the pool your worker will listen to (e.g.,
`course-work-pool-cs101`).

### Example with course slug `cs101`

```bash
$ prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n cs101-corrections \
  -q course-work-pool-cs101 \
  -a
```

**What each flag does:**

| Flag | Purpose                                                                 |
| ---- | ----------------------------------------------------------------------- |
| `-n` | **Deployment name** – unique identifier (used when triggering runs)     |
| `-q` | **Work pool** – must match the pool your worker subscribes to           |
| `-a` | **Apply** – create the deployment in your Prefect workspace immediately |

After a successful run you’ll see:

```
Successfully created deployment 'cs101-corrections'!
Deployment applied to work pool 'course-work-pool-cs101'.
```

The deployment is now visible in the Prefect UI under **Deployments**.

## Step 2: Start a worker

**Workers** are processes that pick up flow runs from a work pool and execute
them. Start a worker for your course’s work pool in a separate terminal (or
background process).

### Command

```bash
$ prefect worker start --pool course-work-pool-cs101
```

### Expected output

```
Starting worker for pool 'course-work-pool-cs101'...
Worker 'eager-panda' started!
Waiting for flow runs...
```

The worker will stay alive and wait for flow runs. It must have:

- **Access to Docker** (to launch grader containers)
- **The same environment variables** (Canvas token, etc.) that you configured in
  the course block
- **Network connectivity** to Prefect API (cloud or local server)

You can run workers on any machine: your laptop, a server, or a container
orchestration platform. Multiple workers can join the same pool for load
distribution.

## Step 3: Trigger a test run

With a deployment created and a worker running, trigger a correction flow to
verify everything works.

### Option A: Prefect UI

1. Open the Prefect UI (cloud or local).
2. Navigate to **Deployments** and find your deployment (`cs101-corrections`).
3. Click the **Run** button.

### Option B: Prefect CLI

```bash
$ prefect deployment run cs101-corrections
```

Output:

```
Flow run 'golden-sloth' created!
```

### Option C: CCC CLI (for a specific assignment)

```bash
$ ccc run-once <assignment-id>
```

Replace `<assignment-id>` with the numeric Canvas assignment ID. This command
creates a one‑off flow run for a single assignment, ideal for testing.

**Test with a single submission first** to ensure the worker can pull the grader
image, fetch tests from S3, and submit scores back to Canvas.

## Next steps

Your Prefect deployment and worker are now ready. Next, you can:

- **Schedule automatic corrections** – attach a cron schedule to the deployment
  ([Scheduling corrections](03-scheduling-corrections.md))
- **Monitor runs and logs** – use the Prefect UI to inspect flow runs
  ([Monitoring results](04-monitoring-results.md))
- **Scale workers** – add more workers to the same pool for higher throughput

!!! tip Keep the worker terminal open while testing. For production, run workers
as systemd services or containerized processes.
