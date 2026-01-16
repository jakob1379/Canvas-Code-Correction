"""Minimal grader script that reports the submission file list."""

from __future__ import annotations

import json
import os
from pathlib import Path

RESULTS_PATH = Path(os.getenv("CCC_RESULTS_FILE", "results.json"))
POINTS_PATH = Path(os.getenv("CCC_POINTS_FILE", "points.txt"))
COMMENTS_PATH = Path(os.getenv("CCC_COMMENTS_FILE", "comments.txt"))
WORKSPACE_ROOT = Path(os.getenv("CCC_WORKSPACE_DIR", Path.cwd()))


def submission_files(root: Path) -> list[str]:
    """Return sorted list of file paths relative to root."""
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def write_outputs(files: list[str]) -> None:
    """Write results, points, and comments files."""
    RESULTS_PATH.write_text(json.dumps({"files": files, "total": len(files)}))
    POINTS_PATH.write_text("1\n")

    message = ["Sample grader succeeded.", "Discovered files:"]
    if files:
        message.extend(f"  - {name}" for name in files)
    else:
        message.append("  (no files found)")

    COMMENTS_PATH.write_text("\n".join(message) + "\n")


def main() -> None:
    """Main entry point for the example grader."""
    submission_root = WORKSPACE_ROOT / "submission"
    if not submission_root.exists():
        raise SystemExit("submission directory missing")  # noqa: TRY003, EM101

    files = submission_files(submission_root)
    write_outputs(files)


if __name__ == "__main__":
    main()
