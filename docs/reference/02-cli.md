# CLI Reference

Use the `ccc` CLI to configure courses, run corrections, and operate the
webhook/deployment stack.

CCC groups commands by intent:

- `ccc course ...` for **course administration**
- `ccc system ...` for **platform operations**

Python requirement: **3.13+**.

## Try It Now

Run help to confirm the CLI is available:

```bash
$ ccc --help
```

Expected output (abbreviated):

```bash
Usage: ccc [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show version information
  --help     Show this message and exit

Commands:
  course  Course administration commands
  system  Platform administration commands
```

If you have not activated the environment created by `uv sync`, run commands
with `uv run`:

```bash
$ uv run ccc --help
```

## Command Groups

### Course Commands

Use course commands when you are configuring or grading a specific Canvas
course.

```bash
$ ccc course --help
```

Available subcommands:

- `setup` – guided setup (interactive by default)
- `run` – run corrections for an assignment or one submission
- `list` – list saved course config blocks

### System Commands

Use system commands when you are managing infrastructure, webhook serving, or
deployments.

```bash
$ ccc system --help
```

Available subcommands:

- `webhook serve` – start webhook API server
- `deploy create` – create/update a Prefect deployment for a course block
- `status` – show local platform health checks

## Course Commands

### `ccc course setup`

Use guided setup to collect required values in dependency order (token first,
then Canvas-derived data).

Usage:

```bash
$ ccc course setup [OPTIONS]
```

Key options:

| Option                           | Description                              | Default                          |
| -------------------------------- | ---------------------------------------- | -------------------------------- |
| `--token`, `-t`                  | Canvas API token                         | prompted in interactive mode     |
| `--token-stdin`                  | Read Canvas API token from stdin         | `false`                          |
| `--api-url`                      | Canvas base URL                          | `https://canvas.instructure.com` |
| `--course-id`, `-c`              | Skip interactive course selection        | interactive select               |
| `--assets-block`, `-a`           | Prefect S3 block name                    | prompted in interactive mode     |
| `--assets-prefix`, `-p`          | Asset path prefix                        | `""`                             |
| `--slug`, `-s`                   | Course slug used for block name          | inferred or prompted             |
| `--docker-image`, `-d`           | Grader image                             | optional                         |
| `--work-pool`, `-w`              | Prefect work pool name                   | optional                         |
| `--test-map`                     | Mapping `assignment_id:/path/to/test.py` | optional, repeatable             |
| `--env`, `-e`                    | Extra grader env values `KEY=VALUE`      | optional, repeatable             |
| `--interactive/--no-interactive` | Prompt for missing values                | interactive                      |

Example (non-interactive with stdin token):

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --course-id 12345 \
  --assets-block course-assets-cs101 \
  --slug cs101 \
  --test-map 59160606:/tests/assignment_1.py
```

Expected output (abbreviated):

```bash
Canvas API token validated successfully
Course ID 12345 validated
Course configuration saved as block: ccc-course-cs101
```

Common error example:

```bash
$ ccc course setup --no-interactive --course-id 12345 --assets-block course-assets-cs101
Error: --token or --token-stdin is required in non-interactive mode
```

### `ccc course run`

Run grading for one assignment (batch) or one submission.

Usage:

```bash
$ ccc course run <assignment-id> [OPTIONS]
```

Options:

| Option            | Description                      | Default          |
| ----------------- | -------------------------------- | ---------------- |
| `--submission-id` | Limit to one submission          | batch mode       |
| `--course`, `-c`  | Course block name                | `default-course` |
| `--download-dir`  | Directory for downloaded files   | temp directory   |
| `--dry-run`       | Skip grading upload side effects | `false`          |

Single-submission example:

```bash
$ ccc course run 12345 --submission-id 67890 --course ccc-course-cs101 --dry-run
```

Batch example:

```bash
$ ccc course run 12345 --course ccc-course-cs101
```

### `ccc course list`

List all configured course blocks:

```bash
$ ccc course list
```

Expected output is a table containing block name, Canvas course ID, grader
image, and assets block.

## System Commands

### `ccc system webhook serve`

Start the FastAPI webhook server.

```bash
$ ccc system webhook serve --host 127.0.0.1 --port 8080
```

Expected output (abbreviated):

```bash
Starting webhook server on 127.0.0.1:8080
```

### `ccc system deploy create`

Create or update a deployment for a configured course block.

```bash
$ ccc system deploy create ccc-course-cs101
```

Expected output (abbreviated):

```bash
Creating deployment for course block: ccc-course-cs101
Deployment '...' created/updated successfully
```

### `ccc system status`

Check local platform status (Prefect and RustFS probes).

```bash
$ ccc system status
```

Expected output includes `Prefect server` and `RustFS (S3)` health lines.

## Global Options

### `--version`

Print installed CLI version:

```bash
$ ccc --version
```

Expected output:

```bash
Canvas Code Correction 2.0.0a0
```

## Related Docs

- [Architecture Overview](01-architecture.md)
- [Configuration Reference](03-configuration.md)
- [Configuring a Course](../platform-setup/01-configuring-course.md)
- [Setting up Prefect](../platform-setup/02-setting-up-prefect.md)
