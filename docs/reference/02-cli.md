# CLI Reference

CCC provides a command-line interface for configuring courses and running
corrections.

## Installation

After installing the package with `uv sync`, the `ccc` command is available via
`uv run ccc`.

## Commands

### `ccc run-once`

Run correction flow for an assignment or specific submission.

```bash
uv run ccc run-once <assignment-id> [OPTIONS]
```

**Arguments**:

- `assignment-id`: Canvas assignment ID (integer)

**Options**:

- `--submission-id`, `--submission`: Specific submission ID (default: all
  submissions)
- `--course`, `-c`: Prefect course configuration block name (default:
  "default-course")
- `--dry-run`: Skip actual grading and upload
- `--download-dir`: Directory for downloaded submissions (default: temporary
  directory)

**Examples**:

```bash
uv run ccc run-once 12345
uv run ccc run-once 12345 --submission-id 67890 --dry-run
```

### `ccc configure-course`

Create or update a course configuration block.

```bash
uv run ccc configure-course <course-slug> [OPTIONS]
```

**Arguments**:

- `course-slug`: Unique identifier for the course (string)

**Options**:

- `--token`, `-t`: Canvas API token (prompted if omitted)
- `--course-id`, `-i`: Canvas course ID (integer)
- `--assets-block`, `-a`: Prefect S3 bucket block name for assets
- `--docker-image`, `-d`: Docker image for grading (optional)
- `--s3-prefix`, `-p`: S3 prefix for grader assets (default: "")
- `--work-pool`, `-w`: Prefect work pool name (optional)
- `--env`, `-e`: Environment variables for grader (KEY=VALUE), repeatable

**Example**:

```bash
uv run ccc configure-course cs101 \
  --token $CANVAS_TOKEN \
  --course-id 12345 \
  --assets-block course-assets-cs101 \
  --docker-image mygrader:latest \
  --s3-prefix graders/cs101/
```

### `ccc list-courses`

List all configured course blocks.

```bash
uv run ccc list-courses
```

Displays a table with block name, Canvas course ID, Docker image, and assets
block.

### `ccc version`

Show version information.

```bash
uv run ccc version
```

## Environment Variables

CCC respects standard Prefect environment variables (`PREFECT_API_URL`,
`PREFECT_API_KEY`) and Canvas credentials can be passed via options or stored in
Prefect blocks.
