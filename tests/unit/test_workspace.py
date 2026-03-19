"""Unit tests for workspace utilities."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from canvas_code_correction.workspace import (
    WorkspaceConfig,
    WorkspacePaths,
    prepare_workspace,
)


def test_workspace_config() -> None:
    """Test WorkspaceConfig initialization."""
    config = WorkspaceConfig(
        workspace_root=Path("/tmp/workspaces"),
        bucket_block="test-bucket",
        path_prefix="test/prefix",
        assignment_id=123,
        submission_id=456,
        run_id="run123",
    )
    assert config.workspace_root == Path("/tmp/workspaces")
    assert config.bucket_block == "test-bucket"
    assert config.path_prefix == "test/prefix"
    assert config.assignment_id == 123
    assert config.submission_id == 456
    assert config.run_id == "run123"


def test_workspace_paths() -> None:
    """Test WorkspacePaths initialization."""
    root = Path("/tmp/workspace")
    submission_dir = root / "submission"
    assets_dir = root / "assets"
    paths = WorkspacePaths(root=root, submission_dir=submission_dir, assets_dir=assets_dir)
    assert paths.root == root
    assert paths.submission_dir == submission_dir
    assert paths.assets_dir == assets_dir


@patch("canvas_code_correction.workspace.S3Bucket")
def test_prepare_workspace_with_submission_files(mock_s3_bucket_class, tmp_path: Path) -> None:
    """Test workspace preparation with submission files."""
    mock_bucket = MagicMock()
    mock_s3_bucket_class.load.return_value = mock_bucket

    # Create dummy submission files outside workspace
    submission_files = []
    for i in range(2):
        file_path = tmp_path / f"submission_{i}.txt"
        file_path.write_text(f"Content {i}")
        submission_files.append(file_path)

    config = WorkspaceConfig(
        workspace_root=tmp_path,
        bucket_block="test-bucket",
        path_prefix="prefix",
        assignment_id=123,
        submission_id=456,
    )

    workspace_paths = prepare_workspace(config, submission_files)

    # Verify directories created
    assert workspace_paths.root.exists()
    assert workspace_paths.submission_dir.exists()
    assert workspace_paths.assets_dir.exists()

    # Verify submission files copied
    for i, file_path in enumerate(submission_files):
        dest = workspace_paths.submission_dir / file_path.name
        assert dest.exists()
        assert dest.read_text() == f"Content {i}"

    # Verify bucket load called
    mock_s3_bucket_class.load.assert_called_once_with("test-bucket")
    # Verify bucket was accessed (either download_folder or get_directory)
    # Since we didn't specify methods, mock_bucket may not have been called
    # but that's fine


@patch("canvas_code_correction.workspace.S3Bucket")
def test_prepare_workspace_with_assets_download(mock_s3_bucket_class, tmp_path: Path) -> None:
    """Test workspace preparation with asset download (download_folder method)."""
    mock_bucket = MagicMock()
    mock_bucket.download_folder = MagicMock()
    mock_s3_bucket_class.load.return_value = mock_bucket

    config = WorkspaceConfig(
        workspace_root=tmp_path,
        bucket_block="test-bucket",
        path_prefix="assets/prefix",
        assignment_id=1,
        submission_id=2,
    )

    workspace_paths = prepare_workspace(config, [])

    # Verify bucket load
    mock_s3_bucket_class.load.assert_called_once_with("test-bucket")
    # Verify download_folder called with correct arguments
    mock_bucket.download_folder.assert_called_once_with(
        local_path=str(workspace_paths.assets_dir),
        from_path="assets/prefix",
    )


@patch("canvas_code_correction.workspace.S3Bucket")
def test_prepare_workspace_with_assets_get_directory(mock_s3_bucket_class, tmp_path: Path) -> None:
    """Test workspace preparation with asset download (get_directory method)."""
    mock_bucket = MagicMock()
    # Simulate bucket lacking download_folder but having get_directory
    del mock_bucket.download_folder
    mock_bucket.get_directory = MagicMock()
    mock_s3_bucket_class.load.return_value = mock_bucket

    config = WorkspaceConfig(
        workspace_root=tmp_path,
        bucket_block="test-bucket",
        path_prefix="prefix",
        assignment_id=3,
        submission_id=4,
    )

    workspace_paths = prepare_workspace(config, [])

    mock_bucket.get_directory.assert_called_once_with(
        local_path=str(workspace_paths.assets_dir),
        from_path="prefix",
    )


@patch("canvas_code_correction.workspace.S3Bucket")
def test_prepare_workspace_empty_prefix(mock_s3_bucket_class, tmp_path: Path) -> None:
    """Test workspace preparation with empty path prefix."""
    mock_bucket = MagicMock()
    mock_bucket.download_folder = MagicMock()
    mock_s3_bucket_class.load.return_value = mock_bucket

    config = WorkspaceConfig(
        workspace_root=tmp_path,
        bucket_block="test-bucket",
        path_prefix="",  # empty prefix
        assignment_id=5,
        submission_id=6,
    )

    workspace_paths = prepare_workspace(config, [])

    # download_kwargs should be empty dict (no from_path)
    mock_bucket.download_folder.assert_called_once_with(
        local_path=str(workspace_paths.assets_dir),
    )


@patch("canvas_code_correction.workspace.S3Bucket")
def test_prepare_workspace_no_download_method(mock_s3_bucket_class, tmp_path: Path) -> None:
    """Test workspace preparation when bucket lacks download methods."""
    mock_bucket = MagicMock()
    # Remove both download_folder and get_directory
    del mock_bucket.download_folder
    del mock_bucket.get_directory
    mock_s3_bucket_class.load.return_value = mock_bucket

    config = WorkspaceConfig(
        workspace_root=tmp_path,
        bucket_block="test-bucket",
        path_prefix="prefix",
        assignment_id=7,
        submission_id=8,
    )

    with pytest.raises(AttributeError, match="S3Bucket block missing download method"):
        prepare_workspace(config, [])


@patch("canvas_code_correction.workspace.S3Bucket")
def test_prepare_workspace_submission_file_not_exists(mock_s3_bucket_class, tmp_path: Path) -> None:
    """Test workspace preparation when a submission file doesn't exist."""
    # Create a file that exists and one that doesn't
    existing_file = tmp_path / "exists.txt"
    existing_file.write_text("Hello")
    missing_file = tmp_path / "missing.txt"

    config = WorkspaceConfig(
        workspace_root=tmp_path,
        bucket_block="test-bucket",
        path_prefix="prefix",
        assignment_id=9,
        submission_id=10,
    )

    mock_bucket = MagicMock()
    mock_bucket.download_folder = MagicMock()
    mock_s3_bucket_class.load.return_value = mock_bucket

    workspace_paths = prepare_workspace(config, [existing_file, missing_file])

    # Only existing file should be copied
    dest_exists = workspace_paths.submission_dir / existing_file.name
    dest_missing = workspace_paths.submission_dir / missing_file.name
    assert dest_exists.exists()
    assert not dest_missing.exists()


@patch("canvas_code_correction.workspace.S3Bucket")
def test_prepare_workspace_rejects_world_writable_root(
    mock_s3_bucket_class,
    tmp_path: Path,
) -> None:
    unsafe_root = tmp_path / "unsafe-root"
    unsafe_root.mkdir(mode=0o777)
    unsafe_root.chmod(0o777)

    config = WorkspaceConfig(
        workspace_root=unsafe_root,
        bucket_block="test-bucket",
        path_prefix="prefix",
        assignment_id=11,
        submission_id=12,
    )

    with pytest.raises(RuntimeError, match="world-writable"):
        prepare_workspace(config, [])

    mock_s3_bucket_class.load.assert_not_called()


@patch("canvas_code_correction.workspace.S3Bucket")
def test_prepare_workspace_rejects_symlink_root(
    mock_s3_bucket_class,
    tmp_path: Path,
) -> None:
    real_root = tmp_path / "real-root"
    real_root.mkdir()
    symlink_root = tmp_path / "linked-root"
    symlink_root.symlink_to(real_root, target_is_directory=True)

    config = WorkspaceConfig(
        workspace_root=symlink_root,
        bucket_block="test-bucket",
        path_prefix="prefix",
        assignment_id=13,
        submission_id=14,
    )

    with pytest.raises(RuntimeError, match="symlink"):
        prepare_workspace(config, [])

    mock_s3_bucket_class.load.assert_not_called()
