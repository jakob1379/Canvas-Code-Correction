"""Tests for checked-in repo examples."""

import json
from pathlib import Path

import yaml


def test_count_submitted_files_example_exists() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    example_root = repo_root / "examples" / "count-submitted-files"

    assert (example_root / "README.md").is_file()
    assert (example_root / "assets" / "grader.py").is_file()
    assert (example_root / "assets" / "main.sh").is_file()
    assert (example_root / "local-workspace" / "submission" / "README.md").is_file()
    assert (example_root / "local-workspace" / "submission" / "main.py").is_file()


def test_work_package_schema_exists_and_has_expected_keys() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / "schemas" / "work-package.schema.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["title"] == "CCC Work Package"
    assert schema["properties"]["schema_version"]["const"] == 1
    assert "assignment_ids" in schema["properties"]
    assert "docker" in schema["properties"]
    assert "assets" in schema["properties"]


def test_count_submitted_files_example_manifest_uses_schema_metadata() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = repo_root / "examples" / "count-submitted-files" / "work-package.yaml"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = yaml.safe_load(manifest_text)

    # yamlfix owns this file's formatting and prepends a `---` document marker.
    assert (
        "# yaml-language-server: $schema=../../schemas/work-package.schema.json"
        in manifest_text.splitlines()[:2]
    )
    assert manifest["name"] == "count-submitted-files"
    assert manifest["version"] == "1.0.0"
    assert manifest["assets"]["source_directory"] == "assets"
