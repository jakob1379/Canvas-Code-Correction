# Configuration Reference

The project reads configuration from environment variables or a TOML file parsed
into `Settings`:

| Key                       | Environment Variable                                 | Description                                                |
| ------------------------- | ---------------------------------------------------- | ---------------------------------------------------------- |
| `canvas.api_url`          | `CANVAS_API_URL`                                     | Base URL for the Canvas instance.                          |
| `canvas.token`            | `CANVAS_API_TOKEN`                                   | API token with rights to read submissions and post grades. |
| `canvas.course_id`        | `CANVAS_COURSE_ID`                                   | Numeric identifier of the Canvas course.                   |
| `runner.docker_image`     | `CCC_RUNNER_IMAGE` / `CCC_GRADER_IMAGE`              | Docker image used to run grading jobs.                     |
| `runner.network_disabled` | `CCC_RUNNER_NETWORK_DISABLED`                        | Disable network inside grading container.                  |
| `runner.memory_limit`     | `CCC_RUNNER_MEMORY_LIMIT`                            | Container memory limit (e.g., `1g`).                       |
| `runner.cpu_limit`        | `CCC_RUNNER_CPU_LIMIT`                               | CPU quota for the container.                               |
| `assets.block_name`       | `CCC_ASSETS_BLOCK`                                   | Prefect S3 block name that stores grader assets.           |
| `assets.bucket`           | `CCC_ASSETS_S3_BUCKET`                               | S3 bucket that contains grader tests and fixtures.         |
| `assets.prefix`           | `CCC_ASSETS_S3_PREFIX`                               | Prefix (folder) within the bucket to scope course assets.  |
| `assets.endpoint_url`     | `CCC_ASSETS_S3_ENDPOINT`                             | Optional custom S3 endpoint (useful for MinIO).            |
| `assets.region`           | `CCC_ASSETS_S3_REGION`                               | Region for AWS-hosted buckets.                             |
| `assets.use_ssl`          | `CCC_ASSETS_S3_SSL`                                  | Whether to use HTTPS for the S3 client.                    |
| `assets.verify_ssl`       | `CCC_ASSETS_S3_VERIFY`                               | Whether to verify TLS certificates.                        |
| `assets.access_key`       | `CCC_ASSETS_S3_ACCESS_KEY` / `AWS_ACCESS_KEY_ID`     | Optional S3 access key override.                           |
| `assets.secret_key`       | `CCC_ASSETS_S3_SECRET_KEY` / `AWS_SECRET_ACCESS_KEY` | Optional S3 secret key override.                           |
| `assets.session_token`    | `CCC_ASSETS_S3_SESSION_TOKEN` / `AWS_SESSION_TOKEN`  | Optional session token for temporary credentials.          |
| `working_dir`             | `CCC_WORKING_DIR`                                    | Root directory for temporary run workspaces.               |

Configuration files can be supplied via `ccc --config path/to/settings.toml` and
must follow the same structure as the `Settings` model defined in
`canvas_code_correction.config`.

### RustFS Integration

For local development and testing with RustFS S3-compatible storage, use the
following environment variables with the `setup-rustfs.py` script:

| Environment Variable | Default Value           | Description                              |
| -------------------- | ----------------------- | ---------------------------------------- |
| `RUSTFS_ENDPOINT`    | `http://localhost:9000` | RustFS S3 endpoint URL                   |
| `RUSTFS_ACCESS_KEY`  | `rustfsadmin`           | Access key for RustFS                    |
| `RUSTFS_SECRET_KEY`  | `rustfsadmin`           | Secret key for RustFS                    |
| `RUSTFS_BUCKET_NAME` | `test-assets`           | Bucket name for test assets              |
| `RUSTFS_PREFIX`      | `dev`                   | Path prefix for assets within the bucket |

The main application uses the standard S3 configuration variables
(`CCC_ASSETS_S3_ENDPOINT`, `CCC_ASSETS_S3_ACCESS_KEY`, etc.) which can point to
RustFS or any S3-compatible service.
