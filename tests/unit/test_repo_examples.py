"""Tests for checked-in repo examples."""

from pathlib import Path


def test_count_submitted_files_example_exists() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    example_root = repo_root / "examples" / "count-submitted-files"

    assert (example_root / "README.md").is_file()
    assert (example_root / "assets" / "grader.py").is_file()
    assert (example_root / "assets" / "main.sh").is_file()
    assert (example_root / "local-workspace" / "submission" / "README.md").is_file()
    assert (example_root / "local-workspace" / "submission" / "main.py").is_file()
