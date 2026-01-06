# Phase 2 – Canvas Client Migration Plan

This document captures the current state of the legacy automation, the canonical
data/flow requirements we must preserve, and the concrete steps for the
Prefect-based rewrite.

## 1. Legacy feature inventory

The existing bash + Python tooling in `src/` provides the reference behaviour we
need parity with:

| Scope                                   | Current implementation                                                                             | Notes for parity                                                                                       |
| --------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Assignment discovery & folder bootstrap | `setup-assignment-folders.sh`, `init-config.sh`                                                    | Reads Canvas via `canvas_helpers` and populates local directories + `.config_array`.                   |
| Submission download                     | `download_submissions.py`                                                                          | Supports filtering (state, assignment, student), pagination, md5-based file naming.                    |
| Extraction/normalisation                | `submissions_unzip.py`, `process_submissions.sh`                                                   | Handles zip unpacking, flattens nested folders.                                                        |
| Grading execution                       | `submissions_correcting.sh`, user-provided `code/main.sh`, optional firejail, timeout, parallelism | Consumes config values, copies instructor `code/` into each submission, captures logs/points/comments. |
| Result packaging                        | `zip_submission`, `submissions_correcting.sh`                                                      | Produces `<handin>+.zip` artefacts and `<handin>_points.txt`.                                          |
| Comment upload                          | `upload_comments.py`                                                                               | Idempotent via md5 + filename checks; attaches zipped feedback.                                        |
| Grade upload                            | `upload_grades.py`                                                                                 | Reads points file(s), applies config-specified grading mode (score vs complete).                       |
| Cleanup                                 | `delete_submissions.py`                                                                            | Removes local submissions when desired.                                                                |
| Analytics                               | `plot_scores.py`, `hclust.py`, `plagiarism-check.sh`                                               | Non-critical for MVP but worth preserving hooks.                                                       |

Supporting utilities:

- `canvas_helpers.py` – shared Canvas API helper (init course, get assignments,
  md5 hashing).
- `config2shell`/`.config_array` – bridges INI → bash arrays.
- `canvas-code-correction.sh` – end-to-end orchestrator (daemon/batch modes).

## 2. Course fixture & test data

- All functional tests rely on the shared Canvas dev course at
  <https://canvas.instructure.com/courses/13121974>.
- Tokens and course identifiers are provided via the project-level `.env` (e.g.
  `CANVAS_API_TOKEN`, `CANVAS_COURSE_ID`).
- The repository should not depend on static IMSCC exports; instead, test data
  is retrieved dynamically from the dev course via the Canvas API.
- When additional fixtures are required, seed data using Canvas API calls or
  manual setup in the dev course, then capture the resulting IDs in `.env` for
  repeatability.

## 3. Target architecture (Prefect-driven)

Core components to implement in Python:

1. **CanvasClient** – thin wrapper around Canvas REST API with retry/backoff and
   typed responses (leveraging `canvasapi` or `httpx`).
2. **SubmissionStore** – manages local filesystem workspace
   (`var/runs/<assignment>/<submission>`), mirrors download/unzip contract.
3. **Runner** – executes grading inside a clean container (Docker image
   configurable in `.env`/settings). Responsible for:
   - Mounting the workspace read/write.
   - Injecting instructor correction code and student submission.
   - Enforcing time/resource limits (CPU, memory, network toggle).
4. **ResultCollector** – normalises grader outputs into the expected
   `points.txt`, `comments.txt`, `artifacts/` structure.
5. **Uploader** – uploads comments and grades idempotently, maintaining audit
   logs.
6. **Reporter** – optional analytics hook (e.g., grade summary CSV, plot
   triggers).

Prefect orchestration outline:

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

## 4. Incremental implementation steps

1. **Configuration groundwork (Day 0–1)** ✅
   - Settings now sourced exclusively from environment variables (with Canvas
     Cloud defaults) and validated via `Settings` models.
2. **Canvas client & download (Day 1–2)** ✅
   - `CanvasClient` now wraps `canvasapi` objects for submission metadata and
     attachment download with accompanying unit tests.
3. **Workspace preparation (Day 2)** ✅
   - `SubmissionStore` handles extraction/normalisation with coverage via
     synthetic zip fixtures.
4. **Runner integration (Day 3–4)** ✅
   - **Completed**: `GraderExecutor` executes instructor commands inside Docker
     containers with workspace mounts, resource limits, and course-specific
     configuration from Prefect blocks. Provides secure execution with non-root
     users, network isolation, and timeout handling.
   - **Completed**: `ResultCollector` packages grader outputs (`points.txt`,
     `comments.txt`, zipped feedback, `results.json`) for downstream upload and
     metadata tracking. Supports various points file formats and robust error
     handling.
5. **Uploader tasks (Day 4–5)** ✅
   - **Completed**: `CanvasUploader` provides idempotent feedback and grade
     uploads with MD5 duplicate detection. Integrates with Prefect tasks and
     reuses `CanvasClient`.
6. **End-to-end Prefect flow (Day 5–6)** ✅
   - **Completed**: `correct_submission_flow` now integrates all components:
     download, workspace preparation, runner execution, result collection, and
     uploads. The flow includes tasks `execute_grader`, `collect_results`,
     `upload_feedback`, and `post_grade`.
7. **Testing & docs (Day 6–7)** ✅
   - Unit test suite (`uv run --group tests pytest`) and full pre-commit hooks
     executed successfully on 2025-10-14; coverage includes Canvas client,
     workspace preparation, download tasks, execution layer, result collector,
     uploader, and flow orchestration. All unit tests pass as of January 2026.
   - Prefect Assets integration investigated: dynamic per-submission asset keys
     are not yet required for MVP; revisit in Phase 3 when run cataloguing is
     prioritised.

## 5. Non-goals for this iteration

- Automated Canvas course cloning/reset (remains manual).
- Webhook listener/service deployment (can follow once core workflow is stable).
- Full analytics/visualisation parity (plotting, similarity) — defer until core
  grading loop is stable.
- Multi-run scheduling/daemon replacement — to be addressed after single-run
  path is reliable.

## 6. Open questions / follow-ups

1. **Instructor code packaging** – store in repo, S3, or separate artifact?
   (short-term: repository folder copied into workspace).
2. **Secrets management** – continue with local `.env`, but plan migration to
   Prefect blocks / Vault later.
3. **Container image build pipeline** – need CI job to build/publish grader
   image tagged with repo commit.
4. **Student code limits** – confirm CPU/memory/time defaults with teaching
   team; codify in settings.
5. **Roll-forward strategy** – plan data migration for existing feedback
   archives (if needed).
6. **Prefect assets cataloguing** – revisit in Phase 3 once long-term run
   lineage requirements are defined.
7. **CI & operational runbooks** – document Prefect worker setup and add CI
   pipelines to execute tests/linters before Phase 3 launch.

## 7. Recent Updates (January 2026)

- **RustFS Integration**: Added configurable RustFS S3-compatible storage support
  via environment variables (`RUSTFS_ENDPOINT`, `RUSTFS_ACCESS_KEY`, `RUSTFS_SECRET_KEY`,
  `RUSTFS_BUCKET_NAME`, `RUSTFS_PREFIX`). Updated `setup-rustfs.py` script and
  documentation.
- **Comprehensive Test Suite**: Added end-to-end test suite (`tests/e2e/`) with
  pytest fixtures for docker-compose stack (RustFS, Prefect). Tests verify full
  pipeline: Canvas download → workspace preparation → Docker execution → result
  collection → Canvas upload.
- **CI/CD Pipeline**: Added GitHub Actions workflow for automated testing with
  RustFS service, unit tests, integration tests, and e2e tests.
- **Production Configuration**: Updated Prefect S3 block registration to support
  custom endpoints via `AwsClientParameters`.

---

This plan keeps scope narrow, focuses on essential parity, and paves the way for
Prefect-based orchestration without overengineering.
