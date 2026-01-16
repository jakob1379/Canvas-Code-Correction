# Configuring a Course

> **Audience**: CCC platform operators **Prerequisites**: Grader Docker image
> built, grader tests uploaded to S3 storage, Prefect blocks created

Once you have a grader image and tests uploaded to storage, you need to
configure a course on CCC. This creates a Prefect block that stores
course-specific settings.

## Using the CCC CLI

The `ccc configure-course` command sets up a course. You'll need:

- Canvas API token
- Canvas course ID
- S3 bucket block name (Prefect block for assets)
- Docker image name (optional)

### Example

```bash
uv run ccc configure-course cs101 \
  --token YOUR_CANVAS_TOKEN \
  --course-id 12345 \
  --assets-block course-assets-cs101 \
  --docker-image yourusername/canvas-grader:latest \
  --s3-prefix graders/cs101/
```

### Options

- `--token`, `-t`: Canvas API token (will prompt if omitted)
- `--course-id`, `-i`: Canvas course numeric ID
- `--assets-block`, `-a`: Prefect S3 bucket block name (must exist)
- `--docker-image`, `-d`: Docker image for grading (defaults to base image)
- `--s3-prefix`, `-p`: Prefix within the S3 bucket where grader assets are
  stored
- `--env`, `-e`: Environment variables for the grader container (KEY=VALUE)

## Prefect Blocks

CCC uses Prefect blocks to store configuration securely. The command creates a
`ccc-course-<slug>` block. Ensure you have the required S3 bucket block created
beforehand (via Prefect UI or CLI).

## Verifying Configuration

List configured courses:

```bash
uv run ccc list-courses
```

This displays all course blocks.

Next, we'll set up Prefect deployments and workers.
