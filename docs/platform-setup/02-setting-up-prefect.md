# Setting up Prefect

> **Audience**: CCC platform operators **Prerequisites**: Course configured via
> `ccc configure-course`

CCC uses Prefect for workflow orchestration. After configuring a course, you
need to create a Prefect deployment and start a worker.

## Creating a Deployment

A deployment makes your correction flow triggerable via schedule, API, or UI.
Use the Prefect CLI:

```bash
uv run prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n cs101-corrections \
  -q course-work-pool-cs101 \
  -a
```

- `-n`: Deployment name (unique)
- `-q`: Work pool name (must match the worker pool)
- `-a`: Apply the deployment immediately

The work pool name should match the one configured for your course (default
`course-work-pool-<slug>`).

## Starting a Worker

Workers execute flow runs. Start a worker for your course's work pool:

```bash
uv run prefect worker start --pool course-work-pool-cs101
```

The worker must have access to Docker and the same environment variables (Canvas
token, etc.) as configured in the course block.

You can run workers on any machine: your laptop, a server, or a container
orchestration platform.

## Triggering a Test Run

Once the worker is running, trigger a flow run:

- Via Prefect UI: Navigate to Deployments and click "Run"
- Via CLI: `uv run prefect deployment run cs101-corrections`
- Via CCC CLI: `uv run ccc run-once <assignment-id>`

Test with a single submission first to ensure everything works.

Next, we'll schedule automatic corrections.
