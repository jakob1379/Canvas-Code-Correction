"""Placeholder grader runner executed inside the grader container."""

from __future__ import annotations

import json
import os
from pathlib import Path

RESULTS_FILE = Path(os.getenv("CCC_RESULTS_FILE", "results.json"))
POINTS_FILE = Path(os.getenv("CCC_POINTS_FILE", "points.txt"))
COMMENTS_FILE = Path(os.getenv("CCC_COMMENTS_FILE", "comments.txt"))


def main() -> None:
    workspace = Path.cwd()
    RESULTS_FILE.write_text(json.dumps({"status": "not-implemented", "workspace": str(workspace)}))
    POINTS_FILE.write_text("0\n")
    COMMENTS_FILE.write_text("Autograder placeholder: no feedback generated.\n")


if __name__ == "__main__":  # pragma: no cover
    main()
