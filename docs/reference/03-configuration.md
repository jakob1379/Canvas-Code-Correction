# Configuration Reference

CCC configuration is stored in Prefect blocks and read at runtime by CLI
commands.

## Try It Now

Create a course block with the minimum required settings:

```bash
$ ccc course setup \
  --slug cs101 \
  --course-id 12345 \
  --assets-block course-assets-cs101
```

Secure non-interactive variant:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup \
  --token-stdin \
  --slug cs101 \
  --course-id 12345 \
  --assets-block course-assets-cs101
```

Expected output:

```bash
Course configuration saved as block: ccc-course-cs101
```

Verify the block exists:

```bash
$ ccc course list
```

## Configuration Model

CCC loads settings from `ccc-course-<slug>` blocks using
`Settings.from_course_block`.

The model is defined in `src/canvas_code_correction/config.py` and includes:

- **Canvas**: `api_url`, `token`, `course_id`
- **Assets**: `bucket_block`, `path_prefix`
- **Grader**: `docker_image`, `work_pool_name`, `env`
- **Workspace**: `root`
- **Webhook**: `secret`, `deployment_name`, `enabled`, `require_jwt`,
  `rate_limit`

## How You Configure It

### Guided setup (recommended first run)

```bash
$ ccc course setup
```

Use this when you want token validation, course discovery, and optional
assignment-to-test mapping.

### Direct setup (automation-friendly)

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup \
  --token-stdin \
  --slug cs101 \
  --course-id 12345 \
  --assets-block course-assets-cs101 \
  --s3-prefix graders/cs101/ \
  --docker-image yourusername/canvas-grader:latest \
  --work-pool course-work-pool-cs101 \
  --env DEBUG=true
```

## Environment Variables

CCC supports infrastructure and test environment variables.

### Core runtime

| Variable             | Purpose                       | Example                     |
| -------------------- | ----------------------------- | --------------------------- |
| `PREFECT_API_URL`    | Prefect API endpoint          | `http://localhost:4200/api` |
| `PREFECT_API_KEY`    | Prefect API key (if required) | `pnu_...`                   |
| `CCC_WORKSPACE_ROOT` | Workspace root directory      | `/tmp/ccc/workspaces`       |

### Canvas (mainly for tests/scripts)

| Variable                    | Purpose                             | Example                          |
| --------------------------- | ----------------------------------- | -------------------------------- |
| `CANVAS_API_URL`            | Canvas API URL                      | `https://canvas.instructure.com` |
| `CANVAS_API_TOKEN`          | Canvas API token                    | `7~...`                          |
| `CANVAS_COURSE_ID`          | Course ID used in test commands     | `13122436`                       |
| `CANVAS_TEST_ASSIGNMENT_ID` | Assignment ID for integration tests | `59160606`                       |

### RustFS / local S3-compatible storage

| Variable             | Default                 | Purpose         |
| -------------------- | ----------------------- | --------------- |
| `RUSTFS_ENDPOINT`    | `http://localhost:9000` | RustFS endpoint |
| `RUSTFS_ACCESS_KEY`  | `rustfsadmin`           | Access key      |
| `RUSTFS_SECRET_KEY`  | `rustfsadmin`           | Secret key      |
| `RUSTFS_BUCKET_NAME` | `test-assets`           | Bucket name     |
| `RUSTFS_PREFIX`      | `dev`                   | Asset prefix    |

Example shell setup:

```bash
$ export PREFECT_API_URL="http://localhost:4200/api"
$ export CANVAS_API_URL="https://canvas.instructure.com"
$ export CANVAS_API_TOKEN="your_token"
$ export CANVAS_COURSE_ID="12345"
```

## Common Errors

Missing required options during direct configuration:

```bash
$ ccc course setup --no-interactive --slug cs101 --assets-block course-assets-cs101
Error: --token or --token-stdin is required in non-interactive mode
```

Invalid Canvas token during setup:

```bash
$ ccc course setup --no-interactive --token invalid --course-id 12345 --assets-block course-assets-cs101
Error: Failed to validate Canvas API token
```

## Related Docs

- [CLI Reference](02-cli.md)
- [Configuring a Course](../platform-setup/01-configuring-course.md)
- [Setting up Prefect](../platform-setup/02-setting-up-prefect.md)
- [RustFS Storage](../platform-setup/07-rustfs-storage.md)
