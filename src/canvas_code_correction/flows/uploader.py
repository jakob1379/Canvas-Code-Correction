"""Idempotent upload of feedback and grades to Canvas with duplicate detection."""

from __future__ import annotations

import hashlib
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, Required, TypedDict, cast

import requests
from canvasapi.exceptions import CanvasException

if TYPE_CHECKING:
    from canvasapi.submission import Submission

    from canvas_code_correction.clients.canvas_resources import CanvasResources

logger = logging.getLogger(__name__)
UPLOAD_EXCEPTION_TYPES = (
    CanvasException,
    NotImplementedError,
    OSError,
    requests.RequestException,
    RuntimeError,
    TypeError,
    ValueError,
)


type UploadDetailValue = str | int | float | bool | None


class AttachmentWithUrl(TypedDict):
    """Attachment payload after URL normalization."""

    url: Required[str]
    display_name: NotRequired[str]


class SubmissionCommentInfo(TypedDict, total=False):
    """Subset of submission comment data used for duplicate checks."""

    attachments: list[AttachmentWithUrl]


@dataclass(frozen=True)
class UploadBatchResult:
    """Combined feedback and grade outcomes for a batch upload."""

    feedback: UploadResult | None
    grade: UploadResult | None


@dataclass(frozen=True)
class UploadResult:
    """Result of an upload operation."""

    success: bool
    message: str
    duplicate: bool = False
    grade_posted: bool = False
    comment_posted: bool = False
    details: dict[str, UploadDetailValue] = field(default_factory=dict)


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

    def __init__(self, submission: Submission) -> None:
        """Initialize uploader with Canvas submission object."""
        self.submission = submission

    def _check_feedback_duplicate(
        self,
        feedback_file: Path,
        config: UploadConfig,
    ) -> UploadResult | None:
        """Check if feedback file already exists as a comment attachment."""
        try:
            comments = self._refresh_submission_and_get_comments()
            local_md5 = self._calculate_md5(feedback_file)
            duplicate_result = self._find_duplicate_in_comments(comments, local_md5, config)
            if duplicate_result:
                return duplicate_result
        except UPLOAD_EXCEPTION_TYPES as exc:
            if config.verbose:
                logger.warning("Error during duplicate check: %s", exc)
            return UploadResult(
                success=False,
                message=f"Duplicate check failed: {exc}",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={"error": str(exc), "stage": "duplicate_check"},
            )
        return None

    def _refresh_submission_and_get_comments(self) -> list[SubmissionCommentInfo]:
        """Refresh submission then return normalized submission comments."""
        self.submission = self.submission.refresh()
        raw_comments = getattr(self.submission, "submission_comments", []) or []
        comments: list[SubmissionCommentInfo] = []
        for comment in raw_comments:
            if not isinstance(comment, dict):
                continue
            comments.append(
                {"attachments": self._normalize_comment_attachments(comment.get("attachments"))},
            )
        return comments

    def _normalize_comment_attachments(
        self,
        raw_attachments: object,
    ) -> list[AttachmentWithUrl]:
        if not isinstance(raw_attachments, list):
            return []

        normalized: list[AttachmentWithUrl] = []
        for raw_attachment in raw_attachments:
            normalized_attachment = self._to_attachment_with_url(raw_attachment)
            if normalized_attachment is not None:
                normalized.append(normalized_attachment)
        return normalized

    @staticmethod
    def _to_attachment_with_url(raw_attachment: object) -> AttachmentWithUrl | None:
        if not isinstance(raw_attachment, dict):
            return None

        attachment_dict = cast("dict[str, object]", raw_attachment)
        url = attachment_dict.get("url")
        if not isinstance(url, str):
            return None

        attachment: AttachmentWithUrl = {"url": url}
        display_name = attachment_dict.get("display_name")
        if isinstance(display_name, str):
            attachment["display_name"] = display_name

        return attachment

    def _find_duplicate_in_comments(
        self,
        comments: list[SubmissionCommentInfo],
        local_md5: str,
        config: UploadConfig,
    ) -> UploadResult | None:
        """Search through comments and attachments for duplicate MD5."""
        for comment in comments:
            attachments = comment.get("attachments", [])
            if not attachments:
                continue
            for attachment in attachments:
                normalized_attachment = self._to_attachment_with_url(attachment)
                if normalized_attachment is None:
                    continue

                duplicate_result = self._check_attachment_duplicate(
                    normalized_attachment,
                    local_md5,
                    config,
                )
                if duplicate_result:
                    return duplicate_result
        return None

    def _check_attachment_duplicate(
        self,
        attachment: AttachmentWithUrl,
        local_md5: str,
        config: UploadConfig,
    ) -> UploadResult | None:
        """Check if a single attachment matches local MD5."""
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            try:
                self._download_attachment(
                    attachment["url"],
                    Path(tmp.name),
                )
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
            except UPLOAD_EXCEPTION_TYPES as exc:
                if config.verbose:
                    logger.warning("Error checking attachment: %s", exc)
                return UploadResult(
                    success=False,
                    message=f"Duplicate check failed for existing attachment: {exc}",
                    duplicate=False,
                    comment_posted=False,
                    grade_posted=False,
                    details={
                        "error": str(exc),
                        "attachment": attachment.get("display_name"),
                        "stage": "duplicate_check",
                    },
                )
        return None

    def _upload_feedback_without_duplicate_check(
        self,
        feedback_file: Path,
        config: UploadConfig,
    ) -> UploadResult:
        """Upload feedback file assuming no duplicate."""
        del config
        local_md5 = self._calculate_md5(feedback_file)
        try:
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
        except UPLOAD_EXCEPTION_TYPES as exc:
            return UploadResult(
                success=False,
                message=f"Failed to upload feedback: {exc}",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={"error": str(exc), "file": str(feedback_file)},
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

        if not config.upload_comments:
            return UploadResult(
                success=True,
                message="Comments upload disabled, skipping",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={
                    "file": str(feedback_file),
                    "upload_comments": False,
                },
            )

        if config.check_duplicates:
            duplicate_result = self._check_feedback_duplicate(
                feedback_file,
                config,
            )
            if duplicate_result:
                return duplicate_result

        return self._upload_feedback_without_duplicate_check(
            feedback_file,
            config,
        )

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

            if config.check_duplicates and str(current_grade) == str(grade):
                return UploadResult(
                    success=True,
                    message=f"Grade already set to {grade}, skipping",
                    duplicate=True,
                    comment_posted=False,
                    grade_posted=False,
                    details={
                        "current_grade": current_grade,
                        "new_grade": grade,
                    },
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
            return UploadResult(
                success=True,
                message="Grade upload disabled, skipping",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={"grade": grade, "upload_grades": False},
            )

        except UPLOAD_EXCEPTION_TYPES as exc:
            return UploadResult(
                success=False,
                message=f"Failed to post grade: {exc}",
                duplicate=False,
                comment_posted=False,
                grade_posted=False,
                details={"error": str(exc), "grade": grade},
            )

    def upload_feedback_and_grade(
        self,
        feedback_file: Path,
        grade: str | float,
        config: UploadConfig | None = None,
    ) -> UploadBatchResult:
        """Upload both feedback and grade.

        This method requires both inputs. Use :meth:`upload_feedback` or
        :meth:`upload_grade` for single-operation callers.
        """
        config = config or UploadConfig()
        feedback_result = self.upload_feedback(feedback_file, config)
        grade_result = self.upload_grade(grade, config)
        return UploadBatchResult(feedback=feedback_result, grade=grade_result)

    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5(usedforsecurity=False)
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _download_attachment(self, _url: str, _destination: Path) -> None:
        """Download a file from a URL to destination."""
        with requests.get(_url, stream=True, timeout=30) as response:
            response.raise_for_status()
            _destination.parent.mkdir(parents=True, exist_ok=True)
            with _destination.open("wb") as file_obj:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_obj.write(chunk)


def create_uploader_from_resources(
    resources: CanvasResources,
    assignment_id: int,
    submission_id: int,
) -> CanvasUploader:
    """Create an uploader from CanvasResources."""
    assignment = resources.course.get_assignment(assignment_id)
    submission = assignment.get_submission(submission_id)
    return CanvasUploader(submission)
