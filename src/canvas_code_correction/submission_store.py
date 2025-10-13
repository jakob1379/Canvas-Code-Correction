"""Utilities for managing submission workspaces on the local filesystem."""

from __future__ import annotations

from pathlib import Path

from .canvas import Attachment


class SubmissionStore:
    """Handles workspace layout for downloaded submissions."""

    def __init__(self, root: Path) -> None:
        self._root = root

    @property
    def root(self) -> Path:
        return self._root

    def workspace(self, assignment_id: int, submission_id: int) -> Path:
        workspace = self._root / str(assignment_id) / str(submission_id)
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def attachments_dir(self, workspace: Path) -> Path:
        attachments = workspace / "attachments"
        attachments.mkdir(parents=True, exist_ok=True)
        return attachments

    def attachment_path(self, workspace: Path, attachment: Attachment) -> Path:
        return self.attachments_dir(workspace) / attachment.suggested_name
