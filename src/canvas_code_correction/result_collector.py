"""Utilities for collecting grader results from the workspace."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

POINTS_FILENAME = "points.txt"
COMMENTS_FILENAME = "comments.txt"
RESULTS_FILENAME = "results.json"
FEEDBACK_ARCHIVE_NAME = "submission_feedback"


@dataclass
class CollectedResults:
    """Structured representation of grader outputs."""

    points: float
    points_breakdown: list[float]
    comment: str
    feedback_zip: Path | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_payload(self) -> dict[str, Any]:
        payload = {
            "points": self.points,
            "points_breakdown": self.points_breakdown,
            "comment": self.comment,
            "feedback_zip": self.feedback_zip.as_posix() if self.feedback_zip else None,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


def collect_results(workspace: Path, runner_payload: dict[str, Any]) -> CollectedResults:
    """Aggregate grader outputs into a single structure."""

    workspace = workspace.resolve()
    points_file = _resolve_file(workspace, runner_payload.get("points_file"), POINTS_FILENAME)
    comment_file = _resolve_file(workspace, runner_payload.get("comments_file"), COMMENTS_FILENAME)
    results_file = _resolve_file(workspace, runner_payload.get("results_file"), RESULTS_FILENAME)

    points_breakdown: list[float] = []
    if points_file and points_file.exists():
        raw_lines = points_file.read_text(encoding="utf-8").splitlines()
        lines = [line.strip() for line in raw_lines if line.strip()]
        for line in lines:
            try:
                points_breakdown.append(float(line))
            except ValueError:
                continue
    points = sum(points_breakdown)

    comment = ""
    if comment_file and comment_file.exists():
        comment = comment_file.read_text(encoding="utf-8")

    metadata: dict[str, Any] = {}
    if results_file and results_file.exists():
        try:
            metadata["results"] = json.loads(results_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            metadata["results_raw"] = results_file.read_text(encoding="utf-8")

    submission_dir = workspace / "submission"
    feedback_zip: Path | None = None
    if submission_dir.exists():
        archive_base = workspace / FEEDBACK_ARCHIVE_NAME
        shutil.make_archive(str(archive_base), "zip", submission_dir)
        feedback_zip = archive_base.with_suffix(".zip")

    metadata.setdefault("runner", runner_payload)

    return CollectedResults(
        points=points,
        points_breakdown=points_breakdown,
        comment=comment,
        feedback_zip=feedback_zip,
        metadata=metadata,
    )


def _resolve_file(workspace: Path, payload_path: str | None, default_name: str) -> Path | None:
    candidates: list[Path] = []
    if payload_path:
        candidates.append(Path(payload_path))
    candidates.append(workspace / default_name)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
