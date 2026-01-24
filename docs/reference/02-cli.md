# CLI Reference

Canvas Code Correction CLI

**Usage**:

```console
$ ccc [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `run-once`: Run correction flow for an assignment or...
* `configure-course`: Create or update a course configuration...
* `list-courses`: List all configured course blocks.
* `version`: Show version information.
* `webhook`
* `deploy`

## `ccc run-once`

Run correction flow for an assignment or specific submission.

**Usage**:

```console
$ ccc run-once [OPTIONS] ASSIGNMENT_ID
```

**Arguments**:

* `ASSIGNMENT_ID`: Canvas assignment ID  [required]

**Options**:

* `--submission-id INTEGER`: Specific submission ID (default: all submissions)
* `-c, --course TEXT`: Prefect course configuration block name  [default: default-course]
* `--download-dir PATH`: Directory for downloaded submissions (default: temporary directory)
* `--dry-run`: Skip actual grading and upload
* `--help`: Show this message and exit.

## `ccc configure-course`

Create or update a course configuration block.

**Usage**:

```console
$ ccc configure-course [OPTIONS] COURSE_SLUG
```

**Arguments**:

* `COURSE_SLUG`: Unique identifier for the course  [required]

**Options**:

* `-t, --token TEXT`: Canvas API token  [required]
* `-i, --course-id INTEGER`: Canvas course ID  [required]
* `-a, --assets-block TEXT`: Prefect S3 bucket block name for assets  [required]
* `--api-url TEXT`: Canvas instance URL  [default: https://canvas.instructure.com]
* `-p, --s3-prefix TEXT`: S3 prefix for grader assets
* `-d, --docker-image TEXT`: Docker image for grading
* `-w, --work-pool TEXT`: Prefect work pool name
* `--workspace-root PATH`: Root directory for workspaces
* `-e, --env TEXT`: Environment variables (KEY=VALUE)
* `--help`: Show this message and exit.

## `ccc list-courses`

List all configured course blocks.

**Usage**:

```console
$ ccc list-courses [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `ccc version`

Show version information.

**Usage**:

```console
$ ccc version [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `ccc webhook`

**Usage**:

```console
$ ccc webhook [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `serve`: Start webhook server for Canvas submissions.

### `ccc webhook serve`

Start webhook server for Canvas submissions.

**Usage**:

```console
$ ccc webhook serve [OPTIONS]
```

**Options**:

* `--host TEXT`: Host to bind  [default: 0.0.0.0]
* `--port INTEGER`: Port to bind  [default: 8080]
* `--help`: Show this message and exit.

## `ccc deploy`

**Usage**:

```console
$ ccc deploy [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create or update a Prefect deployment for...

### `ccc deploy create`

Create or update a Prefect deployment for webhook-triggered corrections.

**Usage**:

```console
$ ccc deploy create [OPTIONS] COURSE_BLOCK
```

**Arguments**:

* `COURSE_BLOCK`: Prefect course configuration block name  [required]

**Options**:

* `--help`: Show this message and exit.
