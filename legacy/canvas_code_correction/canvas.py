"""Canvas API client utilities for the Prefect-based orchestration."""

from collections.abc import Iterable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

from canvasapi import Canvas as CanvasAPI
from canvasapi.file import File as CanvasFile
from canvasapi.submission import Submission as CanvasSubmission

from .config import Settings


class CanvasClient(AbstractContextManager["CanvasClient"]):
    """Lightweight helper around :mod:`canvasapi`."""

    def __init__(
        self,
        base_url: str,
        token: str,
        course_id: int,
        *,
        canvas: CanvasAPI | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._course_id = course_id
        self._canvas = canvas or CanvasAPI(self._base_url, token)
        self._course = self._canvas.get_course(course_id)

    @property
    def course_id(self) -> int:
        return self._course_id

    def close(self) -> None:  # pragma: no cover - no resources to release presently
        return None

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs: Any) -> "CanvasClient":
        return cls(
            base_url=settings.canvas.api_url,
            token=settings.canvas.token,
            course_id=settings.canvas.course_id,
            **kwargs,
        )

    def get_submission(
        self,
        assignment_id: int,
        submission_id: int,
        *,
        include: Iterable[str] | None = None,
    ) -> CanvasSubmission:
        assignment = self._course.get_assignment(assignment_id)
        include_params = list(include) if include is not None else None
        return assignment.get_submission(submission_id, include=include_params)

    def list_submission_ids(self, assignment_id: int) -> list[int]:
        assignment = self._course.get_assignment(assignment_id)
        return [submission.id for submission in assignment.get_submissions()]

    def get_submission_files(self, submission: CanvasSubmission) -> list[CanvasFile]:
        attachments = getattr(submission, "attachments", None) or []
        files: list[CanvasFile] = []
        for attachment in attachments:
            attachment_id = attachment.get("id")
            if attachment_id is None:
                continue
            files.append(self._canvas.get_file(attachment_id))
        return files

    def download_attachment(
        self,
        attachment: CanvasFile,
        destination_dir: Path,
        *,
        filename: str | None = None,
    ) -> Path:
        name = (
            filename
            or getattr(attachment, "filename", None)
            or getattr(
                attachment,
                "display_name",
                None,
            )
        )
        if not name:
            name = f"attachment-{getattr(attachment, 'id', 'unknown')}"

        local_path = destination_dir / name
        local_path.parent.mkdir(parents=True, exist_ok=True)
        attachment.download(local_path.as_posix())
        return local_path
