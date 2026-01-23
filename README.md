<p align="center">
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/jakob1379/canvas-code-correction/actions/workflows/test.yml/badge.svg)](https://github.com/jakob1379/canvas-code-correction/actions)
[![Coverage](https://img.shields.io/endpoint?url=https://jakob1379.github.io/canvas-code-correction/badges/coverage.json)](https://jakob1379.github.io/canvas-code-correction/htmlcov/)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-jakob1379%2FCanvas--Code--Correction-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==)](https://deepwiki.com/jakob1379/Canvas-Code-Correction)
</p>

# Canvas Code Correction

**Modern orchestration for downloading, grading, and uploading Canvas
submissions using Prefect, Docker, and reproducible local workspaces.**

## Try It Now (60 Seconds)

Copy and run these commands to install CCC and verify it works:

```bash
# Clone the repository
git clone https://github.com/jakob1379/canvas-code-correction.git
cd canvas-code-correction

# Install dependencies with uv (Python 3.13+)
uv sync

# Activate the virtual environment
source .venv/bin/activate

# Verify the CLI is ready
ccc --help
```

**Note:** All commands assume you have activated the virtual environment created
by `uv sync`. If you haven't activated it, prefix commands with `uv run`. This
example shows activation via `source .venv/bin/activate`; you can also use
`uv shell` or prefix individual commands with `uv run`.

You’ll see:

```
Usage: ccc [OPTIONS] COMMAND [ARGS]...

  Canvas Code Correction CLI.

Options:
  --help  Show this message and exit.

Commands:
  configure-course  Create or update a course configuration block.
  deploy            Manage Prefect deployments.
  list-courses      List all configured courses.
  run-once          Run a correction for a single assignment.
  webhook           Start the Canvas webhook server.
```

If you see the help text, **CCC is installed and ready**. The next step is to
configure your first course.

## Quick Tutorial (5 Minutes)

This tutorial walks you through setting up CCC and grading your first
assignment. You’ll need:

- **Canvas API token** with sufficient permissions
- **Canvas course ID** (numeric)
- **Docker** (for running grader containers)

### 1. Configure Your First Course

Use `ccc configure-course` to create a course configuration block. The
configuration is stored as a Prefect block and can be reused across runs.

```bash
ccc configure-course cs101 \
  --token YOUR_CANVAS_TOKEN \
  --course-id 12345 \
  --assets-block course-assets-cs101 \
  --docker-image yourusername/canvas-grader:latest \
  --s3-prefix graders/cs101/
```

**What this does:**

- Creates a Prefect block named `ccc-course-cs101`
- Stores your Canvas token, course ID, and grader image reference
- Links to an S3 bucket block (`course-assets-cs101`) for grader assets

If you omit `--token`, you’ll be prompted to enter it securely.

**Verify the configuration:**

```bash
ccc list-courses
```

Expected output:

```
Configured courses:
- cs101 (course ID: 12345, image: yourusername/canvas-grader:latest)
```

### 2. Run a Correction Manually

Test your setup by grading a specific assignment. Replace `98765` with your
actual Canvas assignment ID.

```bash
ccc run-once 98765 --course ccc-course-cs101
```

**What happens:**

1. **Downloads** all submissions for assignment `98765`
2. **Runs** the grader Docker image on each submission
3. **Uploads** feedback and grades to Canvas

You’ll see progress output like:

```
📥 Downloading submissions for assignment 98765...
✅ Downloaded 42 submissions
🏃 Running graders in Docker containers...
  ████████████████████████████████████ 100% (42/42)
📊 Results: 40 passed, 2 failed
📤 Uploading feedback to Canvas...
🎉 Done! Grades posted for 40 students
⏱️  Total time: 18.3 seconds
```

To grade a single submission (dry‑run mode), add `--submission-id`:

```bash
ccc run-once 98765 --submission-id 54321 --dry-run
```

### 3. Start the Webhook Server (Optional)

For automatic grading when students submit, start the webhook server:

```bash
ccc webhook serve --host 0.0.0.0 --port 8080
```

The server listens for Canvas webhook events and triggers the correction flow.
You’ll need to configure Canvas to send events to this endpoint.

### 4. Create a Prefect Deployment (Optional)

To run corrections via Prefect’s scheduler or API, create a deployment. First,
ensure your Prefect server is running (see **Installation & Setup** below).

```bash
ccc deploy create ccc-course-cs101
```

This registers a deployment that can be triggered by webhooks or manually
through the Prefect UI.

---

## Installation & Setup

### Prerequisites

- **[uv](https://docs.astral.sh/uv/)** – manages Python toolchain and
  dependencies
- **Python 3.13** (automatically provisioned by `uv sync`)
- **Canvas API token** and course identifiers with sufficient permissions
- **Docker** (for running grader containers)

### Complete Installation

1. Clone the repository and enter it:

   ```bash
   git clone https://github.com/jakob1379/canvas-code-correction.git
   cd canvas-code-correction
   ```

2. Provision dependencies and the virtual environment with uv:

   ```bash
   uv sync
   ```

3. Create a `.env` file (copy `.env.example` or request credentials) and provide
   the following values:

   ```dotenv
   CANVAS_API_URL=https://canvas.instructure.com
   CANVAS_API_TOKEN=your_token
   CANVAS_COURSE_ID=123456
   # optional overrides
   CCC_WORKING_DIR=/absolute/path/to/var/runs
   # RustFS configuration (for integration tests)
   # RUSTFS_ENDPOINT=http://localhost:9000
   # RUSTFS_ACCESS_KEY=rustfsadmin
   # RUSTFS_SECRET_KEY=rustfsadmin
   # RUSTFS_BUCKET_NAME=test-assets
   # RUSTFS_PREFIX=dev
   ```

4. Verify the CLI is working:

   **Note:** If you haven't activated the virtual environment created by
   `uv sync`, prefix the command with `uv run` or activate it first with
   `source .venv/bin/activate`.

   ```bash
   ccc --help
   ```

### Prefect Server (Optional)

For local development, start a Prefect server:

```bash
poe prefect
```

This starts Prefect’s UI at `http://localhost:4200`. The CLI commands interact
with this server to store blocks and create deployments.

## Security Features

Recent improvements make CCC secure by default:

- **PostgreSQL password hardening**: No default passwords in docker‑compose.yml
- **Regex DoS protection**: Fixed vulnerable patterns in submission parsing
- **S3 bucket ownership**: Added `ExpectedBucketOwner` to prevent
  misconfigurations
- **Docker security**: Extended `.dockerignore` to exclude `.env*` files
- **Test security**: Removed hardcoded tokens and HTTP URLs from tests
- **Comprehensive test coverage**: 100% coverage for critical modules (runner,
  auth, workspace) with integration tests for resource limits and error handling

## Testing & Development

### Running Tests

Execute the full test suite and lint before opening a pull request:

```bash
prek run
pytest
ruff check
```

Test coverage reports are generated automatically (`--cov-report=term-missing`).
Critical modules have 100% coverage, and integration tests verify real S3
operations with RustFS mocks.

#### Integration Tests with RustFS

For end‑to‑end integration tests, start the local RustFS S3‑compatible storage:

```bash
poe s3
poe rustfs-setup
pytest -m integration
```

Integration tests use mock S3Bucket fixtures to avoid Prefect block registration
requirements, allowing tests to run against a real S3‑compatible endpoint
without external dependencies.

#### End‑to‑End Tests

Comprehensive e2e tests require a running RustFS server and Prefect server:

```bash
docker-compose up -d rustfs postgres redis prefect-server prefect-services
pytest -m e2e
```

## Documentation

Detailed documentation is available in the `docs/` directory:

- **[Architecture Overview](docs/reference/01-architecture.md)** – component
  responsibilities and data flow
- **[CLI Reference](docs/reference/02-cli.md)** – complete command‑line
  reference
- **[Configuration Guide](docs/reference/03-configuration.md)** – system setup
  and environment variables
- **[Platform Setup](docs/platform-setup/)** – operator‑focused guides for
  deployment and monitoring
- **[Tutorial](docs/tutorial/)** – course‑responsible guide for creating work
  packages

## Contributing

We welcome contributions that improve reliability, performance, or ergonomics.
See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on development
setup, code style, testing, and the pull request process.

## License

This project is distributed under the terms of the MIT License. See
[`LICENSE`](LICENSE) for details.
