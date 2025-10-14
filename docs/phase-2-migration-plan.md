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
      → Task: run_grader_container (Runner)
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
4. **Runner integration (Day 3–4)** ⏳
   - Prototype Prefect task that spins up Docker container (`docker SDK` or
     Prefect Docker task collection) with workspace mount and env vars.
   - Ensure results contract (`points.txt`, `comments.txt`, zipped feedback)
     matches legacy output.
   - Phase 1.5 Compose sandbox work (PR
     [#1313](https://github.com/jakob1379/Canvas-Code-Correction/pull/1313))
     merged; Prefect task still needs to invoke the runner image instead of
     returning a placeholder payload.
   - Runner configuration (image, limits) resolves from Prefect blocks so each
     course can bring its own grading environment without code changes.
5. **Uploader tasks (Day 4–5)**
   - Port `upload_comments.py` and `upload_grades.py` into reusable async tasks
     with retries.
   - Maintain md5/idempotency checks.
6. **End-to-end Prefect flow (Day 5–6)** ⏳
   - Flow skeleton in place (`correct_submission_flow`) with download and
     workspace staging; grader container execution still stubbed pending runner
     integration.
7. **Testing & docs (Day 6–7)** ⏳
   - Unit tests cover settings, Canvas client, flows, and submission store; CI
     workflow and operational docs still outstanding.

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

---

This plan keeps scope narrow, focuses on essential parity, and paves the way for
Prefect-based orchestration without overengineering.
