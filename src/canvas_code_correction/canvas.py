"""Canvas API client utilities for the Prefect-based orchestration."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

import httpx
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
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._course_id = course_id
        headers = {"Authorization": f"Bearer {token}"}
        self._client = httpx.Client(
            base_url=f"{self._base_url}/api/v1",
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    @property
    def course_id(self) -> int:
        return self._course_id

    def close(self) -> None:
        self._client.close()

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
        params: list[tuple[str, str]] = []
        if include:
            params.extend(("include[]", value) for value in include)

        response = self._client.get(
            f"/courses/{self._course_id}/assignments/{assignment_id}/submissions/{submission_id}",
            params=params or None,
        )
        response.raise_for_status()
        payload = response.json()
        return Submission.model_validate(payload)

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

        with self._client.stream("GET", str(attachment.url)) as response:
            response.raise_for_status()
            with local_path.open("wb") as file_handle:
                for chunk in response.iter_bytes():
                    file_handle.write(chunk)
        return local_path
