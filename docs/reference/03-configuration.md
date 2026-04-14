# Configuration Reference

CCC loads runtime configuration from **Prefect course blocks** and a small set
of environment variables.

## Try It Now

Create a course block:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --api-url https://canvas.example.edu \
  --course-id 12345 \
  --slug cs101 \
  --assets-block course-assets-cs101 \
  --assets-prefix graders/cs101/ \
  --docker-image ghcr.io/example/cs101-grader:latest \
  --work-pool course-work-pool-cs101
```

Verify it:

```bash
$ ccc course list
```

## Runtime Loading Path

CCC turns a `ccc-course-<slug>` block into runtime settings with:

- `canvas_code_correction.bootstrap.load_course_block`
- `canvas_code_correction.bootstrap.load_settings_from_course_block`

The runtime model itself lives in `src/canvas_code_correction/config.py`.

## Runtime Settings Model

### Canvas

- `api_url`
- `token`
- `course_id`

### Assets

- `bucket_block`
- `path_prefix`

### Grader

- `docker_image`
- `work_pool_name`
- `env`
- `command`
- `timeout_seconds`
- `memory_mb`
- `upload_check_duplicates`
- `upload_comments`
- `upload_grades`
- `upload_verbose`

### Workspace

- `root`

### Webhook

- `secret`
- `deployment_name`
- `enabled`
- `require_jwt`
- `rate_limit`
- `allow_canvas_api_fallback`

## Persisted Course Block Fields

The `CourseConfigBlock` in
`src/canvas_code_correction/prefect_blocks/canvas.py` persists these important
fields:

- `canvas_api_url`
- `canvas_token`
- `canvas_course_id`
- `asset_bucket_block`
- `asset_path_prefix`
- `grader_image`
- `work_pool_name`
- `grader_env`
- webhook fields such as `deployment_name`, `webhook_enabled`, and
  `webhook_rate_limit`

## CLI-to-Block Mapping

`ccc course setup` populates these key fields:

| CLI flag | Stored field |
| --- | --- |
| `--api-url` | `canvas_api_url` |
| `--course-id` | `canvas_course_id` |
| `--assets-block` | `asset_bucket_block` |
| `--assets-prefix` | `asset_path_prefix` |
| `--docker-image` | `grader_image` |
| `--work-pool` | `work_pool_name` |
| `--env` | `grader_env` |

## Environment Variables

### Prefect

| Variable | Purpose | Example |
| --- | --- | --- |
| `PREFECT_API_URL` | Prefect API endpoint | `http://localhost:4200/api` |
| `PREFECT_API_KEY` | Prefect API key when required | `pnu_...` |

### Canvas and tests

| Variable | Purpose | Example |
| --- | --- | --- |
| `CANVAS_API_URL` | Canvas base URL | `https://canvas.instructure.com` |
| `CANVAS_API_TOKEN` | Canvas API token | `7~...` |
| `CANVAS_COURSE_ID` | Test or local course ID | `12345` |
| `CANVAS_TEST_ASSIGNMENT_ID` | Integration-test assignment ID | `59160606` |

### Workspace

| Variable | Purpose | Example |
| --- | --- | --- |
| `CCC_WORKSPACE_ROOT` | Override workspace root | `/tmp/ccc/workspaces` |

### RustFS / S3-compatible storage

| Variable | Default | Purpose |
| --- | --- | --- |
| `RUSTFS_ENDPOINT` | `http://localhost:9000` | S3 endpoint |
| `RUSTFS_ACCESS_KEY` | `rustfsadmin` | Access key |
| `RUSTFS_SECRET_KEY` | `rustfsadmin` | Secret key |
| `RUSTFS_BUCKET_NAME` | `test-assets` | Bucket name |
| `RUSTFS_PREFIX` | `dev` | Prefix used by `poe rustfs-setup` |

## Known Gap

`allow_canvas_api_fallback` exists in the runtime `WebhookSettings` model, but
it is **not** currently exposed by `ccc course setup` or persisted on the
course block. Treat it as an internal runtime field unless that persistence path
is added.

## Common Errors

Missing token:

```bash
$ ccc course setup --no-interactive --slug cs101 --assets-block course-assets-cs101
```

Expected output:

```text
--token or --token-stdin is required in non-interactive mode
```

Invalid Canvas credentials:

```bash
$ ccc course setup --no-interactive --token invalid --course-id 12345 --assets-block course-assets-cs101
```

Expected output begins with:

```text
Error: Failed to validate Canvas credentials
```

## Related Docs

- [CLI Reference](02-cli.md)
- [Configuring a Course](../platform-setup/01-configuring-course.md)
- [RustFS Storage](../platform-setup/07-rustfs-storage.md)
