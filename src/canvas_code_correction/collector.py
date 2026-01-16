"""Collects and packages grader results for upload to Canvas."""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

ERRORS_LOG_FILENAME = "errors.log"


class GradingResult(BaseModel):
    """Structured result of a grading run ready for upload."""

    points: float
    points_file_content: str
    comments: str | None = None
    comments_file_path: Path | None = None
    artifacts_zip_path: Path | None = None
    errors_log_path: Path | None = None
    metadata: dict[str, Any] = {}


@dataclass(frozen=True)
class CollectionResult:
    """Aggregated collection results with all discovered files."""

    grading_result: GradingResult
    discovered_files: list[Path]
    workspace_root: Path


class ResultCollector:
    """Collects grader outputs and prepares them for upload."""

    _MAX_POINTS = 1000  # Arbitrary high limit for validation

    def __init__(self, workspace_root: Path) -> None:
        """Initialize collector with workspace root directory."""
        self.workspace_root = workspace_root

    def _find_points_file(self, submission_dir: Path) -> Path:
        """Find points file in submission directory."""
        points_files = list(submission_dir.glob("*_points.txt"))
        if not points_files:
            points_files = list(submission_dir.glob("points.txt"))
        if not points_files:
            msg = f"No points file found in {submission_dir}"
            raise FileNotFoundError(msg)
        return points_files[0]

    def _find_comments_file(
        self,
        submission_dir: Path,
        submission_dir_name: str | None,
    ) -> tuple[Path | None, str | None]:
        """Find comments file and read its content."""
        comments_file = None
        comments = None
        if submission_dir_name:
            comments_file_candidate = submission_dir / f"{submission_dir_name}.txt"
            if comments_file_candidate.exists():
                comments_file = comments_file_candidate
        else:
            txt_files = [
                f
                for f in submission_dir.glob("*.txt")
                if not f.name.endswith("_points.txt") and f.name != ERRORS_LOG_FILENAME
            ]
            if txt_files:
                comments_file = txt_files[0]
        if comments_file and comments_file.exists():
            comments = comments_file.read_text(
                encoding="utf-8",
                errors="replace",
            )
        return comments_file, comments

    def _find_artifacts_zip(self, submission_dir: Path) -> Path | None:
        """Find artifacts zip file."""
        zip_files = list(submission_dir.glob("*.zip"))
        return zip_files[0] if zip_files else None

    def _find_errors_log(self, submission_dir: Path) -> Path | None:
        """Find errors log file."""
        errors_log = submission_dir / ERRORS_LOG_FILENAME
        return errors_log if errors_log.exists() else None

    def collect(
        self,
        submission_dir_name: str | None = None,
    ) -> CollectionResult:
        """Collect all grader outputs from the workspace."""
        submission_dir = self.workspace_root / "submission"
        if not submission_dir.exists():
            msg = f"Submission directory not found: {submission_dir}"
            raise ValueError(
                msg,
            )

        # Determine the base name for files (currently unused, reserved for future naming)
        if submission_dir_name:
            # Could be used to prefix output files in future
            pass

        # Find all relevant files
        discovered_files = list(submission_dir.glob("*"))

        # Find points file and parse points
        points_file = self._find_points_file(submission_dir)
        points = self._parse_points_file(points_file)

        # Find comments file and content
        comments_file, comments = self._find_comments_file(
            submission_dir,
            submission_dir_name,
        )

        # Find artifacts zip
        artifacts_zip = self._find_artifacts_zip(submission_dir)

        # Find errors log
        errors_log = self._find_errors_log(submission_dir)

        # Create grading result
        grading_result = GradingResult(
            points=points,
            points_file_content=points_file.read_text(
                encoding="utf-8",
                errors="replace",
            ),
            comments=comments,
            comments_file_path=comments_file,
            artifacts_zip_path=artifacts_zip,
            errors_log_path=errors_log,
            metadata={
                "points_file": str(
                    points_file.relative_to(self.workspace_root),
                ),
                "submission_dir": str(
                    submission_dir.relative_to(self.workspace_root),
                ),
            },
        )

        return CollectionResult(
            grading_result=grading_result,
            discovered_files=discovered_files,
            workspace_root=self.workspace_root,
        )

    def _parse_points_file(self, points_file: Path) -> float:  # noqa: C901
        """Parse points file, summing all numbers if multiple lines."""
        content = points_file.read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()
        if not content:
            return 0.0

        lines = content.splitlines()
        total = 0.0
        for line in lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                continue
            try:
                total += float(cleaned_line)
            except ValueError:
                # If it's not a number, try to extract numbers

                # Special handling for fraction format like "25.5/30"
                if "/" in cleaned_line:
                    # Try to parse as numerator/denominator
                    parts = cleaned_line.split("/")
                    if parts:
                        # Try to extract first number from first part
                        nums = re.findall(r"[-+]?\d*\.?\d+", parts[0])
                        if nums:
                            try:
                                total += float(nums[0])
                                continue
                            except ValueError:
                                pass
                # General case: find all numbers and sum them
                numbers = re.findall(r"[-+]?\d*\.?\d+", cleaned_line)
                for num in numbers:
                    try:
                        total += float(num)
                    except ValueError:
                        continue

        return total

    def create_feedback_zip(
        self,
        result: GradingResult,
        output_path: Path | None = None,
        include_errors_log: bool = True,  # noqa: FBT001, FBT002
    ) -> Path:
        """Create a zip file with feedback for upload."""
        if output_path is None:
            output_path = self.workspace_root / "feedback.zip"

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add points file
            if result.points_file_content:
                zipf.writestr("points.txt", result.points_file_content)

            # Add comments if available
            if result.comments:
                zipf.writestr("comments.txt", result.comments)

            # Add errors log if exists and requested
            if include_errors_log and result.errors_log_path and result.errors_log_path.exists():
                zipf.write(result.errors_log_path, ERRORS_LOG_FILENAME)

            # Add metadata as JSON
            metadata = {
                "points": result.points,
                "collected_at": json.dumps(
                    str(Path.cwd()),
                ),  # Simple timestamp placeholder
                "files_included": [],
            }
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

        return output_path

    def validate_result(self, result: GradingResult) -> list[str]:
        """Validate grading result for common issues."""
        issues = []

        if result.points < 0:
            issues.append(f"Negative points value: {result.points}")

        if result.points > self._MAX_POINTS:
            issues.append(f"Unusually high points value: {result.points}")

        if result.artifacts_zip_path and not result.artifacts_zip_path.exists():
            issues.append(
                f"Artifacts zip referenced but not found: {result.artifacts_zip_path}",
            )

        return issues
