# CLI Reference

The `ccc` CLI has two top-level command groups:

- `ccc course` for **course-specific operations**
- `ccc system` for **platform operations**

Python requirement: **3.13+**.

## Try It Now

```bash
$ ccc --help
```

Expected output begins with:

```text
Usage: ccc [OPTIONS] COMMAND [ARGS]...
```

If you have not activated `.venv`, prefix commands with `uv run`.

## Top-Level Commands

### `ccc course`

Available subcommands:

- `setup`
- `run`
- `list`

### `ccc system`

Available subcommands:

- `webhook serve`
- `deploy create`
- `worker start`
- `status`

## `ccc course setup`

Creates a generated `ccc-course-<canvas-course-id>-<slugified-course-code>` Prefect block.

The repo also includes a ready-made local example grader at
`examples/count-submitted-files/`.

### Real flags

| Flag | Description | Default |
| --- | --- | --- |
| `--token` | Canvas token | prompt in interactive mode |
| `--token-stdin` | Read the Canvas token from stdin | disabled |
| `--api-url`, `-u` | Canvas base URL | `https://canvas.instructure.com` |
| `--course-id`, `-c` | Canvas course ID | interactive selection |
| `--docker-image`, `-d` | Grader image | `jakob1379/canvas-grader:latest` |
| `--work-package`, `--map-assignments` | Assignment-to-work-package mapping in `assignment_id:path` form. Use the work package root directory, the folder that contains `grader/` or `assets/`, for example `59160606:/path/to/my-work-package`. During setup, CCC records the assignment ID in that package's `work-package.yaml`, creates the generated course bucket, saves the Prefect `S3Bucket` block, and uploads the package's asset directory to `assignments/<assignment id>`. | repeatable |
| `--env`, `-e` | Extra grader env in `KEY=VALUE` form | repeatable |
| `--interactive` | Force prompts | enabled |
| `--no-interactive` | Disable prompts | disabled |

Generated values:

- block name: `ccc-course-<course-id>-<slugified-course-code>`
- assets block: `ccc-assets-<course-id>-<slugified-course-code>`
- assets prefix: `graders/<course-id>-<slugified-course-code>/`
- work pool: `course-work-pool-<course-id>-<slugified-course-code>`

### Example

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --api-url https://canvas.example.edu \
  --course-id 12345 \
  --docker-image ghcr.io/example/cs101-grader:latest \
  --work-package 59160606:/path/to/my-work-package \
  --env PYTHONUNBUFFERED=1
```

### Common error

```bash
$ ccc course setup --no-interactive --course-id 12345
```

Expected output:

```text
--token or --token-stdin is required in non-interactive mode
```

## `ccc course run`

Runs corrections for one assignment or one submission.

### Real flags

| Flag | Description | Default |
| --- | --- | --- |
| `ASSIGNMENT_ID` | Canvas assignment ID | required |
| `--submission-id` | Limit the run to one submission | batch mode |
| `--course`, `-c` | Course block name | `default-course` |
| `--download-dir` | Directory for downloaded files | temporary directory |
| `--dry-run` | Skip upload side effects | disabled |

### Examples

Batch run:

```bash
$ ccc course run 98765 --course ccc-course-cs101
```

Single submission:

```bash
$ ccc course run 98765 --course ccc-course-cs101 --submission-id 54321 --dry-run
```

## `ccc course list`

Lists configured course blocks.

```bash
$ ccc course list
```

Expected output is a table containing block name, Canvas course ID, grader
image, assets block, and storage auth mode.

## `ccc system webhook serve`

Starts the FastAPI webhook server.

```bash
$ ccc system webhook serve --host 127.0.0.1 --port 8080
```

Expected output:

```text
Starting webhook server on 127.0.0.1:8080
```

## `ccc system deploy create`

Creates or updates the built-in webhook deployment for a course block.

```bash
$ ccc system deploy create ccc-course-cs101
```

Expected output includes:

```text
Creating deployment for course block: ccc-course-cs101
Deployment 'ccc-cs101-deployment' created/updated successfully
```

## `ccc system status`

Checks local Prefect and RustFS connectivity.

```bash
$ ccc system status
```

Expected output contains health lines for:

- `Prefect server`
- `RustFS (S3)`

## `ccc system worker start`

Starts a course-scoped Prefect worker on the work pool named in that course's
configuration. For `shared_environment` courses it mirrors any `RUSTFS_*`
credentials in the environment into the `AWS_*` names boto3 reads; if none are
set it changes nothing, leaving IAM roles and `~/.aws` profiles intact.

```bash
$ ccc system worker start --course ccc-course-cs101
```

Expected output begins with:

```text
Mirrored RUSTFS_* credentials into AWS_* for the worker
Starting Prefect worker for pool: course-work-pool-cs101
```

## Global Option

### `--version`

```bash
$ ccc --version
```

Expected output:

```text
Canvas Code Correction 2.0.0a0
```

## Related Docs

- [Configuration Reference](03-configuration.md)
- [Configuring a Course](../platform-setup/01-configuring-course.md)
- [Setting Up Prefect](../platform-setup/02-setting-up-prefect.md)
