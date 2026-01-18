<div align="center">

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/jakob1379/Canvas-Code-Correction/actions/workflows/test.yml/badge.svg)](https://github.com/jakob1379/Canvas-Code-Correction/actions)
[![Coverage](https://img.shields.io/endpoint?url=https://ccc.jgalabs.dk/badges/coverage.json)](https://ccc.jgalabs.dk/htmlcov/)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-CCC-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==)](https://deepwiki.com/jakob1379/Canvas-Code-Correction)

</div>

# Canvas Code Correction

**Modern orchestration for downloading, grading, and uploading Canvas
submissions using Prefect, Docker, and reproducible local workspaces.**

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages Python toolchain and dependencies)
- Python 3.13 (automatically provisioned by `uv sync`)
- Canvas API token and course identifiers with sufficient permissions
- Docker (for running grader containers)

### Installation

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

   ```bash
   ccc --help
   ```

### Prefect Server (Optional)

For local development, start a Prefect server:

```bash
uv run poe prefect
```

This starts Prefect's UI at `http://localhost:4200`. The CLI commands interact
with this server to store blocks and create deployments.

## Interactive Tutorial

This tutorial walks you through the main features of Canvas Code Correction
using the Typer‑based CLI.

### 1. Configure Your First Course

Use `ccc configure-course` to create a course configuration block. You'll need:

- Canvas API token
- Canvas course ID
- Prefect S3 bucket block name (for grader assets) – create one via Prefect UI
  or CLI

```bash
uv run ccc configure-course cs101 \
  --token YOUR_CANVAS_TOKEN \
  --course-id 12345 \
  --assets-block course-assets-cs101 \
  --docker-image yourusername/canvas-grader:latest \
  --s3-prefix graders/cs101/
```

The command will prompt for the token if you omit `--token`. The configuration
is stored as a Prefect block named `ccc-course-cs101`.

List all configured courses:

```bash
uv run ccc list-courses
```

### 2. Run a Correction Manually

Test your setup by grading a specific assignment:

```bash
uv run ccc run-once 98765 --course ccc-course-cs101
```

This downloads all submissions for assignment ID 98765, runs the grader Docker
image on each, and uploads feedback to Canvas.

To grade a single submission (dry‑run mode):

```bash
uv run ccc run-once 98765 --submission-id 54321 --dry-run
```

### 3. Start the Webhook Server

For automatic grading when students submit, start the webhook server:

```bash
uv run ccc webhook serve --host 0.0.0.0 --port 8080
```

The server listens for Canvas webhook events and triggers the correction flow.
You'll need to configure Canvas to send events to this endpoint.

### 4. Create a Prefect Deployment

To run corrections via Prefect's scheduler or API, create a deployment. Ensure
your Prefect server is running (see Quick Start).

```bash
uv run ccc deploy create ccc-course-cs101
```

This registers a deployment that can be triggered by webhooks or manually
through the Prefect UI.

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

- [Architecture Overview](docs/reference/01-architecture.md)
- [CLI Reference](docs/reference/02-cli.md)
- [Configuration Guide](docs/reference/03-configuration.md)
- [Platform Setup](docs/platform-setup/) – for operators
- [Tutorial](docs/tutorial/) – for course responsible

## Contributing

We welcome contributions that improve reliability, performance, or ergonomics.
See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on development
setup, code style, testing, and the pull request process.

## License

This project is distributed under the terms of the MIT License. See
[`LICENSE`](LICENSE) for details.
