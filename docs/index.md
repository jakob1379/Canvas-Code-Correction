# Canvas Code Correction v2

**Try It Now** (60 seconds)

!!! note "Virtual Environment" All commands in this documentation assume you
have activated the virtual environment created by `uv sync`. If you haven't
activated it, prefix commands with `uv run`. To activate:

    ```bash
    source .venv/bin/activate
    ```

    Or use `uv shell` to start a new shell with the environment activated.

Copy and paste this command to run a quick test that verifies your environment
is ready:

```bash
$ pytest tests/unit/test_workspace.py -v
```

You will see output similar to:

```
============================= test session starts ==============================
platform linux -- Python 3.14.0, pytest-9.0.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /home/jsg/Documents/jsg/Canvas-Code-Correction
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.0.0, datadir-1.8.0, xdist-3.8.0
collecting ... collected 9 items

tests/unit/test_workspace.py::test_workspace_config PASSED               [ 11%]
tests/unit/test_workspace.py::test_workspace_paths PASSED                [ 22%]
tests/unit/test_workspace.py::test_build_workspace_config PASSED         [ 33%]
...
tests/unit/test_workspace.py::test_prepare_workspace_submission_file_not_exists PASSED [100%]
```

If all tests pass, your setup is correct and you are ready to explore Canvas
Code Correction.

## What is Canvas Code Correction?

**Canvas Code Correction (CCC)** is a Python‑based orchestration layer that
automates the grading of programming assignments in Canvas. It replaces ad‑hoc
shell scripts with a **Prefect‑powered pipeline** that:

- Downloads student submissions from Canvas
- Executes instructor‑provided grader code in **secure, ephemeral Docker
  containers**
- Collects scores, feedback, and artefacts
- Uploads results back to Canvas

CCC keeps **platform operators**, **grader authors**, and **contributors**
separate:

- **Platform operators** deploy and monitor the grading pipeline
- **Grader authors** (course responsibles) create Docker images and test scripts
- **Contributors** extend the core orchestration logic

The system is **modular**, **testable**, and **secure by default**. It ships
with MkDocs documentation, pytest‑based tests, and uv‑managed dependencies.

## Documentation Structure

Choose the documentation that matches your role:

| Role                                   | What You Need                                       | Where to Start                                                                    |
| -------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Grader Author** (course responsible) | Create grader Docker images and test scripts        | [Tutorial: Create Your First Work Package in 10 Minutes](./tutorial/index.md)     |
| **Platform Operator**                  | Deploy, configure, and monitor the grading pipeline | [Platform Setup: Configuring a Course](./platform-setup/01-configuring-course.md) |
| **Contributor** / **Developer**        | Understand the architecture and extend the system   | [Reference: Architecture Overview](./reference/01-architecture.md)                |
| **All Roles**                          | See what is coming next and track progress          | [Current Development: Roadmap](./current-development/01-roadmap.md)               |

### Tutorial (4 files)

Start here if you are a **course responsible** creating your first work package.

1. **[Tutorial Index](./tutorial/index.md)** – Create a work package in 10
   minutes
2. **[Prerequisites](./tutorial/02-prerequisites.md)** – Canvas API access,
   Docker basics, Python 3.13+
3. **[Creating a Grader Docker Image](./tutorial/03-creating-grader-image.md)**
   – Build a container with your testing environment
4. **[Writing Grader Tests](./tutorial/04-writing-grader-tests.md)** – Write
   scripts that evaluate student submissions

### Reference (6 files)

Deep dive into architecture, CLI, configuration, and APIs.

1. **[Architecture Overview](./reference/01-architecture.md)** – Design goals,
   component responsibilities, and new services
2. **[CLI Reference](./reference/02-cli.md)** – All `ccc` commands with examples
3. **[Configuration](./reference/03-configuration.md)** – Environment variables,
   Prefect blocks, and course‑specific settings
4. **[API Clients](./reference/04-api-clients.md)** – Canvas API wrapper and
   storage client details
5. **[Grader Image Specification](./reference/05-grader-image.md)** – Required
   entry points, environment variables, and output format
6. **[Authoring Grader Tests](./reference/06-authoring-grader-tests.md)** – Test
   structure, scoring, and feedback conventions

### Platform Setup (7 files)

Step‑by‑step guides for **platform operators** deploying CCC in production.

1. **[Configuring a Course](./platform-setup/01-configuring-course.md)** – Set
   up a course with Canvas token, Docker image, and S3 assets
2. **[Setting Up Prefect](./platform-setup/02-setting-up-prefect.md)** – Install
   Prefect, create work pools, and configure agents
3. **[Scheduling Corrections](./platform-setup/03-scheduling-corrections.md)** –
   Create scheduled deployments and trigger flows via webhooks
4. **[Monitoring Results](./platform-setup/04-monitoring-results.md)** – Track
   flow runs, logs, and errors in the Prefect UI
5. **[Deploying Tests to CCC](./platform-setup/05-deploying-tests-to-ccc.md)** –
   Upload grader assets to S3 and link them to a course
6. **[Prefect Agent Configuration](./platform-setup/06-prefect-agent.md)** – Run
   a Prefect agent locally or in a container
7. **[RustFS Storage](./platform-setup/07-rustfs-storage.md)** – Set up an
   S3‑compatible storage backend for local development and production

### Current Development (2 files)

Track progress and upcoming changes.

1. **[Roadmap](./current-development/01-roadmap.md)** – High‑level timeline and
   feature priorities
2. **[Phase 2 Migration Plan](./current-development/02-phase-2-migration-plan.md)**
   – Detailed migration steps from v1 to v2

## Quick Start

Run these commands to install dependencies, run the full test suite, and serve
the documentation locally. These commands assume **Python 3.13+** and a clean
environment.

```bash
# Install dependencies (uv handles virtualenv and locking)
$ uv sync
```

You will see output similar to:

```
Resolved 171 packages in 4ms
Installed 171 packages in 2.3s
```

```bash
# Run the entire test suite (~30 seconds)
$ pytest
```

Expect a series of passing tests:

```
============================= test session starts ==============================
platform linux -- Python 3.14.0, pytest-9.0.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /home/jsg/Documents/jsg/Canvas-Code-Correction
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.0.0, datadir-1.8.0, xdist-3.8.0
collecting ... collected 123 items

tests/unit/test_workspace.py::test_workspace_config PASSED               [  0%]
tests/unit/test_workspace.py::test_workspace_paths PASSED                [  1%]
...
tests/e2e/test_correction_flow.py::test_full_flow_with_mocks PASSED      [100%]
```

```bash
# Serve documentation on http://localhost:8000
$ poe serve-docs
```

The command starts a local MkDocs server:

```
INFO    -  Building documentation...
INFO    -  Cleaning site directory
INFO    -  Documentation built in 0.30 seconds
INFO    -  [20:00:00] Serving on http://localhost:8000
INFO    -  [20:00:00] Browser opened automatically
```

Press `Ctrl+C` to stop the server.

### Local Development with RustFS

For integration testing, start a local RustFS S3‑compatible server:

```bash
# Start RustFS server
$ poe s3

# Setup RustFS for testing (creates bucket, uploads test assets)
$ poe rustfs-setup

# Run integration tests
$ pytest -m integration
```

Configuration via environment variables:

- `RUSTFS_ENDPOINT`: S3 endpoint URL (default: `http://localhost:9000`)
- `RUSTFS_ACCESS_KEY`: Access key (default: `rustfsadmin`)
- `RUSTFS_SECRET_KEY`: Secret key (default: `rustfsadmin`)
- `RUSTFS_BUCKET_NAME`: Bucket name (default: `test-assets`)
- `RUSTFS_PREFIX`: Path prefix for assets (default: `dev`)

## Current Status (January 2026)

**Phase 2 of the v2 rewrite is complete.** The following key components are
implemented and tested:

- **GraderExecutor**: Secure Docker‑based execution with resource limits and
  timeout handling
- **ResultCollector**: Robust parsing of grader outputs and feedback zip
  creation
- **CanvasUploader**: Idempotent feedback and grade uploads with duplicate
  detection
- **Prefect Flow Integration**: Complete end‑to‑end flow with `execute_grader`,
  `collect_results`, `upload_feedback`, and `post_grade` tasks
- **Enhanced CLI**: New `ccc` commands for `run‑once`, `configure‑course`, and
  `list‑courses`
- **RustFS Integration**: Configurable S3‑compatible storage backend with
  environment‑variable support for production deployments
- **Comprehensive Test Suite**: End‑to‑end tests with docker‑compose stack
  (RustFS, Prefect) and GitHub Actions CI pipeline
- **Production‑Ready Configuration**: Support for custom S3 endpoints and secure
  credential management

All unit tests pass, and the system is ready for integration testing with the
Canvas Cloud development course.

## Need Help?

- Use the **agent system** described in [`AGENTS.md`](../AGENTS.md) to explore
  the codebase and delegate tasks.
- Check the
  [GitHub repository](https://github.com/jakob1379/canvas-code-correction) for
  issues and discussions.
- Follow the
  [Conventional Commits](../AGENTS.md#3-commit-conventions-conventional-commits)
  convention when contributing changes.
