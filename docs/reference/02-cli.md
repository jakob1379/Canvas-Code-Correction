# CLI Reference

Canvas Code Correction provides a command-line interface for configuring
courses, running corrections, and managing webhook deployments. The CLI is built
with **Typer** and offers rich help via `--help` flags.

## Accessing the CLI

After installing the package with `uv sync`, the `ccc` command is available via
`ccc`. You can also install the package globally, but using `uv run` ensures the
correct environment.

**Quick start:** Run the help command to see all available commands:

```bash
$ ccc --help
```

Expected output:

```
Canvas Code Correction CLI

Usage: ccc [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  configure-course  Create or update a course configuration block.
  deploy            Manage Prefect deployments.
  list-courses      List all configured course blocks.
  run-once          Run correction flow for an assignment or specific...
  version           Show version information.
  webhook           Manage webhook server.
```

## Commands

### `run-once`

Run correction flow for an assignment or specific submission.

**Usage:**

```bash
ccc run-once <assignment-id> [OPTIONS]
```

**Arguments:**

| Name            | Description                    | Required |
| --------------- | ------------------------------ | -------- |
| `assignment-id` | Canvas assignment ID (integer) | Yes      |

**Options:**

| Flag                              | Description                                                         | Default            |
| --------------------------------- | ------------------------------------------------------------------- | ------------------ |
| `--submission-id`, `--submission` | Specific submission ID (default: all submissions)                   | `None`             |
| `--course`, `-c`                  | Prefect course configuration block name                             | `"default-course"` |
| `--dry-run`                       | Skip actual grading and upload                                      | `False`            |
| `--download-dir`                  | Directory for downloaded submissions (default: temporary directory) | `None`             |

**Example – process a single submission:**

```bash
$ ccc run-once 12345 --submission-id 67890 --dry-run
```

Expected output:

```
[blue]Running correction for assignment 12345, submission 67890[/blue]
[yellow]Dry run enabled - no actual grading or upload will occur[/yellow]
[green]Correction flow completed successfully![/green]
{
  "submission_metadata_keys": ["67890"],
  "downloaded_files_count": 2,
  "workspace": "/tmp/ccc-download-abc123",
  "results_keys": ["score", "feedback"]
}
```

**Example – batch process all submissions:**

```bash
$ ccc run-once 12345
```

Expected output:

```
[blue]Batch mode: processing all submissions for assignment 12345[/blue]
[blue]Processing submission 67890[/blue]
[green]Submission 67890 processed successfully[/green]
[blue]Processing submission 67891[/blue]
[green]Submission 67891 processed successfully[/green]
[green]Batch processing completed![/green]
```

**Notes:**

- If `--download-dir` is omitted, a temporary directory is created and its path
  is printed.
- In batch mode, errors for individual submissions are logged but processing
  continues.

---

### `configure-course`

Create or update a course configuration block.

**Usage:**

```bash
ccc configure-course <course-slug> [OPTIONS]
```

**Arguments:**

| Name          | Description                               | Required |
| ------------- | ----------------------------------------- | -------- |
| `course-slug` | Unique identifier for the course (string) | Yes      |

**Options:**

| Flag                   | Description                                   | Default                            |
| ---------------------- | --------------------------------------------- | ---------------------------------- |
| `--token`, `-t`        | Canvas API token (prompted if omitted)        | Prompted                           |
| `--course-id`, `-i`    | Canvas course ID (integer)                    | (required)                         |
| `--assets-block`, `-a` | Prefect S3 bucket block name for assets       | (required)                         |
| `--api-url`            | Canvas instance URL                           | `"https://canvas.instructure.com"` |
| `--s3-prefix`, `-p`    | S3 prefix for grader assets                   | `""`                               |
| `--docker-image`, `-d` | Docker image for grading                      | `None`                             |
| `--work-pool`, `-w`    | Prefect work pool name                        | `None`                             |
| `--workspace-root`     | Root directory for workspaces                 | `None`                             |
| `--env`, `-e`          | Environment variables (KEY=VALUE), repeatable | `None`                             |

**Example – configure a new course:**

```bash
$ ccc configure-course cs101 \
  --token $CANVAS_TOKEN \
  --course-id 12345 \
  --assets-block course-assets-cs101 \
  --docker-image mygrader:latest \
  --s3-prefix graders/cs101/ \
  --env DEBUG=true \
  --env TIMEOUT=300
```

Expected output:

```
Course configuration saved as block: ccc-course-cs101
```

**Example – error when required options are missing:**

```bash
$ ccc configure-course cs101 --course-id 12345
```

Expected output:

```
Error: Missing option '--assets-block' / '-a'.
```

**Notes:**

- The block name is automatically prefixed with `ccc-course-`.
- Environment variables are passed to the grader container.

---

### `list-courses`

List all configured course blocks.

**Usage:**

```bash
ccc list-courses
```

**Arguments:** None

**Options:** None

**Example:**

```bash
$ ccc list-courses
```

Expected output:

```
              Configured Courses
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Block Name    ┃ Canvas Course ID ┃ Docker Image ┃ Assets Block ┃
┣━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━━┫
┃ ccc-course-cs101 ┃ 12345          ┃ mygrader:latest ┃ course-assets-cs101 ┃
┃ ccc-course-math202 ┃ 67890         ┃ Not set    ┃ course-assets-math ┃
┗━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━━━┛
```

**Notes:**

- Blocks that fail to load are shown with an error message in the table.

---

### `webhook serve`

Start webhook server for Canvas submissions.

**Usage:**

```bash
ccc webhook serve [OPTIONS]
```

**Arguments:** None

**Options:**

| Flag     | Description  | Default     |
| -------- | ------------ | ----------- |
| `--host` | Host to bind | `"0.0.0.0"` |
| `--port` | Port to bind | `8080`      |

**Example – start server on localhost:8080:**

```bash
$ ccc webhook serve --host 127.0.0.1 --port 8080
```

Expected output:

```
[blue]Starting webhook server on 127.0.0.1:8080[/blue]
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

**Notes:**

- The server uses the FastAPI application defined in the webhook module.
- Ensure the appropriate course blocks are configured before using webhooks.

---

### `deploy create`

Create or update a Prefect deployment for webhook-triggered corrections.

**Usage:**

```bash
ccc deploy create <course-block> [OPTIONS]
```

**Arguments:**

| Name           | Description                             | Required |
| -------------- | --------------------------------------- | -------- |
| `course-block` | Prefect course configuration block name | Yes      |

**Options:** None

**Example – create deployment for a course block:**

```bash
$ ccc deploy create ccc-course-cs101
```

Expected output:

```
[blue]Creating deployment for course block: ccc-course-cs101[/blue]
[green]Deployment 'ccc-cs101-deployment' created/updated successfully[/green]
[yellow]Note: Ensure work pool 'local-pool' exists and has workers[/yellow]
```

**Notes:**

- The deployment name is derived from the course slug (removing the
  `ccc-course-` prefix).
- The deployment is registered with Prefect and can be triggered via webhooks.

---

### `version`

Show version information.

**Usage:**

```bash
ccc version
```

**Arguments:** None

**Options:** None

**Example:**

```bash
$ ccc version
```

Expected output:

```
Canvas Code Correction v2.0.0a0
```

**Notes:**

- Version is read from the package metadata, or defaults to `v2.0.0a0` if not
  found.

---

## Environment Variables

CCC respects standard Prefect environment variables (`PREFECT_API_URL`,
`PREFECT_API_KEY`). Canvas credentials can be passed via options or stored in
Prefect blocks.

| Variable             | Purpose                       | Default                 |
| -------------------- | ----------------------------- | ----------------------- |
| `PREFECT_API_URL`    | Prefect API URL               | `http://127.0.0.1:4200` |
| `PREFECT_API_KEY`    | Prefect API key               | None                    |
| `CCC_WORKSPACE_ROOT` | Root directory for workspaces | `/tmp/ccc/workspaces`   |

**Example – set environment variables before running commands:**

```bash
export PREFECT_API_URL="http://localhost:4200"
export PREFECT_API_KEY="your-api-key"
ccc list-courses
```

## Getting Help

Every command supports a `--help` flag that provides detailed usage information.
For example:

```bash
$ ccc configure-course --help
```

This will show the command’s arguments, options, and a brief description.
