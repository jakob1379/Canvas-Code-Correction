# Writing Grader Tests: A Hands-On Tutorial

This tutorial walks you through writing a grader test script for Canvas Code
Correction (CCC). You will create a minimal grader, run it locally, examine
outputs, and extend it with real grading logic.

By the end, you will have a working grader script you can adapt for your course.

## 1. Understand the Workspace Layout

When CCC runs your grader, it executes your script inside a fresh Docker
container with a predefined directory structure:

```
/workspace/
├── submission/          # Extracted Canvas submission files
├── results.json         # Structured results (JSON)
├── points.txt           # Numeric scores (one per line)
└── comments.txt         # Plain-text feedback for the student
```

Key environment variables tell your script where these paths are:

- **`CCC_WORKSPACE_DIR`** – root of the workspace (`/workspace`)
- **`CCC_RESULTS_FILE`** – path to write `results.json`
- **`CCC_POINTS_FILE`** – path to write `points.txt`
- **`CCC_COMMENTS_FILE`** – path to write `comments.txt`

Your script reads student files from the **submission directory** and writes the
three output files.

## 2. Create a Minimal Grader Script

Start with a Python script that verifies the submission directory exists and
awards a point. Copy the entire block below into a file named `grader.py`:

```python
#!/usr/bin/env python3
"""Minimal grader that checks for a submission directory."""

import json
import os
from pathlib import Path

# Read environment variables (fallback defaults for local testing)
WORKSPACE_ROOT = Path(os.getenv("CCC_WORKSPACE_DIR", Path.cwd()))
RESULTS_PATH = Path(os.getenv("CCC_RESULTS_FILE", WORKSPACE_ROOT / "results.json"))
POINTS_PATH = Path(os.getenv("CCC_POINTS_FILE", WORKSPACE_ROOT / "points.txt"))
COMMENTS_PATH = Path(os.getenv("CCC_COMMENTS_FILE", WORKSPACE_ROOT / "comments.txt"))

def main() -> None:
    submission_root = WORKSPACE_ROOT / "submission"

    # 1. Check that the submission directory exists
    if not submission_root.exists():
        raise SystemExit("❌ No submission directory found")

    # 2. List files in the submission
    files = sorted(
        path.relative_to(submission_root).as_posix()
        for path in submission_root.rglob("*")
        if path.is_file()
    )

    # 3. Write the three required output files
    RESULTS_PATH.write_text(json.dumps({"files": files}, indent=2))
    POINTS_PATH.write_text("1\n")

    comment_lines = [
        "✅ Submission received.",
        f"Found {len(files)} file(s):",
    ]
    if files:
        comment_lines.extend(f"  - {name}" for name in files)
    else:
        comment_lines.append("  (no files)")

    COMMENTS_PATH.write_text("\n".join(comment_lines) + "\n")

    print("✅ Grader finished successfully")

if __name__ == "__main__":
    main()
```

This script:

- Locates the **submission directory**
- Lists all files inside it
- Writes a simple JSON summary to **results.json**
- Awards 1 point in **points.txt**
- Provides a readable comment in **comments.txt**

## 3. Run It Locally with a Test Submission

Before deploying, test your grader locally. Create a mock submission directory
and run the script.

### Step 1: Set up a test workspace

```bash
# Create a temporary workspace
mkdir -p /tmp/ccc-test/submission
cd /tmp/ccc-test

# Add some dummy student files
echo "print('Hello, world!')" > submission/main.py
echo "# My Project" > submission/README.md
```

### Step 2: Run the grader

```bash
# Run the grader script (adjust the path to your grader.py)
python3 /path/to/your/grader.py
```

You should see:

```
✅ Grader finished successfully
```

If you see an error, check that the **submission directory** exists and is
readable.

### Step 3: Simulate a missing submission

```bash
# Remove the submission directory to test error handling
rm -rf submission
python3 /path/to/your/grader.py
```

Expected output (to stderr):

```
❌ No submission directory found
```

The script exits with a non‑zero status, which CCC will treat as a grader
failure. Always validate inputs before proceeding.

## 4. Examine Output Files

After a successful run, inspect the three output files in the workspace root:

**`results.json`** – structured data for later analysis

```json
{
  "files": ["README.md", "main.py"]
}
```

**`points.txt`** – one numeric score per line (floating point)

```text
1
```

**`comments.txt`** – plain‑text feedback shown to the student

```text
✅ Submission received.
Found 2 file(s):
  - README.md
  - main.py
```

CCC collects these files and uploads the points and comments to Canvas. The JSON
results are stored for your own reporting.

## 5. Extend for Real Grading Logic

Replace the simple file‑listing logic with your actual grading checks. Below are
common patterns.

### Pattern A: Run unit tests

```python
import subprocess

def run_pytest(submission_root: Path) -> tuple[int, str]:
    """Run pytest and return (exit_code, stdout)."""
    # Install dependencies if needed (use a requirements.txt in your grader image)
    # Then run pytest on the student's code
    result = subprocess.run(
        ["pytest", "-v", "--tb=short"],
        cwd=submission_root,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout
```

### Pattern B: Check for required files

```python
REQUIRED_FILES = {"main.py", "README.md"}

def check_required_files(submission_root: Path) -> list[str]:
    missing = []
    for req in REQUIRED_FILES:
        if not (submission_root / req).exists():
            missing.append(req)
    return missing
```

### Pattern C: Execute student code and compare output

```python
def execute_and_compare(submission_root: Path) -> str:
    """Run student script and compare to expected output."""
    proc = subprocess.run(
        ["python3", submission_root / "main.py"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    actual = proc.stdout.strip()
    expected = "Hello, world!"

    if actual == expected:
        return "✅ Output matches"
    else:
        return f"❌ Expected '{expected}', got '{actual}'"
```

### Putting it all together

Update the `main()` function to call your checks and assign points accordingly:

```python
def main() -> None:
    submission_root = WORKSPACE_ROOT / "submission"
    if not submission_root.exists():
        raise SystemExit("❌ No submission directory found")

    points = 0.0
    comments = []

    # Check for required files
    missing = check_required_files(submission_root)
    if missing:
        comments.append(f"❌ Missing files: {', '.join(missing)}")
    else:
        points += 1.0
        comments.append("✅ All required files present")

    # Run unit tests
    exit_code, pytest_output = run_pytest(submission_root)
    if exit_code == 0:
        points += 4.0
        comments.append("✅ All tests passed")
    else:
        comments.append("❌ Some tests failed")
        # Include the first few lines of pytest output for debugging
        comments.extend(pytest_output.splitlines()[:5])

    # Write outputs
    RESULTS_PATH.write_text(json.dumps({"points_awarded": points}, indent=2))
    POINTS_PATH.write_text(f"{points}\n")
    COMMENTS_PATH.write_text("\n".join(comments) + "\n")
```

## Next Steps

You now have a grader script that works locally. To deploy it:

1. **Package your script** (and any supporting files) in a directory, e.g.,
   `grader/`.
2. **Optionally create a Dockerfile** if you need extra dependencies beyond the
   base `jakob1379/canvas‑grader` image.
3. **Give the package to your CCC platform operator** – they will upload it to
   S3 and configure your course.

For more advanced topics, see the
[Authoring Grader Tests](../reference/06-authoring-grader-tests.md) reference.

Remember: your grader runs once per student submission, in isolation. Keep it
focused on the current submission, and always write the three output files.
