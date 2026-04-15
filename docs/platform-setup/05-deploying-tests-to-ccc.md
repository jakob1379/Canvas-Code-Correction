# Deploying Grader Tests to CCC

This guide covers the **current integration contract** between grader assets and
CCC:

- your **Docker image** provides the grading runtime
- your **assets block + assets prefix** point at grader files in S3-compatible storage
- the course block ties those together with Canvas and Prefect settings

## Try It Now

For local development with RustFS:

```bash
$ poe s3
$ poe rustfs-setup
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --course-id 12345 \
  --docker-image ghcr.io/example/cs101-grader:latest
```

Expected result:

```text
✓ Course configuration saved as block: ccc-course-12345-cs101
```

## What CCC Expects

CCC downloads grader assets from the configured bucket block and prefix into
`/workspace/assets`. The default grader command is:

```text
sh /workspace/assets/main.sh
```

That means your assets prefix should contain an executable `main.sh` plus any
supporting files your grader needs.

## Step 1: Build and Publish the Grader Image

Build the grader image from your grader repository:

```bash
$ docker build -t ghcr.io/example/cs101-grader:latest .
```

If workers need to pull the image from a registry, push it:

```bash
$ docker push ghcr.io/example/cs101-grader:latest
```

For authoring guidance, see
[Grader Image Guide](../reference/05-grader-image.md).

## Step 2: Put Assets in S3-Compatible Storage

Choose a bucket block and prefix, for example:

- block: `course-assets-cs101`
- prefix: `graders/cs101/`

Your uploaded assets should include at least:

```text
graders/cs101/
  main.sh
  tests/
  fixtures/
```

For local development, `poe rustfs-setup` creates the `local-rustfs` block and
verifies the test bucket. You still need to place your real grader assets under
the prefix you plan to use.

## Step 3: Configure the Course Block

Save the image and generated course settings into the course block:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --api-url https://canvas.example.edu \
  --course-id 12345 \
  --docker-image ghcr.io/example/cs101-grader:latest
```

The CLI generates the assets block, assets prefix, and work pool from the
Canvas course and saves them with the course block.

## Step 4: Create the Deployment and Start a Worker

```bash
$ ccc system deploy create ccc-course-12345-cs101
$ uv run prefect worker start --pool course-work-pool-cs101
```

The worker host must be able to:

- pull the grader image
- reach the S3-compatible endpoint
- talk to the Prefect API

## Step 5: Run a Dry Test

Run one submission without posting results:

```bash
$ ccc course run 98765 --course ccc-course-12345-cs101 --submission-id 54321 --dry-run
```

That confirms the image, assets, and runtime wiring are correct before you post
grades.

## Troubleshooting

### The grader cannot find `main.sh`

- Confirm the assets prefix really contains `main.sh`.
- Confirm the course block uses the same prefix you uploaded to.

### The worker cannot pull the image

- Test `docker pull <image:tag>` on the worker host.
- Add registry credentials if the image is private.

### Asset downloads fail

- Verify the assets block credentials.
- For local RustFS, rerun:

  ```bash
  $ poe rustfs-setup
  ```

## Related Docs

- [Configuring a Course](01-configuring-course.md)
- [Setting Up Prefect](02-setting-up-prefect.md)
- [RustFS Storage](07-rustfs-storage.md)
- [Grader Image Guide](../reference/05-grader-image.md)
