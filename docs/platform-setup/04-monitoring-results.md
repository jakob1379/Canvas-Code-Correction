# Monitoring Results

Use **Prefect** to monitor runs and **Canvas** to verify the uploaded grade and
feedback.

## Try It Now

List the most recent flow runs:

```bash
$ uv run prefect flow-run ls --limit 5
```

Then inspect one run's logs:

```bash
$ uv run prefect flow-run logs <flow-run-id> --tail
```

For the local stack, also run:

```bash
$ ccc system status
```

## Prefect Checks

### List recent flow runs

```bash
$ uv run prefect flow-run ls --limit 10
```

Useful states:

- `Running`
- `Completed`
- `Failed`
- `Pending`

### Read the logs

```bash
$ uv run prefect flow-run logs <flow-run-id>
```

Look for the major correction stages:

1. submission metadata fetch
2. workspace preparation
3. grader execution
4. feedback upload
5. grade upload

### Inspect the deployment

```bash
$ uv run prefect deployment inspect webhook-correction-flow/ccc-cs101-deployment
```

This is the fastest way to confirm the deployment name, work pool, and
parameters in Prefect.

### Inspect the work pool

```bash
$ uv run prefect work-pool inspect course-work-pool-cs101
```

Use this when runs stay pending and you need to confirm the pool exists and is
not paused.

## Canvas Checks

After a successful run, verify the submission in Canvas:

1. Open the assignment in **SpeedGrader**
2. Select the submission
3. Confirm the score changed if grade uploads are enabled
4. Confirm the feedback attachment or comment is present

CCC typically uploads:

- a score from `points.txt`
- a comment from `comments.txt`
- feedback artifacts when the grader produced them

## Common Failure Modes

### Runs stay pending

- Start or restart a worker:

  ```bash
  $ uv run prefect worker start --pool course-work-pool-cs101
  ```

- Confirm the course block and worker use the same pool name.

### RustFS or S3 access fails

- Recheck the block and prefix stored in the course block.
- Run the local probe:

  ```bash
  $ ccc system status
  ```

### The grader image fails to start

- Test the image outside CCC:

  ```bash
  $ docker run --rm <image:tag> --help
  ```

- Confirm the worker host can pull the image.

### Canvas uploads fail

- Re-run `ccc course setup` if the token changed.
- Confirm the course ID and token still match the target Canvas environment.

## Related Docs

- [Setting Up Prefect](02-setting-up-prefect.md)
- [Deploying Grader Tests to CCC](05-deploying-tests-to-ccc.md)
- [Configuration Reference](../reference/03-configuration.md)
