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

## Important Note About Help Output

`ccc course setup` and `ccc course run` accept additional options that are
parsed after the Typer entrypoint. That means `--help` only shows the top-level
subcommand help, not every course-specific flag. The flag list below reflects
the actual parser in `src/canvas_code_correction/cli_course.py`.

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
- `status`

## `ccc course setup`

Creates or updates a `ccc-course-<slug>` Prefect block.

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
| `--map-assignments`, `--test-map` | Assignment-to-test mapping | repeatable |
| `--env`, `-e` | Extra grader env in `KEY=VALUE` form | repeatable |
| `--interactive` | Force prompts | enabled |
| `--no-interactive` | Disable prompts | disabled |
| `--assets-block` | Assets block name | prompt in interactive mode |
| `--slug` | Course slug | inferred or prompted |
| `--assets-prefix` | Assets prefix inside the bucket | `graders/<slug>/` |
| `--work-pool` | Prefect work pool name | `course-work-pool-<slug>` |

### Example

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --api-url https://canvas.example.edu \
  --course-id 12345 \
  --slug cs101 \
  --assets-block course-assets-cs101 \
  --assets-prefix graders/cs101/ \
  --docker-image ghcr.io/example/cs101-grader:latest \
  --work-pool course-work-pool-cs101 \
  --env PYTHONUNBUFFERED=1
```

### Common error

```bash
$ ccc course setup --no-interactive --course-id 12345 --assets-block course-assets-cs101
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
image, and assets block.

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
