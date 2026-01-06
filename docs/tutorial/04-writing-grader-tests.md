# Writing Grader Tests

Grader tests are scripts that evaluate student submissions. They run inside the grader container and produce results.

## Execution Environment

Each grader test runs in complete isolation, in a fresh Docker container created just for a single student submission. This ensures:

- No cross-contamination between student submissions
- Consistent starting state for every run
- Secure execution with resource limits

### Submission Structure

When the grader runs, Canvas submissions are automatically processed:
- CCC downloads and unzips the Canvas submission package
- The unzipped content is placed in `/workspace/submission/`
- Your test script reads files from this directory

### Canvas Submission Format

Canvas typically provides submissions as ZIP files containing:
- Student-uploaded files (preserving directory structure)
- Sometimes a `__MACOSX/` folder (can be ignored)
- File names and extensions as uploaded by the student

Your grader should handle various submission structures, including:
- Single file uploads
- Multiple file uploads
- ZIP files uploaded as-is (Canvas may double-zip)
- Missing or malformed submissions

### Expected Output Files

CCC expects three output files in the workspace root:

- `results.json`: Structured results (any JSON)
- `points.txt`: One numeric score per line (floating point)
- `comments.txt`: Plain text feedback for the student

## Sample Grader

Here's a simple Python grader that lists submission files and awards a point:

```python
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
    message = ["Grader succeeded.", "Discovered files:"]
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

## Extending for Your Course

Replace the `submission_files` logic with your own checks: run unit tests, style checks, compile code, etc. Ensure your script writes the three output files.

## Packaging Your Work Package

Your work package should include:

1. **Grader test scripts** (required): Place your grader scripts in a directory (e.g., `grader/`)
2. **Dockerfile** (optional): Only needed if the default `jakob1379/canvas-grader:latest` image doesn't contain your required dependencies

Bundle these assets for your **CCC platform operator**:
- Option 1: Create a `.zip` or `.tar.gz` archive
- Option 2: Provide a Git repository URL
- Option 3: Share a directory structure

The platform operator will:
- Upload tests and data to S3 storage (if using RustFS or similar)
- Deploy any custom Docker image to a container registry
- Configure CCC to use your assets

## Next Steps

You now have a complete work package:
- ✅ Grader Docker image (with dependencies, if custom)
- ✅ Grader test scripts (evaluation logic)

Give these assets to your **CCC platform operator** for deployment. They will configure your course, set up scheduling, and monitor results.

For operator documentation, see the **Platform Setup** section.