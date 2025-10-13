"""Utilities for managing submission workspaces on the local filesystem."""

from __future__ import annotations

import shutil
import zipfile
from collections.abc import Iterable
from pathlib import Path, PurePosixPath


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

    def attachment_path(self, workspace: Path, attachment_name: str) -> Path:
        return self.attachments_dir(workspace) / attachment_name

    def submission_dir(self, workspace: Path) -> Path:
        submission = workspace / "submission"
        submission.mkdir(parents=True, exist_ok=True)
        return submission

    def stage_attachments(self, workspace: Path, attachments: Iterable[Path]) -> list[Path]:
        submission_root = self.submission_dir(workspace)

        for attachment_path in attachments:
            if not attachment_path.exists():
                continue

            if zipfile.is_zipfile(attachment_path):
                self._extract_zip(attachment_path, submission_root)
                continue

            destination = submission_root / attachment_path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if attachment_path.resolve() != destination.resolve():
                shutil.copy2(attachment_path, destination)

        self._remove_macosx_dirs(submission_root)
        self._flatten_single_directory(submission_root)

        files = [path for path in submission_root.rglob("*") if path.is_file()]
        files.sort(key=lambda path: path.relative_to(submission_root).parts)
        return files

    def _extract_zip(self, archive_path: Path, destination: Path) -> None:
        temp_dir = destination / f".extract-{archive_path.stem}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_base = temp_dir.resolve()

        try:
            with zipfile.ZipFile(archive_path) as archive:
                for info in archive.infolist():
                    relative = PurePosixPath(info.filename)

                    if not relative.parts:
                        continue

                    if relative.is_absolute():
                        try:
                            relative = relative.relative_to("/")
                        except ValueError:
                            continue

                    if ".." in relative.parts:
                        continue

                    if relative.parts[0] == "__MACOSX":
                        continue

                    target = temp_dir.joinpath(*relative.parts)
                    resolved_target = target.resolve()
                    if temp_base not in (resolved_target, *resolved_target.parents):
                        raise RuntimeError(
                            f"Archive member {info.filename!r} extracts outside of destination"
                        )

                    if info.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue

                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info, "r") as source, target.open("wb") as handle:
                        shutil.copyfileobj(source, handle)

            self._remove_macosx_dirs(temp_dir)
            self._flatten_single_directory(temp_dir)

            for child in sorted(temp_dir.iterdir()):
                target = destination / child.name
                if child.is_dir():
                    shutil.copytree(child, target, dirs_exist_ok=True)
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        target.unlink()
                    shutil.move(str(child), target)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _flatten_single_directory(self, root: Path) -> None:
        entries = [path for path in root.glob("*")]
        if len(entries) != 1:
            return

        sole = entries[0]
        if not sole.is_dir():
            return

        temp = sole.with_name(f"{sole.name}-old")
        sole.rename(temp)

        for child in temp.iterdir():
            destination = root / child.name
            if child.is_dir():
                shutil.copytree(child, destination, dirs_exist_ok=True)
                shutil.rmtree(child, ignore_errors=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    destination.unlink()
                shutil.move(str(child), destination)

        shutil.rmtree(temp, ignore_errors=True)

    @staticmethod
    def _remove_macosx_dirs(root: Path) -> None:
        for path in root.rglob("__MACOSX"):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
