# Authoring Grader Tests

Write grader tests that evaluate student submissions. This guide shows you how
to create a minimal grader script, test it locally, and deploy it to Canvas Code
Correction.

## Quick Start: A Minimal Grader That Works Immediately

The same example is checked into the repo at
`examples/count-submitted-files/` so you can run it directly.

Copy the following Python script to a file named `grader.py`. This grader lists
the submission files, awards one point, and writes feedback.

```python
import json
import os
from pathlib import Path


RESULTS_PATH = Path(os.getenv("CCC_RESULTS_FILE", "results.json"))
POINTS_PATH = Path(os.getenv("CCC_POINTS_FILE", "points.txt"))
COMMENTS_PATH = Path(os.getenv("CCC_COMMENTS_FILE", "comments.txt"))
WORKSPACE_ROOT = Path(os.getenv("CCC_WORKSPACE_DIR", Path.cwd()))


def submission_files(root: Path) -> list[str]:
    """Return sorted relative paths of all files under `root`."""
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )


def write_outputs(files: list[str]) -> None:
    """Write the three required output files."""
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

### Test the Grader Locally with a Mock Submission

Create a mock submission directory and run the grader to see the outputs.

```bash
# Create a temporary workspace
$ mkdir -p /tmp/test_workspace/submission
$ echo "print('hello')" > /tmp/test_workspace/submission/hello.py
$ echo "# README" > /tmp/test_workspace/submission/README.md

# Set the environment variables the grader expects
$ export CCC_WORKSPACE_DIR=/tmp/test_workspace
$ export CCC_RESULTS_FILE=/tmp/test_workspace/results.json
$ export CCC_POINTS_FILE=/tmp/test_workspace/points.txt
$ export CCC_COMMENTS_FILE=/tmp/test_workspace/comments.txt

# Run the grader
$ cd /tmp/test_workspace && python grader.py

# Examine the outputs
$ cat /tmp/test_workspace/results.json
{
  "files": ["README.md", "hello.py"],
  "total": 2
}
$ cat /tmp/test_workspace/points.txt
1
$ cat /tmp/test_workspace/comments.txt
Sample grader succeeded.
Discovered files:
  - README.md
  - hello.py
```

The grader has produced the three required outputs: a JSON results file, a
points file, and a plain‑text comment file. Canvas Code Correction will collect
these files when the grader runs inside a container.

## Execution Context: How Your Grader Runs

Each student submission is evaluated in a fresh Ubuntu container. Your grader
script is invoked with a predefined **workspace layout** and a set of
**environment variables**.

### Workspace Layout

```
/workspace
├── submission/          # Extracted files from the Canvas submission
├── results.json         # JSON payload returned to CCC (created by your script)
├── points.txt           # One numeric score per line (created by your script)
└── comments.txt         # Plain‑text feedback for the student (created by your script)
```

### Environment Variables

| Variable            | Default                   | Purpose                                                |
| ------------------- | ------------------------- | ------------------------------------------------------ |
| `CCC_WORKSPACE_DIR` | `/workspace`              | Root directory of the mounted workspace.               |
| `CCC_RESULTS_FILE`  | `/workspace/results.json` | Path where your script must write the JSON results.    |
| `CCC_POINTS_FILE`   | `/workspace/points.txt`   | Path for the point(s) awarded (one value per line).    |
| `CCC_COMMENTS_FILE` | `/workspace/comments.txt` | Path for the plain‑text feedback shown to the student. |

!!! note
    The container is ephemeral. Your grader should not rely on any state
    from previous submissions.

## Writing Your Own Grader

Start from the minimal grader above and replace or extend the `submission_files`
and `write_outputs` functions.

### Example: Run a Python Test Suite

Suppose you want to run `pytest` on the submission and capture the output.

```python
import subprocess
import sys


def run_pytest(submission_root: Path) -> tuple[int, str]:
    """Run pytest in the submission directory and return (exit_code, stdout)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v"],
        cwd=submission_root,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout


def grade_python_assignment(submission_root: Path) -> tuple[float, str]:
    """Grade a Python submission using pytest."""
    exit_code, output = run_pytest(submission_root)
    if exit_code == 0:
        points = 1.0
        comment = "All tests passed.\n" + output
    else:
        points = 0.0
        comment = "Some tests failed.\n" + output
    return points, comment
```

Integrate this into the `main` function:

```python
def main() -> None:
    submission_root = WORKSPACE_ROOT / "submission"
    if not submission_root.exists():
        raise SystemExit("submission directory missing")

    points, comment = grade_python_assignment(submission_root)

    # Write the three output files
    RESULTS_PATH.write_text(json.dumps({"points": points, "comment_preview": comment[:200]}))
    POINTS_PATH.write_text(f"{points}\n")
    COMMENTS_PATH.write_text(comment)
```

### Example: Check for Required Files

```python
def check_required_files(submission_root: Path, required: list[str]) -> list[str]:
    """Return list of missing required files."""
    missing = []
    for name in required:
        if not (submission_root / name).exists():
            missing.append(name)
    return missing


def main() -> None:
    submission_root = WORKSPACE_ROOT / "submission"
    missing = check_required_files(submission_root, ["main.py", "README.md"])
    if missing:
        comment = f"Missing required files: {', '.join(missing)}"
        points = 0.0
    else:
        comment = "All required files present."
        points = 1.0

    RESULTS_PATH.write_text(json.dumps({"missing": missing}))
    POINTS_PATH.write_text(f"{points}\n")
    COMMENTS_PATH.write_text(comment)
```

## Sample Outputs and Validation

Your grader must create three output files. The formats are simple but strict.

### `results.json`

A JSON payload that Canvas Code Correction stores alongside the grade. You can
put any structured data here; the system does not interpret it. Use this to
record detailed metrics for later analysis.

Example:

```json
{
  "files": ["README.md", "src/main.py"],
  "total": 2
}
```

### `points.txt`

One numeric score per line (usually a single line). Decimals are allowed.

```text
1
```

Or, for partial credit:

```text
0.75
```

### `comments.txt`

Plain‑text feedback that the student will see in Canvas. Keep it concise and
helpful.

```text
All tests passed. Good work!

Detailed test output:
test_add (test_calc.TestCalc) ... ok
test_sub (test_calc.TestCalc) ... ok
```

## Tips and Best Practices

- **Test locally first.** Use the mock‑submission technique shown in the Quick
  Start to verify your grader works before deploying.
- **Keep the grader self‑contained.** The container has Python 3.13 and the
  packages listed in your course’s `requirements.txt`. Do not rely on external
  network access.
- **Write informative comments.** Students see the contents of `comments.txt`.
  Explain what they did well and what needs improvement.
- **Use the results JSON for debugging.** Store intermediate values (e.g., test
  counts, lint scores) to help you diagnose grading issues later.
- **One submission per execution.** The orchestrator launches a fresh container
  for every submission. Your grader should not assume any state from previous
  runs.

## Next Steps

- See [Configuring a Course](../tutorials/02-configuring-a-course.md) to connect
  your grader to a Canvas assignment.
- Explore the [API Reference](../api/) for advanced integration options.
- Check the [Troubleshooting](../troubleshooting/) guide if your grader does not
  produce the expected results.
