# Canvas Code Correction

Modern orchestration for downloading, grading, and uploading Canvas submissions
using Prefect, Docker, and reproducible local workspaces.

## Quickstart for Developers

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages Python toolchain and dependencies)
- Python 3.13 (automatically provisioned by `uv sync`)
- Canvas API token and course identifiers with sufficient permissions

### Environment Setup

1. Clone the repository and enter it:

   ```bash
   git clone https://github.com/<your-org>/canvas-code-correction.git
   cd canvas-code-correction
   ```

2. Provision dependencies and the virtual environment with uv:

   ```bash
   uv sync
   ```

3. Create a `.env` file (copy `.env.example` or request credentials) and provide the
   following values:

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

4. Run project commands through uv to guarantee the environment is active:

   ```bash
   uv run ccc --help
   ```

### Running Tests & Checks

Execute the full test suite and lint before opening a pull request:

```bash
uv run prek run
uv run pytest
uv run ruff check
```

#### Integration Tests with RustFS

For end-to-end integration tests, start the local RustFS S3-compatible storage:

```bash
uv run poe s3
uv run poe rustfs-setup
uv run pytest -m integration
```

#### End-to-End Tests

Comprehensive e2e tests require a running RustFS server and Prefect server. Use docker-compose:

```bash
docker-compose up -d rustfs postgres redis prefect-server prefect-services
uv run pytest -m e2e
```

Configuration via environment variables:
- `RUSTFS_ENDPOINT`: S3 endpoint URL (default: `http://localhost:9000`)
- `RUSTFS_ACCESS_KEY`: Access key (default: `rustfsadmin`)
- `RUSTFS_SECRET_KEY`: Secret key (default: `rustfsadmin`)
- `RUSTFS_BUCKET_NAME`: Bucket name (default: `test-assets`)
- `RUSTFS_PREFIX`: Path prefix for assets (default: `dev`)

## Contributing

We welcome contributions that improve reliability, performance, or ergonomics.

1. Fork the repository and create a feature branch
   (`git switch -c feat/your-change`).
2. Run `uv sync` to install dependencies and keep the lockfile consistent.
3. Implement changes, matching existing code style and Prefect-oriented patterns
   already in use.
4. Validate locally (`uv run pytest` and any relevant flows or scripts).
   For integration tests, ensure RustFS server is running (`uv run poe s3`).
5. Submit a pull request describing the change, expected impact, and any
   follow-up work.

Open an issue first for major architectural proposals to confirm alignment with
maintainers.

## License

This project is distributed under the terms of the MIT License. See
[`LICENSE`](LICENSE) for details.
