"""Unit tests for the ResultCollector."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from canvas_code_correction.flows.collector import (
    ERRORS_LOG_FILENAME,
    CollectionMetadata,
    CollectionResult,
    GradingResult,
    ResultCollector,
)


def create_test_workspace(tmp_path: Path) -> Path:
    """Create a test workspace with sample grader outputs."""
    workspace = tmp_path / "workspace"
    submission_dir = workspace / "submission"
    submission_dir.mkdir(parents=True)

    # Create points file with multiple numbers
    points_file = submission_dir / "test_submission_points.txt"
    points_file.write_text("10.5\n5.0\n2.5\n")

    # Create comments file
    comments_file = submission_dir / "test_submission.txt"
    comments_file.write_text("Good work!\nNeeds improvement.\n")

    # Create artifacts zip
    artifacts_zip = submission_dir / "artifacts.zip"
    with zipfile.ZipFile(artifacts_zip, "w") as zf:
        zf.writestr("file1.txt", "content1")
        zf.writestr("file2.txt", "content2")

    # Create errors log
    errors_log = submission_dir / "errors.log"
    errors_log.write_text("Error 1\nError 2\n")

    # Create some other files
    (submission_dir / "output.png").write_bytes(b"fake image data")

    return workspace


@pytest.mark.local
def test_collect_basic(tmp_path: Path) -> None:
    """Test basic collection of grader outputs."""
    workspace = create_test_workspace(tmp_path)
    collector = ResultCollector(workspace)

    result = collector.collect("test_submission")

    assert isinstance(result, CollectionResult)
    assert result.workspace_root == workspace

    grading_result = result.grading_result
    assert grading_result.points == pytest.approx(18.0)  # 10.5 + 5.0 + 2.5
    assert grading_result.comments == "Good work!\nNeeds improvement.\n"
    assert grading_result.points_file_content == "10.5\n5.0\n2.5\n"
    assert grading_result.artifacts_zip_path is not None
    assert grading_result.artifacts_zip_path.name == "artifacts.zip"
    assert grading_result.errors_log_path is not None
    assert grading_result.errors_log_path.name == "errors.log"

    # Check discovered files
    filenames = {f.name for f in result.discovered_files}
    expected_files = {
        "test_submission_points.txt",
        "test_submission.txt",
        "artifacts.zip",
        "errors.log",
        "output.png",
    }
    assert expected_files.issubset(filenames)


@pytest.mark.local
def test_collect_no_submission_dir_name(tmp_path: Path) -> None:
    """Test collection without explicit submission directory name."""
    workspace = create_test_workspace(tmp_path)
    collector = ResultCollector(workspace)

    # Should infer from directory structure
    result = collector.collect()

    assert result.grading_result.points == pytest.approx(18.0)
    # Should still find comments file even without explicit name
    assert result.grading_result.comments is not None


@pytest.mark.local
def test_collect_missing_points_file(tmp_path: Path) -> None:
    """Test collection when points file is missing."""
    workspace = tmp_path / "workspace"
    submission_dir = workspace / "submission"
    submission_dir.mkdir(parents=True)

    # Only create comments, no points
    (submission_dir / "comments.txt").write_text("No points here")

    collector = ResultCollector(workspace)

    with pytest.raises(FileNotFoundError, match="No points file found"):
        collector.collect()


@pytest.mark.local
def test_collect_alternative_points_file(tmp_path: Path) -> None:
    """Test collection with alternative points file name."""
    workspace = tmp_path / "workspace"
    submission_dir = workspace / "submission"
    submission_dir.mkdir(parents=True)

    # Create points.txt instead of *_points.txt
    points_file = submission_dir / "points.txt"
    points_file.write_text("42.0\n")

    collector = ResultCollector(workspace)
    result = collector.collect()

    assert result.grading_result.points == pytest.approx(42.0)


@pytest.mark.local
@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("10.5", 10.5),
        ("10.5\n5.0\n2.5", 18.0),
        ("", 0.0),
        (" 10.5  \n  ", 10.5),
        ("10\n20\n30", 60.0),
        ("Score: 10.5 points", 10.5),
        ("Total: 25.5/30", 25.5),
        ("1.5 2.5 3.5", 7.5),
    ],
)
def test_collect_parses_supported_points_formats(
    tmp_path: Path,
    content: str,
    expected: float,
) -> None:
    """Test points parsing through the public collect API."""
    workspace = tmp_path / "workspace"
    submission_dir = workspace / "submission"
    submission_dir.mkdir(parents=True)
    (submission_dir / "points.txt").write_text(content)

    collector = ResultCollector(workspace)
    result = collector.collect()

    assert result.grading_result.points == pytest.approx(expected, abs=0.01)


@pytest.mark.local
def test_collect_rejects_malformed_points_content(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    submission_dir = workspace / "submission"
    submission_dir.mkdir(parents=True)
    (submission_dir / "points.txt").write_text(" / ")

    collector = ResultCollector(workspace)

    with pytest.raises(ValueError, match="No numeric points found"):
        collector.collect()


@pytest.mark.local
def test_create_feedback_zip(tmp_path: Path) -> None:
    """Test creation of feedback zip file."""
    workspace = tmp_path / "workspace"
    submission_dir = workspace / "submission"
    submission_dir.mkdir(parents=True)

    # Create sample files
    points_file = submission_dir / "points.txt"
    points_file.write_text("85.5\n")

    errors_log = submission_dir / "errors.log"
    errors_log.write_text("Some errors\n")

    collector = ResultCollector(workspace)

    grading_result = GradingResult(
        points=85.5,
        points_file_content="85.5\n",
        comments="Good job!\n",
        comments_file_path=submission_dir / "comments.txt",
        artifacts_zip_path=None,
        errors_log_path=errors_log,
        metadata=CollectionMetadata(),
    )

    output_zip = tmp_path / "feedback.zip"
    result_path = collector.create_feedback_zip(
        grading_result,
        output_path=output_zip,
        include_errors_log=True,
    )

    assert result_path == output_zip
    assert output_zip.exists()

    # Verify zip contents
    with zipfile.ZipFile(output_zip, "r") as zf:
        filenames = set(zf.namelist())
        assert "points.txt" in filenames
        assert "comments.txt" in filenames
        assert "errors.log" in filenames
        assert "metadata.json" in filenames

        # Check content
        assert zf.read("points.txt").decode() == "85.5\n"
        assert zf.read("comments.txt").decode() == "Good job!\n"
        assert zf.read("errors.log").decode() == "Some errors\n"
        metadata = json.loads(zf.read("metadata.json").decode())
        assert metadata["collected_at"].endswith("+00:00")


@pytest.mark.local
def test_create_feedback_zip_without_errors(tmp_path: Path) -> None:
    """Test feedback zip creation without errors log."""
    workspace = tmp_path / "workspace"
    collector = ResultCollector(workspace)

    grading_result = GradingResult(
        points=100.0,
        points_file_content="100.0\n",
        comments=None,
        comments_file_path=None,
        artifacts_zip_path=None,
        errors_log_path=None,
        metadata=CollectionMetadata(),
    )

    output_zip = tmp_path / "feedback.zip"
    collector.create_feedback_zip(
        grading_result,
        output_path=output_zip,
        include_errors_log=False,
    )

    with zipfile.ZipFile(output_zip, "r") as zf:
        filenames = set(zf.namelist())
        assert "points.txt" in filenames
        assert "comments.txt" not in filenames  # No comments
        assert "errors.log" not in filenames  # No errors log
        assert "metadata.json" in filenames


@pytest.mark.local
def test_validate_result() -> None:
    """Test validation of grading results."""
    collector = ResultCollector(Path("/tmp"))

    # Valid result
    valid_result = GradingResult(
        points=85.5,
        points_file_content="85.5\n",
        comments="Good",
        comments_file_path=Path("/tmp/comments.txt"),
        artifacts_zip_path=Path("/tmp/artifacts.zip"),
        errors_log_path=Path("/tmp/errors.log"),
        metadata=CollectionMetadata(),
    )

    # Mock file existence
    with patch.object(Path, "exists", return_value=True):
        issues = collector.validate_result(valid_result)
        assert issues == []

    # Result with negative points
    negative_result = GradingResult(
        points=-10.0,
        points_file_content="-10.0\n",
        comments="",
        comments_file_path=None,
        artifacts_zip_path=None,
        errors_log_path=None,
        metadata=CollectionMetadata(),
    )

    issues = collector.validate_result(negative_result)
    assert "Negative points value" in issues[0]

    # Result with unusually high points
    high_result = GradingResult(
        points=10000.0,
        points_file_content="10000.0\n",
        comments="",
        comments_file_path=None,
        artifacts_zip_path=None,
        errors_log_path=None,
        metadata=CollectionMetadata(),
    )

    issues = collector.validate_result(high_result)
    assert "Unusually high points value" in issues[0]

    # Result with missing artifacts zip
    missing_artifacts_result = GradingResult(
        points=50.0,
        points_file_content="50.0\n",
        comments="",
        comments_file_path=None,
        artifacts_zip_path=Path("/tmp/nonexistent.zip"),
        errors_log_path=None,
        metadata=CollectionMetadata(),
    )

    with patch.object(Path, "exists", return_value=False):
        issues = collector.validate_result(missing_artifacts_result)
        assert "Artifacts zip referenced but not found" in issues[0]


@pytest.mark.local
def test_collect_missing_submission_dir(tmp_path: Path) -> None:
    """Test collection when submission directory doesn't exist."""
    workspace = tmp_path / "workspace"
    collector = ResultCollector(workspace)
    with pytest.raises(FileNotFoundError, match="Submission directory not found"):
        collector.collect()


@pytest.mark.local
def test_collect_without_comment_file_returns_none(tmp_path: Path) -> None:
    """Test comment discovery through the public collect API."""
    workspace = tmp_path / "workspace"
    submission_dir = workspace / "submission"
    submission_dir.mkdir(parents=True)
    (submission_dir / "points.txt").write_text("10.0")
    (submission_dir / ERRORS_LOG_FILENAME).write_text("")

    collector = ResultCollector(workspace)
    result = collector.collect()

    assert result.grading_result.comments is None
    assert result.grading_result.comments_file_path is None


@pytest.mark.local
def test_create_feedback_zip_empty_points_content(tmp_path: Path) -> None:
    """Test feedback zip creation with empty points file content."""
    workspace = tmp_path / "workspace"
    collector = ResultCollector(workspace)
    grading_result = GradingResult(
        points=0.0,
        points_file_content="",  # empty
        comments=None,
        comments_file_path=None,
        artifacts_zip_path=None,
        errors_log_path=None,
        metadata=CollectionMetadata(),
    )
    output_zip = tmp_path / "feedback.zip"
    collector.create_feedback_zip(grading_result, output_path=output_zip)
    assert output_zip.exists()
    with zipfile.ZipFile(output_zip, "r") as zf:
        filenames = set(zf.namelist())
        # points.txt should not be included because content empty
        assert "points.txt" not in filenames
        assert "metadata.json" in filenames
