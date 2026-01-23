# Phase 2 – Canvas Client Migration Plan

This document is your actionable guide for migrating from the legacy bash+Python
tooling to a Prefect‑based orchestration system. It provides step‑by‑step
instructions, verification commands, and the current implementation status.

!!! note "Before you start" Review the [project roadmap](01-roadmap.md) to
understand the broader context.

## Migration Overview

Your goal is to replace the existing `canvas-code-correction.sh` orchestrator
and its supporting scripts with a modular Python pipeline orchestrated by
Prefect. The migration preserves all essential features of the legacy system
while adding container‑based isolation, robust error handling, and extensible
workflow management.

**Key outcomes**:

- **Canvas API client** with retry logic and typed responses
- **Submission workspace management** that mirrors the existing download/unzip
  contract
- **Containerised grader execution** with configurable resource limits
- **Idempotent upload** of feedback and grades
- **End‑to‑end Prefect flow** that integrates all components

All components are already implemented and tested. This guide walks you through
the migration steps, shows you how to verify each component, and points out
remaining open questions.

## 1. Legacy Feature Inventory

The table below lists the legacy features you must preserve. Every row has been
addressed in the new implementation.

| Scope                                   | Legacy Implementation                                     | Parity Notes                                                                                                                          |
| --------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Assignment discovery & folder bootstrap | `setup-assignment-folders.sh`, `init-config.sh`           | Reads Canvas via `CanvasClient` and populates local directories using `SubmissionStore`.                                              |
| Submission download                     | `download_submissions.py`                                 | Supports filtering, pagination, and MD5‑based file naming via `CanvasClient` and `SubmissionStore`.                                   |
| Extraction/normalisation                | `submissions_unzip.py`, `process_submissions.sh`          | Handles zip unpacking and folder flattening inside `SubmissionStore`.                                                                 |
| Grading execution                       | `submissions_correcting.sh`, user‑provided `code/main.sh` | Executes instructor code inside a Docker container via `GraderExecutor`; supports timeouts, parallelism, and firejail‑like isolation. |
| Result packaging                        | `zip_submission`, `submissions_correcting.sh`             | Produces `<handin>+.zip` artefacts and `<handin>_points.txt` via `ResultCollector`.                                                   |
| Comment upload                          | `upload_comments.py`                                      | Idempotent upload with MD5+filename duplicate detection, handled by `CanvasUploader`.                                                 |
| Grade upload                            | `upload_grades.py`                                        | Reads points files and applies config‑specified grading mode (score vs complete) via `CanvasUploader`.                                |
| Cleanup                                 | `delete_submissions.py`                                   | Removes local submissions on demand (still manual; can be added as a Prefect task).                                                   |
| Analytics                               | `plot_scores.py`, `hclust.py`, `plagiarism-check.sh`      | Non‑critical for MVP; hooks are preserved for future implementation.                                                                  |

**Supporting utilities**:

- **`canvas_helpers.py`** → replaced by `CanvasClient`
- **`config2shell`/`.config_array`** → replaced by environment‑variable‑based
  `Settings` models
- **`canvas-code-correction.sh`** → replaced by `correct_submission_flow`
  Prefect flow

## 2. Course Fixture & Test Data

All functional tests rely on a shared Canvas development course. Follow these
steps to set up your test environment:

1. **Obtain a Canvas API token** and store it as `CANVAS_API_TOKEN` in your
   project‑level `.env` file.
2. **Set the course ID** as `CANVAS_COURSE_ID` in the same `.env` file.
3. **Use the development course** at
   <https://canvas.instructure.com/courses/13121974> for testing.
4. **Add new fixtures dynamically** via the Canvas API; capture resulting IDs in
   `.env` for repeatability.

!!! note "Important" The repository does **not** depend on static IMSCC exports.
All test data is retrieved live from the Canvas API.

## 3. Target Architecture (Prefect‑driven)

The new system is built around six core Python components:

| Component               | Responsibility                                                                                                                                        |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CanvasClient**        | Thin wrapper around the Canvas REST API with retry/backoff and typed responses (uses `canvasapi`).                                                    |
| **SubmissionStore**     | Manages the local filesystem workspace (`var/runs/<assignment>/<submission>`); handles download, extraction, and normalisation.                       |
| **GraderExecutor**      | Executes grading inside a clean Docker container, mounts the workspace, injects instructor code, and enforces resource limits (CPU, memory, network). |
| **ResultCollector**     | Normalises grader outputs into the expected `points.txt`, `comments.txt`, `artifacts/` structure.                                                     |
| **CanvasUploader**      | Uploads comments and grades idempotently, maintaining audit logs and duplicate detection via MD5 hashing.                                             |
| **Reporter** (optional) | Analytics hook for grade summaries, plotting triggers, etc.                                                                                           |

**Prefect orchestration flow**:

```text
Event / trigger (manual CLI, webhook, schedule)
  → Flow: correct_submission_flow
      → Task: fetch_submission_metadata
      → Task: prepare_workspace
      → Task: download_submission_files (CanvasClient → SubmissionStore)
      → Task: stage_instructor_code (from repo or artifact registry)
      → Task: run_grader_command (GraderExecutor)
      → Task: collect_results
      → Task: upload_comment
      → Task: upload_grade
      → Task: publish_run_summary
```

## 4. Incremental Migration Steps

All steps below are **completed** and verified. Use the verification commands to
confirm your environment matches the expected state.

### Step 1: Configuration groundwork ✅

**What you did**: Migrated configuration from INI files and bash arrays to
environment‑variables validated by Pydantic `Settings` models.

**Verification**:

```bash
$ grep -E '^CANVAS_' .env
CANVAS_API_TOKEN=...
CANVAS_COURSE_ID=...
```

### Step 2: Canvas client & download ✅

**What you did**: Implemented `CanvasClient` wrapping `canvasapi` for submission
metadata and attachment download.

**Verification**:

```bash
$ uv run --group tests pytest src/canvas_client/ -xvs -k test_download
```

### Step 3: Workspace preparation ✅

**What you did**: Built `SubmissionStore` that handles extraction,
normalisation, and workspace layout.

**Verification**:

```bash
$ uv run --group tests pytest src/submission_store/ -xvs
```

### Step 4: Runner integration ✅

**What you did**: Implemented `GraderExecutor` (Docker‑based execution) and
`ResultCollector` (output packaging).

**Verification**:

```bash
$ uv run --group tests pytest src/runner/ -xvs
$ uv run --group tests pytest src/result_collector/ -xvs
```

### Step 5: Uploader tasks ✅

**What you did**: Created `CanvasUploader` for idempotent feedback and grade
uploads with MD5 duplicate detection.

**Verification**:

```bash
$ uv run --group tests pytest src/uploader/ -xvs
```

### Step 6: End‑to‑end Prefect flow ✅

**What you did**: Integrated all components into `correct_submission_flow`
(download → workspace → execution → collection → upload).

**Verification**:

```bash
$ uv run --group tests pytest tests/e2e/ -xvs
```

### Step 7: Testing & documentation ✅

**What you did**: Executed the full test suite (`uv run --group tests pytest`)
and established pre‑commit hooks. All unit tests pass as of January 2026.

**Verification**:

```bash
$ uv run --group tests pytest --cov --cov-report=term-missing
```

## 5. Non‑goals for This Iteration

- **Automated Canvas course cloning/reset** – remains manual.
- **Webhook listener/service deployment** – follow after the core workflow is
  stable.
- **Full analytics/visualisation parity** – defer until the grading loop is
  stable.
- **Multi‑run scheduling/daemon replacement** – address after the single‑run
  path is reliable.

## 6. Open Questions / Follow‑ups

1. **Instructor code packaging** – store in repo, S3, or separate artifact?
   (short‑term: repository folder copied into workspace.)
2. **Secrets management** – continue with local `.env`, but plan migration to
   Prefect blocks / Vault later.
3. **Container image build pipeline** – need CI job to build/publish grader
   image tagged with repo commit.
4. **Student code limits** – confirm CPU/memory/time defaults with teaching
   team; codify in settings.
5. **Roll‑forward strategy** – plan data migration for existing feedback
   archives (if needed).
6. **Prefect assets cataloguing** – revisit in Phase 3 once long‑term run
   lineage requirements are defined.
7. **CI & operational runbooks** – document Prefect worker setup and add CI
   pipelines to execute tests/linters before Phase 3 launch.

## 7. Recent Updates (January 2026)

- **RustFS Integration**: Added configurable RustFS S3‑compatible storage
  support via environment variables (`RUSTFS_ENDPOINT`, `RUSTFS_ACCESS_KEY`,
  `RUSTFS_SECRET_KEY`, `RUSTFS_BUCKET_NAME`, `RUSTFS_PREFIX`). Updated
  `setup‑rustfs.py` script and documentation.
- **Comprehensive Test Suite**: Added end‑to‑end test suite (`tests/e2e/`) with
  pytest fixtures for docker‑compose stack (RustFS, Prefect). Tests verify the
  full pipeline: Canvas download → workspace preparation → Docker execution →
  result collection → Canvas upload.
- **CI/CD Pipeline**: Added GitHub Actions workflow for automated testing with
  RustFS service, unit tests, integration tests, and e2e tests.
- **Production Configuration**: Updated Prefect S3 block registration to support
  custom endpoints via `AwsClientParameters`.

---

This migration plan keeps scope narrow, focuses on essential parity, and paves
the way for Prefect‑based orchestration without overengineering.
