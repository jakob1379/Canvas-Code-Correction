<div align="center">

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/jakob1379/Canvas-Code-Correction/actions/workflows/test.yml/badge.svg)](https://github.com/jakob1379/Canvas-Code-Correction/actions)
[![Coverage](https://codecov.io/gh/jakob1379/Canvas-Code-Correction/graph/badge.svg?branch=main)](https://codecov.io/gh/jakob1379/Canvas-Code-Correction)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-CCC-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==)](https://deepwiki.com/jakob1379/Canvas-Code-Correction)

</div>

# Canvas Code Correction

**Canvas Code Correction (CCC)** orchestrates Canvas grading workflows with
**Prefect**, **Docker**, and **S3-compatible asset storage**. It gives you one
repo for course setup, manual grading runs, webhook intake, worker execution,
and Canvas uploads.

## Try It Now

Copy and run this from the repository root:

```bash
$ uv sync
$ source .venv/bin/activate
$ ccc --help
```

Expected output starts like this:

```text
Usage: ccc [OPTIONS] COMMAND [ARGS]...

Canvas Code Correction CLI
```

If you prefer not to activate the virtual environment, prefix commands with
`uv run`, for example `uv run ccc --help`.

## Operator Workflow

### 1. Configure a course

Use `ccc course setup` to create a `ccc-course-<slug>` Prefect block that
stores the Canvas connection, grader image, asset block, asset prefix, and work
pool name.

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

Expected output includes:

```text
✓ Canvas access validated successfully
✓ Course ID 12345 validated
✓ Course configuration saved as block: ccc-course-cs101
```

### 2. Run a correction manually

Use `ccc course run` for batch or single-submission runs.

```bash
$ ccc course run 98765 --course ccc-course-cs101
```

Or limit the run to one submission:

```bash
$ ccc course run 98765 --course ccc-course-cs101 --submission-id 54321 --dry-run
```

Single-submission output includes a JSON summary with downloaded files,
workspace path, and result keys.

### 3. Start the webhook server

```bash
$ ccc system webhook serve --host 0.0.0.0 --port 8080
```

Expected output:

```text
Starting webhook server on 0.0.0.0:8080
```

### 4. Create the Prefect deployment

CCC creates the webhook-oriented deployment for you:

```bash
$ ccc system deploy create ccc-course-cs101
```

Expected output includes:

```text
Creating deployment for course block: ccc-course-cs101
Deployment 'ccc-cs101-deployment' created/updated successfully
```

### 5. Start a worker

The worker must listen on the same work pool stored in the course block:

```bash
$ uv run prefect worker start --pool course-work-pool-cs101
```

## Installation

### Prerequisites

- **Python 3.13**
- **uv**
- **Docker**
- A **Canvas API token**
- A reachable **Prefect API** for block storage and deployments

### Environment file

Copy `.env.example` when you need a local baseline:

```bash
$ cp .env.example .env
```

Common values:

```dotenv
CANVAS_API_URL=https://canvas.instructure.com
CANVAS_API_TOKEN=your_canvas_api_token_here
PREFECT_API_URL=http://localhost:4200/api
```

For local RustFS testing, uncomment the `RUSTFS_*` entries in `.env.example` or
use `.env.dev`.

## Development Commands

The repo standard commands live in `pyproject.toml`:

```bash
$ poe fmt
$ poe lint
$ poe check
$ poe test
$ poe all
```

Useful extras:

```bash
$ poe prefect
$ poe s3
$ poe rustfs-setup
$ uv run zensical build --strict --clean
```

Integration and e2e commands:

```bash
$ uv run pytest tests/integration -v --strict-markers -m integration --no-cov
$ poe test-e2e
```

## Project Layout

- `src/canvas_code_correction/` application code
- `docs/` user and operator documentation
- `tests/` unit, integration, and e2e suites
- `scripts/` helper utilities, including RustFS setup

## Documentation

Start here:

- [Documentation Index](docs/index.md)
- [Architecture Overview](docs/reference/01-architecture.md)
- [CLI Reference](docs/reference/02-cli.md)
- [Configuration Reference](docs/reference/03-configuration.md)
- [Platform Setup](docs/platform-setup/01-configuring-course.md)
- [Tutorial](docs/tutorial/index.md)

## Contributing

Use the workflow in [CONTRIBUTING.md](CONTRIBUTING.md). If you edit docs, apply
the repository checklist in [.docs-style-checklist.md](.docs-style-checklist.md)
and rebuild the docs before opening a PR.

## License

This project is distributed under the terms of the MIT License. See
[`LICENSE`](LICENSE) for details.
