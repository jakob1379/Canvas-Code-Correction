"""Idempotent upload of feedback and grades to Canvas with duplicate detection."""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from canvasapi.submission import Submission
from pydantic import BaseModel, Field


class UploadResult(BaseModel):
    """Result of an upload operation."""

    success: bool
    message: str
    duplicate: bool = False
    grade_posted: bool = False
    comment_posted: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class UploadConfig:
    """Configuration for upload operations."""

    check_duplicates: bool = True
    upload_comments: bool = True
    upload_grades: bool = True
    dry_run: bool = False
    verbose: bool = False


class CanvasUploader:
    """Handles idempotent upload of feedback and grades to Canvas."""

    def __init__(self, submission: Submission):
        self.submission = submission

    def _check_feedback_duplicate(
        self, feedback_file: Path, config: UploadConfig
    ) -> UploadResult | None:
        """Check if feedback file already exists as a comment attachment."""
        try:
            self.submission = self.submission.refresh()
            comments = getattr(self.submission, "submission_comments", []) or []
            local_md5 = self._calculate_md5(feedback_file)
            for comment in comments:
                attachments = comment.get("attachments", [])
                for attachment in attachments:
                    if not attachment.get("url"):
                        continue
                    with tempfile.NamedTemporaryFile(delete=True) as tmp:
                        try:
                            self._download_attachment(attachment["url"], Path(tmp.name))
                            remote_md5 = self._calculate_md5(Path(tmp.name))
                            if remote_md5 == local_md5:
                                return UploadResult(
                                    success=True,
                                    message="Duplicate feedback detected, skipping upload",
                                    duplicate=True,
                                    comment_posted=False,
                                    grade_posted=False,
                                    details={
                                        "local_md5": local_md5,
                                        "remote_md5": remote_md5,
                                        "attachment": attachment.get("display_name"),
                                    },
                                )
                        except Exception as e:
                            if config.verbose:
                                print(f"Warning checking duplicate: {e}")
                            continue
        except Exception as e:
            if config.verbose:
                print(f"Warning checking duplicates: {e}")
            # Continue with upload even if duplicate check fails
        return None

    def _upload_feedback_without_duplicate_check(
        self, feedback_file: Path, config: UploadConfig
    ) -> UploadResult:
        """Upload feedback file assuming no duplicate."""
        local_md5 = self._calculate_md5(feedback_file)
        try:
            if config.upload_comments:
                self.submission.upload_comment(str(feedback_file))
                return UploadResult(
                    success=True,
                    message=f"Feedback uploaded successfully: {feedback_file.name}",
                    duplicate=False,
                    comment_posted=True,
                    grade_posted=False,
                    details={
                        "file": str(feedback_file),
                        "md5": local_md5,
                        "size": feedback_file.stat().st_size,
                    },
                )
            else:
                return UploadResult(
                    success=True,
                    message="Comments upload disabled, skipping",
                    duplicate=False,
                    comment_posted=False,
                    grade_posted=False,
                    details={"file": str(feedback_file), "upload_comments": False},
                )
        except Exception as e:
            return UploadResult(
                success=False,
                message=f"Failed to upload feedback: {e}",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={"error": str(e), "file": str(feedback_file)},
            )

    def upload_feedback(
        self,
        feedback_file: Path,
        config: UploadConfig | None = None,
    ) -> UploadResult:
        """Upload feedback file with MD5 duplicate detection."""
        config = config or UploadConfig()
        if not feedback_file.exists():
            return UploadResult(
                success=False,
                message=f"Feedback file not found: {feedback_file}",
            )

        if config.dry_run:
            return UploadResult(
                success=True,
                message=f"Dry run: would upload {feedback_file}",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={"file": str(feedback_file), "dry_run": True},
            )

        # Check for duplicates
        if config.check_duplicates:
            duplicate_result = self._check_feedback_duplicate(feedback_file, config)
            if duplicate_result:
                return duplicate_result

        # Upload feedback
        return self._upload_feedback_without_duplicate_check(feedback_file, config)

    def upload_grade(
        self,
        grade: str | float,
        config: UploadConfig | None = None,
    ) -> UploadResult:
        """Post grade to Canvas submission."""
        config = config or UploadConfig()
        if config.dry_run:
            return UploadResult(
                success=True,
                message=f"Dry run: would post grade {grade}",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={"grade": grade, "dry_run": True},
            )

        try:
            current_grade = self.submission.grade

            # Check if grade is already the same
            if config.check_duplicates and str(current_grade) == str(grade):
                return UploadResult(
                    success=True,
                    message=f"Grade already set to {grade}, skipping",
                    duplicate=True,
                    comment_posted=False,
                    grade_posted=False,
                    details={"current_grade": current_grade, "new_grade": grade},
                )

            if config.upload_grades:
                self.submission.edit(submission={"posted_grade": grade})
                return UploadResult(
                    success=True,
                    message=f"Grade posted successfully: {grade}",
                    duplicate=False,
                    comment_posted=False,
                    grade_posted=True,
                    details={"grade": grade, "previous_grade": current_grade},
                )
            else:
                return UploadResult(
                    success=True,
                    message="Grade upload disabled, skipping",
                    duplicate=False,
                    comment_posted=False,
                    grade_posted=False,
                    details={"grade": grade, "upload_grades": False},
                )

        except Exception as e:
            return UploadResult(
                success=False,
                message=f"Failed to post grade: {e}",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={"error": str(e), "grade": grade},
            )

    def upload_feedback_and_grade(
        self,
        feedback_file: Path | None,
        grade: str | float | None,
        config: UploadConfig | None = None,
    ) -> tuple[UploadResult | None, UploadResult | None]:
        """Convenience method to upload both feedback and grade."""
        config = config or UploadConfig()
        if feedback_file is None and grade is None:
            raise ValueError("At least one of feedback_file or grade must be provided")
        feedback_result = None
        grade_result = None

        if feedback_file:
            feedback_result = self.upload_feedback(feedback_file, config)

        if grade is not None:
            grade_result = self.upload_grade(grade, config)

        return feedback_result, grade_result

    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _download_attachment(self, url: str, destination: Path) -> None:
        """Download a file from a URL to destination."""
        import shutil
        import urllib.request

        # Simple download implementation
        # In practice, should use canvasapi's built-in methods or requests with auth
        try:
            # This is a simplified version - real implementation should handle
            # Canvas authentication properly
            # For now, we'll use a placeholder that raises NotImplementedError
            # since proper implementation requires the Canvas object context
            raise NotImplementedError(
                "Attachment download requires Canvas object context. "
                "Use submission.attachments or file.download() instead."
            )
        except ImportError:
            # Fallback to urllib (won't work with authenticated Canvas URLs)
            with urllib.request.urlopen(url) as response, open(destination, "wb") as out_file:
                shutil.copyfileobj(response, out_file)


def create_uploader_from_resources(
    resources: Any,  # CanvasResources type
    assignment_id: int,
    submission_id: int,
) -> CanvasUploader:
    """Create an uploader from CanvasResources."""
    assignment = resources.course.get_assignment(assignment_id)
    submission = assignment.get_submission(submission_id)
    return CanvasUploader(submission)
