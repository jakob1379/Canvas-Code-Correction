# Canvas-Code-Correction — Architecture and Usage

Summary

- Repository: Canvas-Code-Correction
- Purpose: A local framework to automate downloading student submissions from Canvas, run user-supplied correction code per submission, collect scores and logs, zip feedback, and upload comments and grades back to Canvas. It also supports plotting scores and basic plagiarism checks.
- Main languages/tools: Bash for orchestration and per-submission workflow; Python for Canvas API interactions, downloading/uploading, and plotting; small helper utilities. Uses canvasapi, pandas, seaborn, p-tqdm, etc.

High-level behavior / workflow

The top-level orchestrator (canvas-code-correction.sh) deletes old local submissions, downloads new submissions from Canvas, unzips them, copies instructor correction code into each student's folder, runs main.sh (user-provided tests/auto-checks) for each student (optionally sandboxed via firejail and timed out), creates per-student result files and zips, then uploads comments and grades, and finally plots course statistics.

Files of interest (core)

- canvas-code-correction.sh — top-level orchestrator. Runs the whole routine and supports daemon mode, repeated runs, timing and verbosity flags.
- download_submissions.py — downloads selected submissions from Canvas and writes them into folder structure: <assignment>/submissions/<student-folder>/
- submissions_unzip.py — unzips each downloaded .zip in a submissions folder and normalizes overhead folders (moves files one level up).
- process_submissions.sh — iterates assignments found with both code/ and submissions/ and calls submissions_unzip.sh and submissions_correcting.sh.
- submissions_correcting.sh — core per-submission runner. Copies the instructor-provided code folder into each student's submission directory, runs their main.sh (with timeout and optional firejail sandbox), writes points and comment files, zips results.
- zip_submission (shell script) — zips the per-student feedback files to produce <student>+.zip to be uploaded as comment attachment.
- upload_comments.py — uploads the zip (feedback) as a submission comment to the Canvas submission (checks by filename/md5 to avoid duplicates).
- upload_grades.py — reads <student>_points.txt, converts points to Canvas grades according to config.ini and posts grades.
- plot_scores.py — fetches Canvas grade data and produces plots/statistics (saves to scores.pdf by default).
- hclust.py & plagiarism-check.sh / mossum usage — basic similarity/plagiarism analysis, and produces cluster heatmaps.
- canvas_helpers.py — utility functions (download_url, md5sum, create_file_name, init_canvas_course, etc.)
- config2shell — converts config.ini into a bash associative array persistent file (.config_array); used by the shell correction scripts.
- requirements.txt / pyproject.toml — Python dependencies.

Configuration

- config.ini (not included in repo view) holds:
  - DEFAULT section: apiurl, token, courseid, sandbox yes/no, MAXTIME, etc.
  - scores_to_complete section: threshold per-assignment for pass/complete.
- You initialize config via init-config.sh (documented in README).
- Each assignment folder must contain a code/ directory with the instructor's correction code; that code must include a main.sh which runs the tests and produces:
  - <handin>_points.txt — required to upload grades (one file with numeric point entries).
  - <handin>.txt — human-readable comments/feedback.
  - errors.log (optional)
- The orchestrator copies the code folder into each student's submission before running.

Typical filesystem layout created/used

- <assignment>/
  - code/                <- instructor correction code, must include main.sh
  - submissions/
    - <student-folder>/
      - (student files extracted)
      - <handin>_points.txt  <- produced by correction process
      - <handin>.txt         <- produced by correction process (comments)
      - errors.log
      - <handin>+.zip        <- zipped feedback (created by zip_submission)

How to use (examples)

- Run entire routine once (downloads, corrects, upload comments & grades, plot):
  - ./src/canvas-code-correction.sh
- Download submissions only:
  - python3 src/download_submissions.py --type new
- Unzip submissions in an assignment:
  - python3 src/submissions_unzip.py myAssignment
- Upload comments (parallel, interactive):
  - python3 src/upload_comments.py -p -q
- Upload grades:
  - python3 src/upload_grades.py -v
- Plot scores:
  - python3 src/plot_scores.py -v

Concurrency & robustness

- Many scripts support parallelism via p_tqdm (p_map/p_umap) or forking from shell (submissions_correcting.sh uses a process limit).
- Timeout is enforced via timeout command; optional sandboxing via firejail if enabled in config.ini.
- md5 checks and comment filename checks are used to avoid re-uploading identical feedback (upload_comments.py).

Security notes

- The framework supports optional sandboxing (firejail) and timeouts to limit malicious student code. However, you must configure sandboxing in config.ini and have firejail installed. There is still risk if sandbox is off.
- The framework requires a Canvas API token (in config.ini). Keep the token safe.

Detailed flow diagrams (Mermaid)

Sequence diagram (UML-style)

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator as canvas-code-correction.sh
    participant Download as download_submissions.py
    participant LocalFS as Local filesystem
    participant Unzip as submissions_unzip.py
    participant Processor as submissions_correcting.sh
    participant InstructorCode as assignment/code (main.sh)
    participant Zip as zip_submission
    participant UploadComments as upload_comments.py
    participant UploadGrades as upload_grades.py
    participant CanvasAPI as Canvas (canvasapi)

    User->>Orchestrator: run ./canvas-code-correction.sh
    Orchestrator->>Download: python download_submissions.py (--type ...)
    Download->>CanvasAPI: query assignments & submissions
    CanvasAPI-->>Download: submission list and attachment URLs
    Download->>LocalFS: save <assignment>/submissions/<student>/*.zip
    Orchestrator->>Unzip: python submissions_unzip.py (per assignment)
    Unzip->>LocalFS: unpack .zip -> <student>/ (normalize)
    Orchestrator->>Processor: bash process_submissions.sh -> submissions_correcting.sh
    Processor->>LocalFS: for each <student> copy assignment/code -> student folder
    Processor->>InstructorCode: run main.sh (timeout & optional firejail)
    InstructorCode-->>Processor: produces <handin>_points.txt, .txt, errors.log
    Processor->>Zip: zip_submission -> <handin>+.zip
    Zip->>LocalFS: create zip files
    Orchestrator->>UploadComments: python upload_comments.py
    UploadComments->>CanvasAPI: check existing submission comments (attachments)
    UploadComments->>CanvasAPI: upload comment with <handin>+.zip
    Orchestrator->>UploadGrades: python upload_grades.py
    UploadGrades->>CanvasAPI: edit submission.posted_grade per student
    Orchestrator->>LocalFS: python plot_scores.py -> scores.pdf
    User<<--Orchestrator: routine finished (logs, plots)
```

Component diagram (module / UML component view)

```mermaid
graph TB
  subgraph LocalRepo
    A[canvas-code-correction.sh] --> B[process_submissions.sh]
    B --> C[submissions_correcting.sh]
    A --> D[download_submissions.py]
    A --> E[upload_comments.py]
    A --> F[upload_grades.py]
    A --> G[plot_scores.py]
    C --> H[assignment/code/main.sh]
    D --> I[canvas_helpers.py]
    E --> I
    F --> I
    G --> I
    C --> J[submissions_unzip.py]
    A --> K[config2shell / config.ini]
    C --> K
    E --> L[tmp/ (md5 downloads)]
    C --> M[zip_submission]
  end

  CanvasAPI[(Canvas)]
  LocalFS[(Filesystem)]

  D -->|fetch attachments| CanvasAPI
  E -->|upload comments| CanvasAPI
  F -->|post grades| CanvasAPI
  C -->|read/write| LocalFS
  D -->|write zips| LocalFS
```

Important implementation details & locations to modify

- Where to put grading code: For each assignment folder, create code/ with the correction script and a single main.sh entrypoint. That script is copied into each student's folder prior to execution.
- Naming: create_file_name in canvas_helpers constructs student folder names. Filenames include user id and attachment id to ensure uniqueness.
- Output contract required by upload_grades.py:
  - The per-student points file must be named <handin>_points.txt and should contain numeric values (can be multiple lines — the upload script sums them).
  - The human feedback should be written to <handin>.txt for viewing.
- config2shell reads config.ini and writes .config_array, which is sourced by submissions_correcting.sh to make config available to correction scripts.

Caveats, gotchas, and suggestions

- Because the framework runs untrusted code (student submissions), enable sandboxing (firejail) in config.ini and ensure firejail is installed. Timeouts are also configured via MAXTIME in config.ini.
- Make sure the Canvas token has permission to read submissions and post comments/grades.
- If multiple submissions per student exist, the scripts pick the first attachment and construct folder names — check create_file_name if your Canvas naming conventions differ.
- Plagiarism: moss/mossum recommended in README; plagiarism-check.sh ties into that. Running plagiarism checks requires installing mossum and probably connectivity to their service.
- Tests are not included; if you want automated testing, adding small unit tests around canvas_helpers can help.
