# Monitoring Results

!!! note "Audience"
    CCC platform operators **Prerequisites**: Corrections running via Prefect (see [Scheduling
    corrections](03-scheduling-corrections.md))

**CCC** uploads feedback and grades to Canvas after each correction run. You can
monitor the entire process through the **Prefect dashboard** and verify the
results in **Canvas**. This guide walks you through both in **3 minutes**.

!!! note "Try It Now (60 seconds)"

    If you have a correction flow that ran in the last hour, open the Prefect UI
    and check its status:

    ```bash
    $ prefect server start  # if using local server
    # Or open https://app.prefect.cloud/your-workspace
    ```

    Then list the most recent flow runs for your deployment:

    ```bash
    $ prefect flow-run ls --limit 5
    ```

    Expected output (example):

    ```
    ID                                    Name                State    Start Time
    ─────────────────────────────────────────────────────────────────────────────
    2a1b3c4d-5e6f-7890-abcd-ef1234567890  cs101-corrections   Success  2025-01-21 14:30:00
    1b2c3d4e-5f6g-7890-bcde-fg2345678901  cs101-corrections   Failed   2025-01-21 14:25:00
    ```

    **Success** means the correction completed and feedback was uploaded to
    Canvas. **Failed** indicates an error: see the troubleshooting section below.

---

## Prerequisites

Before you start monitoring, ensure:

1. **Corrections are scheduled or triggered** – either via cron schedule,
   webhook, or manual run
   ([Scheduling corrections](03-scheduling-corrections.md))
2. **Prefect worker is running** – listening to the same pool as your deployment
   ([Setting up Prefect](02-setting-up-prefect.md))
3. **Canvas course access** – you can log into the Canvas course as an
   instructor to view feedback

If you haven’t run any corrections yet, trigger a test run with:

```bash
$ ccc course run <assignment-id>
```

Replace `<assignment-id>` with a numeric Canvas assignment ID. Wait 2–3 minutes
for the flow to complete.

## 1. Monitoring with Prefect Dashboard

The **Prefect UI** gives you real‑time visibility into flow runs, logs, and
errors. Use it to verify that corrections are running, inspect grader output,
and debug failures.

### Open the dashboard

- **Prefect Cloud**: Go to `https://app.prefect.cloud/your-workspace`
- **Local Prefect server**: Start the UI with `prefect server start` and open
  `http://localhost:4200`

### Check flow‑run status

From the CLI, list recent flow runs for your deployment:

```bash
$ prefect flow-run ls --limit 10
```

**Expected output** (columns may vary):

```
ID                                    Name                State    Start Time
─────────────────────────────────────────────────────────────────────────────
2a1b3c4d-5e6f-7890-abcd-ef1234567890  cs101-corrections   Success  2025-01-21 14:30:00
1b2c3d4e-5f6g-7890-bcde-fg2345678901  cs101-corrections   Failed   2025-01-21 14:25:00
```

**States to watch**:

- **`Success`** – correction completed; feedback uploaded to Canvas
- **`Failed`** – something went wrong; check the logs
- **`Pending`** – waiting for a worker
- **`Running`** – currently executing

### View logs and task output

Click a flow run in the UI, or use the CLI to stream its logs:

```bash
$ prefect flow-run logs <flow-run-id>
```

The logs show each step of the correction process:

1. **Fetch submission** – downloading student files from Canvas
2. **Pull grader image** – Docker image for your grader
3. **Run grader** – executing the grader container with the student’s code
4. **Upload feedback** – packaging results and posting to Canvas

**Look for**:

- `Grader output:` lines – the raw stdout/stderr from your grader container
- `Uploaded feedback ZIP to Canvas` – confirmation that feedback reached Canvas
- Any **error messages** (Docker failures, missing files, Canvas API errors)

## 2. Viewing Canvas Feedback

CCC uploads a **feedback ZIP file** to each submission’s comments area. Students
can download the ZIP from their submission page; instructors can see it in
SpeedGrader.

### Locate the feedback ZIP

1. Go to the Canvas assignment.
2. Click **SpeedGrader**.
3. Select a student’s submission.
4. In the right‑hand comments panel, look for a file attachment named
   `feedback-<timestamp>.zip`.

### What’s inside the ZIP

Download and extract the ZIP to see three files:

| File               | Purpose                                        |
| ------------------ | ---------------------------------------------- |
| **`results.json`** | Structured results from the grader (JSON)      |
| **`comments.txt`** | Plain‑text feedback for the student            |
| **`points.txt`**   | Score(s) – the first line is the numeric grade |

**Example `comments.txt`**:

```
Your submission passed 3/5 test cases.

✓ test_addition passed
✓ test_subtraction passed
✗ test_multiplication failed (expected 6, got 7)
✗ test_division failed (division by zero)
✓ test_modulus passed

See results.json for detailed output.
```

**Example `points.txt`**:

```
3
```

## 3. Verifying Grades

CCC can post grades to Canvas automatically if **grade posting** is enabled in
your course configuration. The grade is extracted from the first line of
`points.txt`.

### How grades are posted

1. The grader container writes a numeric score to `points.txt` (one number per
   line).
2. CCC reads the first line and submits it as the submission’s grade.
3. The grade appears in the Canvas gradebook.

**Important**: The grader must output a numeric value (e.g., `5`, `87.5`).
Non‑numeric lines are ignored.

### Check the gradebook

Open the Canvas gradebook for the assignment. You should see grades for
submissions that have been corrected. If a grade is missing:

- Confirm the grader wrote a valid number to `points.txt`
- Ensure **grade posting** is enabled (see
  [Configuring a Course](01-configuring-course.md))
- Look for errors in the Prefect logs (`Upload grade failed`)

## 4. Troubleshooting Common Issues

Use this step‑by‑step checklist to diagnose problems.

### Issue 1: Grader container fails

**Symptoms**: Flow run fails with `Docker container exited with code 1`, or logs
show `Grader output:` contains a stack trace.

**Diagnosis**:

1. Run the grader image locally with a test submission:
   ```bash
   $ docker run --rm yourusername/canvas-grader:latest /path/to/student/code
   ```
2. Check dependencies and entrypoint in your Dockerfile.

**Fix**: Update the Docker image, rebuild, and push. Then reconfigure the course
with the new image tag:

```bash
$ ccc course setup --slug cs101 --docker-image yourusername/canvas-grader:v2
```

### Issue 2: Missing submission files

**Symptoms**: Logs show `No files found for submission` or
`Canvas API returned empty file list`.

**Diagnosis**:

1. Verify the Canvas token and course ID are correct:
   ```bash
   $ ccc course list
   ```
2. Ensure the assignment ID exists and students have submitted files.

**Fix**: Regenerate the Canvas token and update the course block:

```bash
$ printf "%s" "$NEW_TOKEN" | ccc course setup --slug cs101 --token-stdin
```

### Issue 3: S3 asset fetch fails

**Symptoms**: `Failed to fetch assets from S3` or `No such key` errors.

**Diagnosis**:

1. Confirm the S3 bucket block exists and the worker has read permissions.
2. Check the S3 prefix matches where you uploaded grader tests
   ([Deploying tests to CCC](05-deploying-tests-to-ccc.md)).

**Fix**: Update the course block with the correct prefix or recreate the S3
bucket block.

### Issue 4: Prefect worker offline

**Symptoms**: Flow runs stuck in `Pending` state for more than 5 minutes.

**Diagnosis**:

1. List active workers:
   ```bash
   $ prefect worker ls
   ```
2. Ensure a worker is running for your work pool (`course-work-pool-cs101`).

**Fix**: Start the worker (keep the terminal open or run as a service):

```bash
$ prefect worker start --pool course-work-pool-cs101
```

### Issue 5: Feedback not appearing in Canvas

**Symptoms**: Flow run succeeds but no ZIP appears in SpeedGrader.

**Diagnosis**:

1. Check the logs for `Uploaded feedback ZIP to Canvas` – if missing, Canvas API
   may have rejected the upload.
2. Verify the Canvas token has **write** permissions (`courses:grades:edit`,
   `courses:assignments:edit`).

**Fix**: Regenerate the token with the correct scopes and update the course
block.

### Debugging with a single submission

When in doubt, run a one‑off correction for a specific submission to see
detailed output:

```bash
$ ccc course run <assignment-id> --submission-id <submission-id>
```

The command prints each step and stops on the first error.

## Next Steps

Your correction pipeline is now fully observable. Next, you can:

- **Iterate on grader tests** – improve feedback quality and test coverage
  ([Deploying tests to CCC](05-deploying-tests-to-ccc.md))
- **Scale workers** – add more workers to handle concurrent submissions
- **Set up alerts** – configure Prefect notifications for failed flow runs
- **Review advanced topics** – see the Administration and Development sections
  for custom integrations

!!! tip
    Keep the Prefect UI open during peak submission periods to catch failures early. Use the
    troubleshooting checklist above to resolve common issues in 2–5 minutes.
