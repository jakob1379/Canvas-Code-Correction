# Scheduling Corrections

> **Audience**: CCC platform operators **Prerequisites**: Prefect deployment
> created and worker running

CCC can automatically correct submissions on a schedule or trigger via Canvas
webhooks.

## Prefect Schedules

When building a deployment, you can attach a schedule. For example, to run every
day at 2 AM:

```bash
uv run prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n cs101-corrections \
  -q course-work-pool-cs101 \
  --schedule "0 2 * * *" \
  -a
```

The schedule uses cron syntax. You can also set interval schedules via Prefect
UI.

## Canvas Webhooks

Canvas can send webhooks when students submit assignments. CCC can listen to
these webhooks and trigger corrections automatically.

### Setting up Webhooks

1. In Canvas, go to **Course Settings** > **Integrations**.
2. Add a webhook URL pointing to your Prefect deployment's webhook endpoint.
3. Configure the webhook to send `submission_created` events.

Prefect Cloud provides webhook endpoints for deployments. See
[Prefect webhook documentation](https://docs.prefect.io/concepts/webhooks/).

### Webhook Payload

CCC expects a payload with `assignment_id` and `submission_id`. You may need to
transform Canvas webhook payload using a small middleware.

## Manual Triggers

You can always trigger corrections manually via the CLI or UI.

## Monitoring

Use Prefect's dashboard to monitor flow runs, view logs, and inspect results.

Next, we'll explore monitoring and results.
