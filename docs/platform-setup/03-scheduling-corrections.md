# Scheduling Corrections

This page aligns with the **current CCC deployment model**:

- `ccc system deploy create` creates a **webhook-oriented deployment**
- `ccc course run` is the supported path for **manual and backfill runs**
- Canvas webhooks are the supported path for **automatic per-submission runs**

## What "Scheduling" Means Today

CCC does **not** ship a built-in cron-style batch deployment for "grade every
submission in a course at 02:00 every day". The deployment created by
`ccc system deploy create` expects webhook-style course and submission payloads,
so it is intended for **event-driven runs**, not parameterless nightly sweeps.

## Recommended Automation Patterns

### 1. Immediate grading on submission

Use this when you want the normal production flow.

1. Start the webhook server:

   ```bash
   $ ccc system webhook serve --host 0.0.0.0 --port 8080
   ```

2. Create the Prefect deployment:

   ```bash
   $ ccc system deploy create ccc-course-cs101
   ```

3. Start a worker for the course work pool:

   ```bash
   $ uv run prefect worker start --pool course-work-pool-cs101
   ```

4. Configure Canvas to send submission events to the webhook server.

### 2. Manual backfills

Use this when you need to rerun an assignment or a single submission.

```bash
$ ccc course run 98765 --course ccc-course-cs101
```

Or:

```bash
$ ccc course run 98765 --course ccc-course-cs101 --submission-id 54321 --dry-run
```

### 3. Custom scheduled jobs

If your team needs nightly or weekly backfills, create a **separate Prefect
flow** that calls CCC with the assignment IDs you want. That scheduled flow is
outside the built-in webhook deployment that CCC creates for you.

## Prefect Deployment Schedules

Prefect itself supports deployment schedules:

```bash
$ uv run prefect deployment schedule create --help
```

Use those commands only for deployments whose parameters make sense on a
schedule. For the built-in CCC webhook deployment, that usually means **do not**
attach a cron schedule unless you have wrapped it with the required inputs.

Useful commands:

```bash
$ uv run prefect deployment schedule ls <FLOW_NAME>/<DEPLOYMENT_NAME>
$ uv run prefect deployment schedule clear <FLOW_NAME>/<DEPLOYMENT_NAME> --accept-yes
```

## Canvas Webhook Checklist

For the standard automatic path, confirm:

- the webhook server is reachable
- the Prefect deployment exists
- a worker is online for the course work pool
- the course block points at the correct work pool and assets

## Next Steps

Once runs are being triggered, continue with
[Monitoring Results](04-monitoring-results.md).
