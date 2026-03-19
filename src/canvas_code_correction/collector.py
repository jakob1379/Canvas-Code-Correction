"""Collects and packages grader results for upload to Canvas."""

import json
import logging
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

ERRORS_LOG_FILENAME = "errors.log"

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonScalar] | dict[str, JsonScalar]

logger = logging.getLogger(__name__)


class CollectionMetadata(BaseModel):
    """Metadata describing collected grader artifacts."""

    points_file: str = ""
    submission_dir: str = ""


class GradingResult(BaseModel):
    """Structured result of a grading run ready for upload."""

    points: float
    points_file_content: str
    comments: str | None = None
    comments_file_path: Path | None = None
    artifacts_zip_path: Path | None = None
    errors_log_path: Path | None = None
    metadata: CollectionMetadata = CollectionMetadata()


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
                if not f.name.endswith("_points.txt")
                and f.name not in (ERRORS_LOG_FILENAME, "points.txt")
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
        zip_files = list(submission_dir.glob("*.zip"))
        return zip_files[0] if zip_files else None

    def _find_errors_log(self, submission_dir: Path) -> Path | None:
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
            raise FileNotFoundError(
                msg,
            )

        discovered_files = list(submission_dir.glob("*"))
        points_file = self._find_points_file(submission_dir)
        points = self._parse_points_file(points_file)
        comments_file, comments = self._find_comments_file(
            submission_dir,
            submission_dir_name,
        )
        artifacts_zip = self._find_artifacts_zip(submission_dir)
        errors_log = self._find_errors_log(submission_dir)
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
            metadata=CollectionMetadata(
                points_file=str(points_file.relative_to(self.workspace_root)),
                submission_dir=str(submission_dir.relative_to(self.workspace_root)),
            ),
        )

        return CollectionResult(
            grading_result=grading_result,
            discovered_files=discovered_files,
            workspace_root=self.workspace_root,
        )

    def _parse_line_numbers(self, line: str) -> list[float]:
        numbers = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", line)
        result = []
        for num in numbers:
            parsed_num = self._parse_float(num)
            if parsed_num is not None:
                result.append(parsed_num)
        return result

    def _parse_float(self, value: str) -> float | None:
        try:
            return float(value)
        except ValueError as exc:
            logger.debug("Ignoring invalid point token: %s", exc)
            return None

    def _parse_fraction_format(self, line: str) -> float | None:
        if "/" not in line:
            return None
        parts = line.split("/")
        nums = self._parse_line_numbers(parts[0])
        return nums[0] if nums else None

    def _sum_numbers_from_line(self, line: str) -> float:
        cleaned_line = line.strip()
        if not cleaned_line:
            return 0.0

        # Try direct float conversion
        parsed = self._parse_float(cleaned_line)
        if parsed is not None:
            return parsed

        # Try fraction format
        fraction_num = self._parse_fraction_format(cleaned_line)
        if fraction_num is not None:
            return fraction_num

        # General case: sum all numbers
        numbers = self._parse_line_numbers(cleaned_line)
        if not numbers:
            msg = f"No numeric points found in line: {cleaned_line}"
            raise ValueError(msg)
        return sum(numbers)

    def _parse_points_file(self, points_file: Path) -> float:
        """Parse points file, summing all numbers if multiple lines."""
        content = points_file.read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()
        if not content:
            return 0.0

        total = 0.0
        for line in content.splitlines():
            total += self._sum_numbers_from_line(line)
        return total

    def create_feedback_zip(
        self,
        result: GradingResult,
        output_path: Path | None = None,
        *,
        include_errors_log: bool = True,
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
                "collected_at": datetime.now(UTC).isoformat(),
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
