"""Canvas API client utilities for the Prefect-based orchestration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

import httpx
from canvasapi import Canvas as CanvasAPI
from pydantic import BaseModel, Field, HttpUrl, NonNegativeInt

from .config import Settings


class Attachment(BaseModel):
    """Subset of Canvas attachment fields used by the pipeline."""

    id: NonNegativeInt
    filename: str | None = None
    display_name: str | None = None
    url: HttpUrl | None = None
    content_type: str | None = None
    size: int | None = None

    @property
    def suggested_name(self) -> str:
        if self.filename:
            return self.filename
        if self.display_name:
            return self.display_name
        return f"attachment-{self.id}"


class Submission(BaseModel):
    id: NonNegativeInt
    user_id: NonNegativeInt
    assignment_id: NonNegativeInt
    attempt: int | None = None
    late: bool | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class CanvasClient(AbstractContextManager["CanvasClient"]):
    """Lightweight Canvas REST client."""

    def __init__(
        self,
        base_url: str,
        token: str,
        course_id: int,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        canvas: CanvasAPI | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._course_id = course_id
        self._canvas = canvas or CanvasAPI(self._base_url, token)
        self._course = self._canvas.get_course(course_id)

        if http_client is not None and transport is not None:
            raise ValueError("Specify either http_client or transport, not both")

        if http_client is not None:
            self._http_client = http_client
            self._owns_http_client = False
        else:
            headers = {"Authorization": f"Bearer {token}"}
            self._http_client = httpx.Client(timeout=timeout, headers=headers, transport=transport)
            self._owns_http_client = True

    @property
    def course_id(self) -> int:
        return self._course_id

    def close(self) -> None:
        if self._owns_http_client:
            self._http_client.close()

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs: Any) -> CanvasClient:
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
    ) -> Submission:
        assignment = self._course.get_assignment(assignment_id)
        include_params = list(include) if include is not None else None
        submission_obj = assignment.get_submission(submission_id, include=include_params)
        payload = submission_obj.to_dict()

        attachment_payloads = payload.get("attachments") or []
        attachments = [
            Attachment.model_validate(self._normalize_attachment(item))
            for item in attachment_payloads
        ]

        return Submission(
            id=payload["id"],
            user_id=payload["user_id"],
            assignment_id=payload["assignment_id"],
            attempt=payload.get("attempt"),
            late=payload.get("late"),
            attachments=attachments,
        )

    def download_attachment(
        self,
        attachment: Attachment,
        destination_dir: Path,
        *,
        filename: str | None = None,
    ) -> Path:
        if attachment.url is None:
            raise ValueError(f"Attachment {attachment.id} does not expose a download URL")

        file_name = filename or attachment.suggested_name
        local_path = destination_dir / file_name
        local_path.parent.mkdir(parents=True, exist_ok=True)

        with self._http_client.stream("GET", str(attachment.url)) as response:
            response.raise_for_status()
            with local_path.open("wb") as file_handle:
                for chunk in response.iter_bytes():
                    file_handle.write(chunk)
        return local_path

    @staticmethod
    def _normalize_attachment(raw: Mapping[str, Any]) -> Mapping[str, Any]:
        content_type = raw.get("content_type") or raw.get("content-type")
        return {
            "id": raw["id"],
            "filename": raw.get("filename"),
            "display_name": raw.get("display_name"),
            "url": raw.get("url"),
            "content_type": content_type,
            "size": raw.get("size"),
        }
