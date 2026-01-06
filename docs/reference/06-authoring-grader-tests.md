# Authoring Grader Tests

Course staff only need to implement the grading logic for a single assignment.
The runner container provides a clean Ubuntu workspace and calls your script or
test suite for each submission.

## Execution Context

- Base image: `ubuntu:latest` extended with Python via the shared grader image.
- Working directory: `/workspace`.
- Submission contents: `/workspace/submission` contains the extracted files for
  the current Canvas submission.

!!! note "CCC environment variables"

    <ul>
      <li><code>CCC_WORKSPACE_DIR</code>: <code>/workspace</code> — root directory mounted for the run.</li>
      <li><code>CCC_RESULTS_FILE</code>: <code>/workspace/results.json</code> — JSON payload returned to CCC.</li>
      <li><code>CCC_POINTS_FILE</code>: <code>/workspace/points.txt</code> — points (one value per line).</li>
      <li><code>CCC_COMMENTS_FILE</code>: <code>/workspace/comments.txt</code> — plain-text feedback for the student.</li>
    </ul>

!!! warning "Grade one submission per execution"

    The orchestrator launches a fresh container for every assignment submission. Author tests that focus on the current submission only and avoid any cross-submission state.

## Sample Grader

The repository includes `legacy/examples/file_listing_grader.py`, which lists
submission files, awards a passing score, and records a short comment. Use it as
your template and adapt the helper functions to suit your course needs.

```python
from __future__ import annotations

import json
import os
from pathlib import Path


RESULTS_PATH = Path(os.getenv("CCC_RESULTS_FILE", "results.json"))
POINTS_PATH = Path(os.getenv("CCC_POINTS_FILE", "points.txt"))
COMMENTS_PATH = Path(os.getenv("CCC_COMMENTS_FILE", "comments.txt"))
WORKSPACE_ROOT = Path(os.getenv("CCC_WORKSPACE_DIR", Path.cwd()))


def submission_files(root: Path) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )


def write_outputs(files: list[str]) -> None:
    RESULTS_PATH.write_text(json.dumps({"files": files, "total": len(files)}))
    POINTS_PATH.write_text("1\n")

    message = ["Sample grader succeeded.", "Discovered files:"]
    if files:
        message.extend(f"  - {name}" for name in files)
    else:
        message.append("  (no files found)")

    COMMENTS_PATH.write_text("\n".join(message) + "\n")


def main() -> None:
    submission_root = WORKSPACE_ROOT / "submission"
    if not submission_root.exists():
        raise SystemExit("submission directory missing")

    files = submission_files(submission_root)
    write_outputs(files)


if __name__ == "__main__":
    main()
```

### Sample Outputs

_`results.json`_

```json
{
  "files": ["README.md", "src/main.py"],
  "total": 2
}
```

_`points.txt`_

```text
1
```

_`comments.txt`_

```text
Sample grader succeeded.
Discovered files:
  - README.md
  - src/main.py
```

!!! tip "Extend with your own checks"

    Replace `submission_files` or add new helpers to run pytest suites, execute scripts, or perform custom assertions. Ensure the three output files remain in place so CCC can collect scores and comments.
