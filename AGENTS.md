# Project Overview
Canvas Code Correction (CCC) is a Python 3.13+ service for grading Canvas
submissions with Prefect, Docker, and S3-compatible asset storage. It covers
course setup, webhook intake, isolated grader runs, result collection, and
Canvas uploads in one repo.

## Repository Structure
- `.github/` CI, release, docs deploy, and Dependabot config.
- `docs/` Tutorials, reference docs, and platform setup guides.
- `scripts/` Local helper scripts, mainly RustFS setup.
- `src/` Python source tree.
- `src/canvas_code_correction/` CLI, flows, webhook server, clients, config,
  and Prefect blocks.
- `tests/` Unit, integration, and e2e tests.
- `workspace/` Local RustFS data and scratch space.
- `site/` Generated docs output.
- Tooling/cache dirs such as `.venv/`, `.cache/`, `.pytest_cache/`,
  `.ruff_cache/`, `.scannerwork/`, `.skylos/` are generated state.

## Build & Development Commands
```bash
uv sync
uv sync --all-groups
source .venv/bin/activate
```

```bash
poe fmt
poe lint
poe ci:lint
poe check
poe test
poe all
```

```bash
pytest tests/unit/test_workspace.py -v
uv run pytest tests/unit -v --strict-markers --cov=src/canvas_code_correction --cov-report=xml --cov-report=term
uv run pytest tests/integration -v --strict-markers -m integration --no-cov
uv run pytest tests/e2e -v --strict-markers -m e2e --no-cov
```

```bash
ccc --help
ccc course setup
ccc course run <assignment-id> --course <course-block>
ccc system webhook serve --host 127.0.0.1 --port 8080
ccc system status
ccc system deploy create ccc-course-cs101
```

```bash
poe prefect
poe s3
poe rustfs-setup
poe serve-docs
uv run zensical build --strict --clean
poe docker-publish
```

> TODO: `poe docker-publish` references `containers/grader/Dockerfile`, but no
> `containers/` directory exists in this checkout.

## Code Style & Conventions
- Python 3.13 only.
- Format with `ruff format`; line length 100; double quotes.
- Lint with Ruff using `select = ["ALL"]` and existing per-file ignores.
- Use type hints throughout.
- Use `snake_case` for modules/functions/variables and `PascalCase` for classes.
- Keep flow logic under `src/canvas_code_correction/flows/`.
- Keep CLI entrypoints in `cli.py`, `cli_course.py`, and `cli_system.py`.
- Preserve compatibility wrappers: `collector.py`, `runner.py`, `uploader.py`,
  and `workspace.py`.
- Commit messages follow Commitizen conventional commits.

```text
<type>(<scope>): <imperative summary>
```

## Architecture Notes
```text
Canvas webhook / CLI
        |
        v
 Typer CLI + FastAPI webhook server
        |
        v
 Prefect deployments / flows
        |
        v
 correct_submission_flow
   |- CanvasResources -> Canvas API
   |- prepare_workspace -> RustFS/S3 + local workspace
   |- GraderExecutor -> Docker grader
   |- ResultCollector -> points/comments/artifacts
   `- CanvasUploader -> Canvas uploads
```

The CLI and webhook server both load course config from Prefect blocks and end
up in `correct_submission_flow`. That flow downloads submission data, prepares a
workspace, runs the grader in Docker, collects outputs, and uploads feedback and
grades back to Canvas.

## Testing Strategy
- Unit tests live in `tests/unit/` and run in CI on every push/PR.
- Integration tests live in `tests/integration/` and require RustFS and Canvas
  credentials.
- E2E tests live in `tests/e2e/` and require Docker plus Canvas credentials.
- Local default `pytest` excludes `integration` and `e2e` via `pyproject.toml`.
- CI only runs integration/e2e when Canvas secrets are available.

## Security & Compliance
- Never commit `.env`, `.env.dev`, tokens, or webhook secrets.
- Prefer stdin for secrets, e.g. `printf "%s" "$CANVAS_API_TOKEN" | ...`.
- Canvas tokens and webhook secrets use `SecretStr` and should live in env vars
  or Prefect blocks.
- Webhook auth supports JWT or HMAC; Canvas API fallback exists but is disabled
  by default.
- Pre-commit runs security/compliance checks including `gitleaks`, `bandit`,
  `uv-secure`, workflow validation, and `validate-pyproject`.
- License is MIT.

## Agent Guardrails
- Never edit secrets or generated state: `.env*`, `.venv/`, `.cache/`,
  `.pytest_cache/`, `.ruff_cache/`, `.scannerwork/`, `coverage.*`, `site/`,
  `docs/htmlcov/`, `__pycache__/`.
- Treat `pyproject.toml`, `.pre-commit-config.yaml`, `Dockerfile`,
  `docker-compose.yml`, `.github/workflows/*`, and Prefect block schemas as
  high-impact files; run relevant checks after changing them.
- In pytest fixtures do not use `autouse=true`; it creates hidden suite-wide
  side effects. `tests/AGENTS.md` repeats this rule.
- Respect webhook rate limits; default is `10/minute`.
- Only run integration/e2e flows against Canvas when explicit credentials are
  configured.

## Extensibility Hooks
- Per-course config lives in
  `src/canvas_code_correction/prefect_blocks/canvas.py`.
- Main grader knobs: `grader_image`, `grader_command`, `grader_env`,
  `grader_timeout_seconds`, `grader_memory_mb`, `work_pool_name`,
  `workspace_root`.
- Storage is swappable via `RUSTFS_ENDPOINT`, `RUSTFS_ACCESS_KEY`,
  `RUSTFS_SECRET_KEY`, `RUSTFS_BUCKET_NAME`, and `RUSTFS_PREFIX`.
- Prefect runtime uses `PREFECT_API_URL` and `PREFECT_API_KEY`.
- Test/runtime Canvas env vars: `CANVAS_API_URL`, `CANVAS_API_TOKEN`,
  `CANVAS_COURSE_ID`, `CANVAS_TEST_ASSIGNMENT_ID`.
- Webhook settings include `enabled`, `require_jwt`, `rate_limit`, and
  `deployment_name`.

> TODO: `allow_canvas_api_fallback` exists in code but is not exposed on the
> persisted course block.

## Further Reading
- [`README.md`](README.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`docs/reference/01-architecture.md`](docs/reference/01-architecture.md)
- [`docs/reference/02-cli.md`](docs/reference/02-cli.md)
- [`docs/reference/03-configuration.md`](docs/reference/03-configuration.md)
- [`docs/platform-setup/01-configuring-course.md`](docs/platform-setup/01-configuring-course.md)
- [`docs/platform-setup/02-setting-up-prefect.md`](docs/platform-setup/02-setting-up-prefect.md)
- [`docs/platform-setup/07-rustfs-storage.md`](docs/platform-setup/07-rustfs-storage.md)
