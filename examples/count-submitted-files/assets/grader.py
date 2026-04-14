"""Example grader that counts submitted files."""

import json
import os
from pathlib import Path

WORKSPACE_ROOT = Path(os.getenv("CCC_WORKSPACE_DIR", Path.cwd()))
RESULTS_PATH = Path(os.getenv("CCC_RESULTS_FILE", WORKSPACE_ROOT / "results.json"))
POINTS_PATH = Path(os.getenv("CCC_POINTS_FILE", WORKSPACE_ROOT / "points.txt"))
COMMENTS_PATH = Path(os.getenv("CCC_COMMENTS_FILE", WORKSPACE_ROOT / "comments.txt"))


def submission_files(root: Path) -> list[str]:
    """Return sorted relative paths for every submitted file."""
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def main() -> None:
    """Count submitted files and write the standard CCC outputs."""
    submission_root = WORKSPACE_ROOT / "submission"
    if not submission_root.exists():
        msg = "submission directory missing"
        raise SystemExit(msg)

    files = submission_files(submission_root)
    RESULTS_PATH.write_text(json.dumps({"files": files, "total": len(files)}), encoding="utf-8")
    POINTS_PATH.write_text("1\n", encoding="utf-8")

    message = [f"Counted {len(files)} submitted file(s)."]
    if files:
        message.extend(f"  - {name}" for name in files)
    else:
        message.append("  (no files found)")

    COMMENTS_PATH.write_text("\n".join(message) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
