# Configuration Reference

Configure Canvas Code Correction via environment variables or a TOML file.

## Quick Start

Create a `.env` file in your project root with the minimum required settings:

```bash
# .env
CANVAS_API_URL=https://canvas.instructure.com
CANVAS_API_TOKEN=your_canvas_api_token_here
CANVAS_COURSE_ID=123456
CCC_WORKING_DIR=/tmp/ccc/runs
```

Then run any `ccc` command – the application will automatically load these
variables.

**Expected output when configuration is loaded:**

```bash
$ ccc --help
Canvas Code Correction CLI (v2.0.0)

Usage: ccc [OPTIONS] COMMAND [ARGS]...

  ...
```

If you see the help screen, your environment variables are being read correctly.

## Configuration Sources

Canvas Code Correction reads configuration from three sources, in order of
precedence:

1. **Command‑line arguments** – highest priority (e.g., `--config custom.toml`)
2. **Environment variables** – convenient for development and deployment
3. **TOML configuration file** – recommended for production and team sharing

The settings are merged into a single `Settings` object defined in
`canvas_code_correction.config`.

### Environment Variables

Set any of the variables listed below in your shell or in a `.env` file
(auto‑loaded by the CLI). Example for bash:

```bash
export CANVAS_API_URL=https://your.instructure.com
export CANVAS_API_TOKEN=secret_token_here
export CANVAS_COURSE_ID=98765
```

### TOML Configuration File

Create a `settings.toml` file with the same structure as the `Settings` model.
Pass it to the CLI with `ccc --config path/to/settings.toml`.

```toml
# settings.toml
[canvas]
api_url = "https://canvas.instructure.com"
token = "your_canvas_api_token_here"
course_id = 123456

[assets]
block_name = "course-assets"
bucket = "course-assets"
prefix = "graders/course-slug/"

[runner]
docker_image = "python:3.13-slim"
network_disabled = false
memory_limit = "1g"
cpu_limit = 1.0

[workspace]
root = "/tmp/ccc/workspaces"

[webhook]
enabled = true
secret = "optional_jwt_secret"
require_jwt = false
rate_limit = "10/minute"
```

## Configuration Options

The following table lists every configuration key, its corresponding environment
variable, a brief description, the default value (if any), and a concrete
example.

| Key                                     | Environment Variable                                  | Description                                                       | Default                                  | Example                                      |
| --------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------- | -------------------------------------------- |
| **Canvas API Settings**                 |                                                       |                                                                   |                                          |                                              |
| `canvas.api_url`                        | `CANVAS_API_URL`                                      | Base URL of your Canvas instance.                                 | `https://canvas.instructure.com`         | `https://your‑school.instructure.com`        |
| `canvas.token`                          | `CANVAS_API_TOKEN`                                    | API token with permissions to read submissions and post grades.   | _(required)_                             | `"1~AbCdEf..."`                              |
| `canvas.course_id`                      | `CANVAS_COURSE_ID`                                    | Numeric ID of the Canvas course.                                  | _(required)_                             | `123456`                                     |
| **Runner (Grading Container) Settings** |                                                       |                                                                   |                                          |                                              |
| `runner.docker_image`                   | `CCC_RUNNER_IMAGE`<br>`CCC_GRADER_IMAGE`              | Docker image used to execute grading jobs.                        | `None` (uses default from Prefect block) | `"python:3.13‑slim"`                         |
| `runner.network_disabled`               | `CCC_RUNNER_NETWORK_DISABLED`                         | Disable network access inside the grading container.              | `false`                                  | `true`                                       |
| `runner.memory_limit`                   | `CCC_RUNNER_MEMORY_LIMIT`                             | Memory limit for the container (supports `g`, `m`, `k` suffixes). | `None` (no limit)                        | `"2g"`                                       |
| `runner.cpu_limit`                      | `CCC_RUNNER_CPU_LIMIT`                                | CPU quota for the container (float).                              | `None` (no limit)                        | `1.5`                                        |
| **Asset Storage Settings**              |                                                       |                                                                   |                                          |                                              |
| `assets.block_name`                     | `CCC_ASSETS_BLOCK`                                    | Name of the Prefect S3 block that stores grader assets.           | `""`                                     | `"course‑assets"`                            |
| `assets.bucket`                         | `CCC_ASSETS_S3_BUCKET`                                | S3 bucket containing grader tests and fixtures.                   | `""`                                     | `"course‑assets"`                            |
| `assets.prefix`                         | `CCC_ASSETS_S3_PREFIX`                                | Prefix (folder) inside the bucket that scopes course assets.      | `""`                                     | `"graders/course‑slug/"`                     |
| `assets.endpoint_url`                   | `CCC_ASSETS_S3_ENDPOINT`                              | Custom S3‑compatible endpoint (e.g., RustFS, MinIO).              | `https://s3.amazonaws.com`               | `"http://localhost:9000"`                    |
| `assets.region`                         | `CCC_ASSETS_S3_REGION`                                | AWS region for the bucket (ignored for custom endpoints).         | `None`                                   | `"us‑east‑1"`                                |
| `assets.use_ssl`                        | `CCC_ASSETS_S3_SSL`                                   | Whether to use HTTPS for the S3 client.                           | `true`                                   | `false`                                      |
| `assets.verify_ssl`                     | `CCC_ASSETS_S3_VERIFY`                                | Whether to verify TLS certificates.                               | `true`                                   | `false`                                      |
| `assets.access_key`                     | `CCC_ASSETS_S3_ACCESS_KEY`<br>`AWS_ACCESS_KEY_ID`     | S3 access key (overrides AWS credentials).                        | `None`                                   | `"AKIAIOSFODNN7EXAMPLE"`                     |
| `assets.secret_key`                     | `CCC_ASSETS_S3_SECRET_KEY`<br>`AWS_SECRET_ACCESS_KEY` | S3 secret key (overrides AWS credentials).                        | `None`                                   | `"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"` |
| `assets.session_token`                  | `CCC_ASSETS_S3_SESSION_TOKEN`<br>`AWS_SESSION_TOKEN`  | Session token for temporary credentials.                          | `None`                                   | `"AQoEXAMPLE..."`                            |
| **Workspace Settings**                  |                                                       |                                                                   |                                          |                                              |
| `working_dir`                           | `CCC_WORKING_DIR`                                     | Root directory for temporary run workspaces.                      | `/tmp/ccc/runs`                          | `"/var/lib/ccc/workspaces"`                  |
| `workspace.root`                        | `CCC_WORKSPACE_ROOT`                                  | Root directory for persistent course workspaces.                  | `/tmp/ccc/workspaces`                    | `"/var/lib/ccc/workspaces"`                  |

!!! note
    The `webhook` section (secret, deployment name, rate limiting) is also configurable via the same
    sources. See the `Settings` model in `canvas_code_correction.config` for all available fields.

## RustFS Integration (Local Development)

For local development and testing, Canvas Code Correction can use a RustFS
S3‑compatible storage server. The `setup‑rustfs.py` script expects the following
environment variables:

| Environment Variable | Default Value           | Description                              |
| -------------------- | ----------------------- | ---------------------------------------- |
| `RUSTFS_ENDPOINT`    | `http://localhost:9000` | RustFS S3 endpoint URL                   |
| `RUSTFS_ACCESS_KEY`  | `rustfsadmin`           | Access key for RustFS                    |
| `RUSTFS_SECRET_KEY`  | `rustfsadmin`           | Secret key for RustFS                    |
| `RUSTFS_BUCKET_NAME` | `test‑assets`           | Bucket name for test assets              |
| `RUSTFS_PREFIX`      | `dev`                   | Path prefix for assets within the bucket |

The main application uses the standard S3 configuration variables
(`CCC_ASSETS_S3_ENDPOINT`, `CCC_ASSETS_S3_ACCESS_KEY`, etc.) – you can point
them to RustFS or any other S3‑compatible service.

**Example .env snippet for RustFS:**

```bash
CCC_ASSETS_S3_ENDPOINT=http://localhost:9000
CCC_ASSETS_S3_ACCESS_KEY=rustfsadmin
CCC_ASSETS_S3_SECRET_KEY=rustfsadmin
CCC_ASSETS_S3_BUCKET=test-assets
CCC_ASSETS_S3_PREFIX=dev
```

## Advanced Configuration

### Using a TOML File

A TOML configuration file is the recommended way to store settings for
production deployments and team collaboration. The file must mirror the
structure of the `Settings` Pydantic model.

```toml
# settings.toml
[canvas]
api_url = "https://canvas.instructure.com"
token = "your_canvas_api_token_here"
course_id = 123456

[assets]
block_name = "course-assets"
bucket = "course-assets"
prefix = "graders/course-slug/"
endpoint_url = "https://s3.amazonaws.com"
region = "us-east-1"
use_ssl = true
verify_ssl = true

[runner]
docker_image = "python:3.13-slim"
network_disabled = false
memory_limit = "1g"
cpu_limit = 1.0

[workspace]
root = "/tmp/ccc/workspaces"

[webhook]
enabled = true
secret = "optional_jwt_secret"
require_jwt = false
rate_limit = "10/minute"
```

Load the file with:

```bash
$ ccc --config settings.toml configure-course --slug my-course
```

### Precedence Rules

When the same setting appears in multiple sources, the highest‑priority source
wins:

1. **Command‑line arguments** (e.g., `--config`, `--course‑id`)
2. **Environment variables** (set in shell or `.env`)
3. **TOML configuration file** (if provided)
4. **Defaults** from the `Settings` model

For example, if `CANVAS_API_URL` is set in the environment and also specified in
`settings.toml`, the environment variable takes precedence.

### Validation and Errors

The configuration is validated with Pydantic when the application starts. If a
required field is missing or a value is invalid, you’ll see an error like:

```bash
$ ccc configure-course --slug my-course
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
canvas.token
  Field required [type=missing, input_value={}, input_type=dict]
```

Check the error message for the exact field that needs correction.
