from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from canvas_code_correction.collector import ResultCollector


@pytest.mark.integration
def test_collector_with_real_files() -> None:
    """Test result collection with real files in a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        submission_dir = workspace_root / "submission"
        submission_dir.mkdir()

        submission_dir_name = "submission_123"
        # Create points file with naming pattern
        points_file = submission_dir / f"{submission_dir_name}_points.txt"
        points_file.write_text("Total: 25/30\n")

        # Create comments file with naming pattern
        comments_file = submission_dir / f"{submission_dir_name}.txt"
        comments_file.write_text("Good work!\n")

        # Create artifacts zip
        artifacts_zip = submission_dir / "artifacts.zip"
        with zipfile.ZipFile(artifacts_zip, "w") as zf:
            zf.writestr("output.log", "Some logs")

        collector = ResultCollector(workspace_root)
        result = collector.collect(submission_dir_name=submission_dir_name)

        assert result.grading_result.points == pytest.approx(25.0)
        assert result.grading_result.comments == "Good work!\n"
        assert result.grading_result.points_file_content == "Total: 25/30\n"
        assert result.grading_result.artifacts_zip_path == artifacts_zip
        # discovered_files includes all files in submission directory
        assert set(result.discovered_files) == {points_file, comments_file, artifacts_zip}


@pytest.mark.integration
def test_collector_with_fraction_points() -> None:
    """Test parsing fractional points (e.g., 25.5/30)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        submission_dir = workspace_root / "submission"
        submission_dir.mkdir()

        submission_dir_name = "submission_456"
        points_file = submission_dir / f"{submission_dir_name}_points.txt"
        points_file.write_text("Total: 25.5/30\n")

        collector = ResultCollector(workspace_root)
        result = collector.collect(submission_dir_name=submission_dir_name)

        assert result.grading_result.points == pytest.approx(25.5)


@pytest.mark.integration
def test_collector_without_points_file() -> None:
    """Test collection when points file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        submission_dir = workspace_root / "submission"
        submission_dir.mkdir()

        submission_dir_name = "submission_nopoints"
        # Only comments file, no points file
        comments_file = submission_dir / f"{submission_dir_name}.txt"
        comments_file.write_text("No points provided")

        collector = ResultCollector(workspace_root)
        with pytest.raises(FileNotFoundError, match="No points file found"):
            collector.collect(submission_dir_name=submission_dir_name)


@pytest.mark.integration
def test_create_feedback_zip_real() -> None:
    """Test creation of feedback zip with real files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        submission_dir = workspace_root / "submission"
        submission_dir.mkdir()

        submission_dir_name = "submission_zip"
        points_file = submission_dir / f"{submission_dir_name}_points.txt"
        points_file.write_text("Total: 10/10\n")

        comments_file = submission_dir / f"{submission_dir_name}.txt"
        comments_file.write_text("Perfect!")

        errors_log = submission_dir / "errors.log"
        errors_log.write_text("Some errors")

        collector = ResultCollector(workspace_root)
        result = collector.collect(submission_dir_name=submission_dir_name)

        feedback_zip = collector.create_feedback_zip(result.grading_result)
        assert feedback_zip.exists()
        assert feedback_zip.suffix == ".zip"

        # Verify zip contents
        with zipfile.ZipFile(feedback_zip, "r") as zf:
            names = zf.namelist()
            assert "points.txt" in names
            assert "comments.txt" in names
            assert "errors.log" in names

        feedback_zip.unlink()


@pytest.mark.integration
def test_validate_result_with_issues() -> None:
    """Test validation of grading results with potential issues."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        submission_dir = workspace_root / "submission"
        submission_dir.mkdir()

        submission_dir_name = "submission_validate"
        points_file = submission_dir / f"{submission_dir_name}_points.txt"
        points_file.write_text("Total: 5/10\n")

        # Create a referenced artifacts zip but then delete it to simulate missing file
        artifacts_zip = submission_dir / "artifacts.zip"
        with zipfile.ZipFile(artifacts_zip, "w") as zf:
            zf.writestr("dummy", "")
        artifacts_zip.unlink()  # Now missing

        collector = ResultCollector(workspace_root)
        result = collector.collect(submission_dir_name=submission_dir_name)

        # Manually set artifacts_zip_path to missing file
        result.grading_result.artifacts_zip_path = artifacts_zip

        issues = collector.validate_result(result.grading_result)
        assert any("not found" in issue.lower() for issue in issues)
