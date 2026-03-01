# Scheduling Corrections

!!! note "Audience"
    CCC platform operators **Prerequisites**: Prefect deployment created and worker running (see
    [Setting up Prefect](02-setting-up-prefect.md))

## Try It Now (60 seconds)

Schedule automatic corrections for a course that already has a Prefect
deployment. If you have a deployment named `cs101-corrections`, attach a cron
schedule that runs daily at 2 AM:

```bash
$ prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n cs101-corrections \
  -q course-work-pool-cs101 \
  --schedule "0 2 * * *" \
  -a
```

Expected output:

```
Successfully updated deployment 'cs101-corrections'!
Deployment applied to work pool 'course-work-pool-cs101'.
```

Your corrections now run automatically every day at 2 AM. Continue with the
guide to learn cron syntax, webhook triggers, and manual overrides.

---

**Canvas Code Correction** runs submissions on a schedule (e.g., every night at
2 AM) or triggers immediately via Canvas webhooks when a student submits. This
guide walks you through both options in **5 minutes**.

## Prerequisites

Before you schedule corrections, ensure you have:

1. **A Prefect deployment** – created with `prefect deployment build`
   ([Setting up Prefect](02-setting-up-prefect.md))
2. **A running worker** – listening to the same work pool as the deployment
3. **Access to the Canvas course** – to set up webhooks (optional)

If you haven’t completed the setup, go back to
[Setting up Prefect](02-setting-up-prefect.md) and finish **Steps 1 and 2**.

## 1. Scheduling with Cron

**Prefect schedules** let you run corrections at fixed times (like a system cron
job). Attach the schedule when you build or update a deployment.

### Cron syntax quick reference

CCC uses standard cron syntax with five fields:

```
┌───────────── minute (0–59)
│ ┌───────────── hour (0–23)
│ │ ┌───────────── day of month (1–31)
│ │ │ ┌───────────── month (1–12)
│ │ │ │ ┌───────────── day of week (0–6, Sunday=0)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

| Example         | Meaning                             |
| --------------- | ----------------------------------- |
| `0 2 * * *`     | Every day at 02:00                  |
| `30 14 * * 1-5` | Monday–Friday at 14:30              |
| `*/15 * * * *`  | Every 15 minutes                    |
| `0 0 1 * *`     | First day of each month at midnight |

### Attach a schedule to an existing deployment

Use the same `prefect deployment build` command with the `--schedule` flag.
**Keep all other flags identical** (name, work pool, etc.).

```bash
$ prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n cs101-corrections \
  -q course-work-pool-cs101 \
  --schedule "0 2 * * *" \
  -a
```

**What happens:**

- The existing deployment `cs101-corrections` updates with the new schedule.
- Future flow runs create automatically at the specified times.
- The worker picks up each run and executes the correction flow.

!!! tip
    To remove a schedule, run the same command **without** the `--schedule` flag.

### View and edit schedules in the Prefect UI

1. Open the Prefect UI (cloud or local).
2. Navigate to **Deployments** and select your deployment.
3. Click the **Schedule** tab to see the cron expression and next scheduled run.
4. Use the **Edit** button to change the schedule interactively.

## 2. Trigger via Canvas Webhooks

For immediate corrections after each student submission, configure Canvas to
send webhooks to your Prefect deployment.

### How webhooks work

1. Canvas detects a `submission_created` event.
2. Canvas sends an HTTP POST to a **webhook endpoint** provided by Prefect.
3. Prefect creates a flow run for the affected assignment and submission.
4. Your worker picks up the run and corrects that submission.

### Step‑by‑step setup

#### 1. Get your deployment’s webhook URL

Prefect Cloud automatically provides a webhook endpoint for each deployment.

1. In the Prefect UI, go to **Deployments** and select your deployment.
2. Click the **Webhooks** tab.
3. Copy the **URL** shown (looks like
   `https://api.prefect.cloud/api/accounts/.../webhooks/...`).

!!! note
    If you run a self‑hosted Prefect server, consult the [Prefect webhook documentation](https://docs.prefect.io/concepts/webhooks/) for
    endpoint configuration.

#### 2. Add the webhook in Canvas

1. In Canvas, go to your course → **Settings** → **Integrations**.
2. Click **+ Add Webhook**.
3. Fill in the fields:

   | Field      | Value                               |
   | ---------- | ----------------------------------- |
   | **URL**    | Paste the webhook URL from Prefect  |
   | **Event**  | Select `submission_created`         |
   | **Format** | `JSON` (default)                    |
   | **Secret** | (Optional) Add a secret for signing |

4. Click **Save**.

Canvas now sends a POST request to Prefect for every new submission.

#### 3. Verify the webhook payload

CCC expects a JSON payload with at least `assignment_id` and `submission_id`.
Canvas sends a richer object; CCC extracts the required fields automatically.

To transform the payload (e.g., rename keys), write a small middleware or use
Prefect’s **webhook transformations** (see
[Prefect webhook documentation](https://docs.prefect.io/concepts/webhooks/)).

### Test the webhook

1. Make a test submission in Canvas.
2. Watch the Prefect UI for a new flow run (appears within seconds).
3. Check the logs to confirm the correction succeeded.

## 3. Manual Triggers (When You Need Control)

Even with schedules and webhooks, you can always trigger corrections manually.

### Via the Prefect UI

1. Open **Deployments** and select your deployment.
2. Click the **Run** button.
3. Choose **Custom** to provide parameters (assignment ID, submission ID, etc.).

### Via the CLI

```bash
$ prefect deployment run cs101-corrections
```

This creates a flow run for **all submissions that need grading** (default
behavior).

### Via the CCC CLI (single assignment)

```bash
$ ccc course run 12345
```

Replace `12345` with the numeric Canvas assignment ID. This command creates a
one‑off flow run for just that assignment, ideal for debugging or urgent
corrections.

## 4. Monitoring and Next Steps

Once corrections are scheduled, use the **Prefect dashboard** to monitor flow
runs, view logs, and inspect results. For a full guide, see
[Monitoring results](04-monitoring-results.md).

### Quick checklist after setup

- [ ] Schedule attached (cron expression correct)
- [ ] Worker online and listening to the work pool
- [ ] Webhook configured (if using immediate triggers)
- [ ] Test run completed successfully

---

**Next**: Learn how to interpret correction results, view feedback in Canvas,
and troubleshoot common issues in
[Monitoring results](04-monitoring-results.md).
