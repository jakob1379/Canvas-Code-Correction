"""Unit tests for the CanvasUploader."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from canvas_code_correction.uploader import (
    CanvasUploader,
    UploadConfig,
    UploadResult,
    create_uploader_from_resources,
)


def test_upload_config_defaults() -> None:
    """Test UploadConfig default values."""
    config = UploadConfig()
    assert config.check_duplicates is True
    assert config.upload_comments is True
    assert config.upload_grades is True
    assert config.dry_run is False
    assert config.verbose is False


def test_upload_result_model() -> None:
    """Test UploadResult model creation."""
    result = UploadResult(
        success=True,
        message="Test message",
        duplicate=False,
        grade_posted=True,
        comment_posted=False,
        details={"key": "value"},
    )
    
    assert result.success is True
    assert result.message == "Test message"
    assert result.duplicate is False
    assert result.grade_posted is True
    assert result.comment_posted is False
    assert result.details == {"key": "value"}


def test_uploader_initialization() -> None:
    """Test CanvasUploader initialization."""
    mock_submission = Mock()
    uploader = CanvasUploader(mock_submission)
    assert uploader.submission is mock_submission


@patch("canvas_code_correction.uploader.Path")
def test_upload_feedback_file_not_found(mock_path) -> None:
    """Test upload_feedback when file doesn't exist."""
    mock_submission = Mock()
    mock_path.exists.return_value = False
    
    uploader = CanvasUploader(mock_submission)
    result = uploader.upload_feedback(mock_path)
    
    assert result.success is False
    assert "not found" in result.message
    assert result.comment_posted is False


def test_upload_feedback_dry_run(tmp_path: Path) -> None:
    """Test upload_feedback with dry run."""
    test_file = tmp_path / "feedback.zip"
    test_file.write_text("test content")
    
    mock_submission = Mock()
    uploader = CanvasUploader(mock_submission)
    
    config = UploadConfig(dry_run=True)
    result = uploader.upload_feedback(test_file, config)
    
    assert result.success is True
    assert "Dry run" in result.message
    assert result.details["dry_run"] is True
    # Should not have called any submission methods
    assert not mock_submission.called


def test_upload_feedback_with_duplicate_check() -> None:
    """Test upload_feedback with duplicate checking."""
    # Create a mock submission with existing comments
    mock_submission = Mock()
    mock_submission.refresh = Mock(return_value=mock_submission)
    mock_submission.submission_comments = [
        {
            "attachments": [
                {
                    "url": "http://example.com/file1.zip",
                    "display_name": "feedback.zip",
                }
            ]
        }
    ]
    
    uploader = CanvasUploader(mock_submission)
    
    # Mock file operations and MD5 calculation
    with patch("canvas_code_correction.uploader.Path") as mock_path:
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_size = 100
        
        # Mock MD5 to return a known value
        with (
            patch.object(uploader, "_calculate_md5", return_value="test_hash"),
            patch.object(uploader, "_download_attachment"),
            patch("builtins.open", Mock()),
            patch("canvas_code_correction.uploader.hashlib") as mock_hashlib,
        ):
            mock_md5 = Mock()
            mock_md5.hexdigest.return_value = "test_hash"  # Same hash = duplicate
            mock_hashlib.md5.return_value = mock_md5
            
            result = uploader.upload_feedback(mock_path)
    
    # Should detect duplicate and not upload
    assert result.duplicate is True
    assert "duplicate" in result.message.lower()
    assert result.comment_posted is False


def test_upload_feedback_success() -> None:
    """Test successful feedback upload."""
    mock_submission = Mock()
    mock_submission.submission_comments = []  # No existing comments
    
    uploader = CanvasUploader(mock_submission)
    
    # Create a real temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = Path(tmp.name)
    
    try:
        config = UploadConfig(check_duplicates=False)
        result = uploader.upload_feedback(tmp_path, config)
        
        # Should have called upload_comment
        mock_submission.upload_comment.assert_called_once_with(str(tmp_path))
        
        assert result.success is True
        assert "uploaded successfully" in result.message
        assert result.comment_posted is True
        assert result.duplicate is False
    finally:
        tmp_path.unlink()


def test_upload_feedback_comments_disabled() -> None:
    """Test upload_feedback when comments upload is disabled."""
    mock_submission = Mock()
    uploader = CanvasUploader(mock_submission)
    
    with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(b"test")
        tmp.flush()
        
        config = UploadConfig(upload_comments=False)
        result = uploader.upload_feedback(tmp_path, config)
        
        assert result.success is True
        assert "comments upload disabled" in result.message.lower()
        assert result.comment_posted is False
        assert not mock_submission.upload_comment.called


def test_upload_grade_dry_run() -> None:
    """Test upload_grade with dry run."""
    mock_submission = Mock()
    mock_submission.grade = "85.5"
    
    uploader = CanvasUploader(mock_submission)
    config = UploadConfig(dry_run=True)
    
    result = uploader.upload_grade("90.0", config)
    
    assert result.success is True
    assert "Dry run" in result.message
    assert result.details["dry_run"] is True
    assert not mock_submission.edit.called


def test_upload_grade_duplicate() -> None:
    """Test upload_grade when grade is already the same."""
    mock_submission = Mock()
    mock_submission.grade = "85.5"
    
    uploader = CanvasUploader(mock_submission)
    config = UploadConfig(check_duplicates=True)
    
    result = uploader.upload_grade("85.5", config)
    
    assert result.success is True
    assert "already set" in result.message.lower()
    assert result.duplicate is True
    assert result.grade_posted is False
    assert not mock_submission.edit.called


def test_upload_grade_success() -> None:
    """Test successful grade upload."""
    mock_submission = Mock()
    mock_submission.grade = "75.0"
    
    uploader = CanvasUploader(mock_submission)
    config = UploadConfig(check_duplicates=True)
    
    result = uploader.upload_grade("85.5", config)
    
    mock_submission.edit.assert_called_once_with(
        submission={"posted_grade": "85.5"}
    )
    
    assert result.success is True
    assert "posted successfully" in result.message.lower()
    assert result.grade_posted is True
    assert result.duplicate is False


def test_upload_grade_grades_disabled() -> None:
    """Test upload_grade when grade upload is disabled."""
    mock_submission = Mock()
    mock_submission.grade = "75.0"
    
    uploader = CanvasUploader(mock_submission)
    config = UploadConfig(upload_grades=False)
    
    result = uploader.upload_grade("85.5", config)
    
    assert result.success is True
    assert "grade upload disabled" in result.message.lower()
    assert result.grade_posted is False
    assert not mock_submission.edit.called


def test_upload_feedback_and_grade() -> None:
    """Test upload_feedback_and_grade convenience method."""
    mock_submission = Mock()
    mock_submission.grade = "75.0"
    mock_submission.submission_comments = []
    
    uploader = CanvasUploader(mock_submission)
    
    with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(b"test")
        tmp.flush()
        
        config = UploadConfig(check_duplicates=False)
        feedback_result, grade_result = uploader.upload_feedback_and_grade(
            tmp_path, "85.5", config
        )
        
        assert feedback_result is not None
        assert grade_result is not None
        assert feedback_result.comment_posted is True
        assert grade_result.grade_posted is True


def test_upload_feedback_and_grade_partial() -> None:
    """Test upload_feedback_and_grade with partial inputs."""
    mock_submission = Mock()
    uploader = CanvasUploader(mock_submission)
    
    # Only feedback, no grade
    with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(b"test")
        tmp.flush()
        
        feedback_result, grade_result = uploader.upload_feedback_and_grade(
            tmp_path, None, UploadConfig()
        )
        
        assert feedback_result is not None
        assert grade_result is None
    
    # Only grade, no feedback
    feedback_result, grade_result = uploader.upload_feedback_and_grade(
        None, "85.5", UploadConfig()
    )
    
    assert feedback_result is None
    assert grade_result is not None


def test_create_uploader_from_resources() -> None:
    """Test create_uploader_from_resources helper."""
    mock_resources = Mock()
    mock_course = Mock()
    mock_assignment = Mock()
    mock_submission = Mock()
    
    mock_resources.course = mock_course
    mock_course.get_assignment.return_value = mock_assignment
    mock_assignment.get_submission.return_value = mock_submission
    
    uploader = create_uploader_from_resources(mock_resources, 123, 456)
    
    mock_course.get_assignment.assert_called_once_with(123)
    mock_assignment.get_submission.assert_called_once_with(456)
    assert uploader.submission is mock_submission


def test_calculate_md5(tmp_path: Path) -> None:
    """Test MD5 hash calculation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    
    mock_submission = Mock()
    uploader = CanvasUploader(mock_submission)
    
    md5_hash = uploader._calculate_md5(test_file)
    
    # MD5 of "Hello, World!" (without newline unless added by write_text)
    # write_text adds newline by default
    expected_hash = "65a8e27d8879283831b664bd8b7f0ad4"  # MD5 of "Hello, World!\n"
    assert md5_hash == expected_hash
